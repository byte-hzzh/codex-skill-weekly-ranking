from __future__ import annotations

from collections.abc import Iterable
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from .dates import SHANGHAI, boundary_datetime, iso_utc
from .github import GitHubClient, GitHubError
from .io import atomic_write_json, read_json
from .models import SCHEMA_VERSION, Candidate, PathActivity, RepositorySnapshot, Snapshot


def collect_snapshot(
    client: GitHubClient,
    candidates: Iterable[Candidate],
    *,
    scheduled_date: date | None = None,
    observed_at: str | None = None,
) -> Snapshot:
    scheduled = scheduled_date or datetime.now(tz=SHANGHAI).date()
    observed = observed_at or iso_utc()
    repositories = {
        candidate.repository_id: candidate for candidate in candidates if candidate.eligible
    }
    values: list[RepositorySnapshot] = []
    errors: list[str] = []
    for candidate in sorted(repositories.values(), key=lambda item: item.repository.casefold()):
        try:
            value = client.repository(candidate.repository)
            if bool(value.get("private")) or bool(value.get("archived")):
                raise GitHubError("repository is no longer an eligible public repository")
            values.append(_repository_snapshot(value, client))
        except (GitHubError, KeyError, TypeError, ValueError) as error:
            errors.append(f"{candidate.repository}: {error}")
    return Snapshot(
        schema_version=SCHEMA_VERSION,
        scheduled_date=scheduled.isoformat(),
        timezone="Asia/Shanghai",
        observed_at=observed,
        complete=not errors and len(values) == len(repositories),
        repositories=tuple(values),
        errors=tuple(errors),
    )


def write_snapshot(path: Path, snapshot: Snapshot) -> None:
    if not snapshot.complete:
        raise ValueError("Refusing to write an incomplete snapshot")
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        import json

        if json.loads(existing) != snapshot.to_dict():
            raise FileExistsError(f"Immutable snapshot already exists: {path}")
        return
    atomic_write_json(path, snapshot.to_dict())


def collect_week_activity(
    client: GitHubClient,
    candidates: Iterable[Candidate],
    start: date,
    end_exclusive: date,
) -> tuple[PathActivity, ...]:
    since = boundary_datetime(start).isoformat()
    until = boundary_datetime(end_exclusive).isoformat()
    branch_shas: dict[int, str] = {}
    results: list[PathActivity] = []
    for candidate in sorted(candidates, key=lambda item: item.key):
        if not candidate.eligible:
            continue
        try:
            if candidate.repository_id not in branch_shas:
                branch_data = client.branch(candidate.repository, candidate.default_branch)
                commit = branch_data.get("commit")
                if not isinstance(commit, dict) or not isinstance(commit.get("sha"), str):
                    raise GitHubError("branch response is missing commit SHA")
                branch_shas[candidate.repository_id] = commit["sha"]
            commits = tuple(
                dict.fromkeys(
                    str(item["sha"])
                    for item in client.commits(candidate.repository, candidate.path, since, until)
                    if isinstance(item.get("sha"), str)
                )
            )
            results.append(
                PathActivity(
                    candidate_key=candidate.key,
                    repository_id=candidate.repository_id,
                    path=candidate.path,
                    interval_start=since,
                    interval_end=until,
                    default_branch_sha=branch_shas[candidate.repository_id],
                    commit_shas=commits,
                    complete=True,
                )
            )
        except (GitHubError, KeyError, ValueError):
            results.append(
                PathActivity(
                    candidate_key=candidate.key,
                    repository_id=candidate.repository_id,
                    path=candidate.path,
                    interval_start=since,
                    interval_end=until,
                    default_branch_sha=branch_shas.get(candidate.repository_id, ""),
                    commit_shas=(),
                    complete=False,
                )
            )
    return tuple(results)


def write_activity(path: Path, activity: Iterable[PathActivity]) -> None:
    values = tuple(activity)
    if not values or not all(item.complete for item in values):
        raise ValueError("Refusing to write incomplete activity")
    activities = [item.to_dict() for item in values]
    if path.exists():
        existing = read_json(path)
        if isinstance(existing, dict) and existing.get("activities") == activities:
            return
        raise FileExistsError(f"Immutable activity already exists: {path}")
    atomic_write_json(
        path,
        {
            "schema_version": SCHEMA_VERSION,
            "generated_at": iso_utc(),
            "activities": activities,
        },
    )


def snapshot_for_boundary(
    snapshots: Iterable[Snapshot],
    intended: date,
    tolerance: timedelta,
) -> Snapshot | None:
    intended_at = boundary_datetime(intended)
    eligible: list[tuple[float, Snapshot]] = []
    for snapshot in snapshots:
        if not snapshot.complete:
            continue
        observed = datetime.fromisoformat(snapshot.observed_at.replace("Z", "+00:00")).astimezone(
            SHANGHAI
        )
        distance = abs((observed - intended_at).total_seconds())
        if distance <= tolerance.total_seconds():
            eligible.append((distance, snapshot))
    return min(eligible, key=lambda item: item[0])[1] if eligible else None


def _repository_snapshot(value: dict[str, Any], client: GitHubClient) -> RepositorySnapshot:
    return RepositorySnapshot(
        repository_id=int(value["id"]),
        repository_node_id=str(value.get("node_id", "")),
        repository=str(value["full_name"]),
        default_branch=str(value.get("default_branch", "main")),
        default_branch_sha="",
        stars=int(value["stargazers_count"]),
        forks=int(value["forks_count"]),
        archived=bool(value.get("archived", False)),
        visibility=str(value.get("visibility", "public")),
        request_status="fresh",
    )
