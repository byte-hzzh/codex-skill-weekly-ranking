from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Iterable
from datetime import datetime
from typing import Any

from .dates import WeekRange, boundary_datetime, iso_utc
from .models import (
    ALGORITHM_VERSION,
    SCHEMA_VERSION,
    TRIAL_ALGORITHM_VERSION,
    Candidate,
    PathActivity,
    Ranking,
    RankingEntry,
    RankingStatus,
    RepositorySnapshot,
    Snapshot,
    Week,
)

LIMITATIONS = (
    "Stars and forks are repository aggregate snapshots, not Skill installs.",
    "Path commit counts measure default-branch history touching the Skill path, not effort.",
    "GitHub does not provide this project with exact public stargazer event times.",
)


def percentile_ranks(values: dict[str, float]) -> dict[str, float]:
    if not values:
        return {}
    if len(values) == 1:
        return {next(iter(values)): 1.0}
    result: dict[str, float] = {}
    all_values = list(values.values())
    denominator = len(all_values) - 1
    for key, value in values.items():
        lower = sum(other < value for other in all_values)
        equal = sum(other == value for other in all_values)
        average_zero_based_rank = lower + (equal - 1) / 2
        result[key] = average_zero_based_rank / denominator
    return result


def allocate_repository_delta(delta: int, commit_counts: dict[str, int]) -> dict[str, float]:
    if not commit_counts:
        return {}
    weights = {key: 1 + max(value, 0) for key, value in commit_counts.items()}
    total = sum(weights.values())
    return {key: delta * weight / total for key, weight in weights.items()}


def score_official(
    candidates: Iterable[Candidate],
    start_snapshot: Snapshot,
    end_snapshot: Snapshot,
    activities: Iterable[PathActivity],
    week: WeekRange,
    *,
    top_n: int = 10,
    max_per_repository: int = 2,
    generated_at: str | None = None,
) -> Ranking:
    candidate_values = tuple(item for item in candidates if item.eligible)
    activity_values = tuple(activities)
    activity_by_key = {item.candidate_key: item for item in activity_values}
    if len(activity_by_key) != len(activity_values):
        raise ValueError("Official ranking activity contains duplicate candidate keys")
    _validate_official_inputs(
        candidate_values,
        start_snapshot,
        end_snapshot,
        activity_by_key,
        week,
    )
    missing = [
        item.key
        for item in candidate_values
        if item.key not in activity_by_key or not activity_by_key[item.key].complete
    ]
    if missing:
        raise ValueError(f"Official ranking requires complete path activity: {', '.join(missing)}")
    start_repositories = {item.repository_id: item for item in start_snapshot.repositories}
    end_repositories = {item.repository_id: item for item in end_snapshot.repositories}
    required_ids = {item.repository_id for item in candidate_values}
    if not required_ids <= start_repositories.keys() or not required_ids <= end_repositories.keys():
        raise ValueError(
            "Official ranking boundary snapshots do not cover every candidate repository"
        )

    by_repository: dict[int, list[Candidate]] = defaultdict(list)
    for candidate in candidate_values:
        by_repository[candidate.repository_id].append(candidate)

    raw_rows: list[dict[str, Any]] = []
    for repository_id, repository_candidates in by_repository.items():
        start_repo = start_repositories[repository_id]
        end_repo = end_repositories[repository_id]
        raw_star_delta = end_repo.stars - start_repo.stars
        raw_fork_delta = end_repo.forks - start_repo.forks
        commits = {item.key: activity_by_key[item.key].commits for item in repository_candidates}
        allocated_stars = allocate_repository_delta(max(raw_star_delta, 0), commits)
        allocated_forks = allocate_repository_delta(max(raw_fork_delta, 0), commits)
        for candidate in repository_candidates:
            raw_rows.append(
                {
                    "candidate": candidate,
                    "repository_end": end_repo,
                    "raw_star_delta": raw_star_delta,
                    "raw_fork_delta": raw_fork_delta,
                    "allocated_star_delta": allocated_stars[candidate.key],
                    "allocated_fork_delta": allocated_forks[candidate.key],
                    "path_commits": commits[candidate.key],
                }
            )

    star_percentiles = percentile_ranks(
        {row["candidate"].key: math.log1p(row["allocated_star_delta"]) for row in raw_rows}
    )
    fork_percentiles = percentile_ranks(
        {row["candidate"].key: math.log1p(row["allocated_fork_delta"]) for row in raw_rows}
    )
    commit_percentiles = percentile_ranks(
        {row["candidate"].key: math.log1p(row["path_commits"]) for row in raw_rows}
    )
    for row in raw_rows:
        key = row["candidate"].key
        row["components"] = {
            "star_percentile": star_percentiles[key],
            "fork_percentile": fork_percentiles[key],
            "commit_percentile": commit_percentiles[key],
        }
        row["score"] = 100 * (
            0.65 * star_percentiles[key]
            + 0.15 * fork_percentiles[key]
            + 0.20 * commit_percentiles[key]
        )
    selected = _select(raw_rows, top_n, max_per_repository)
    return _ranking(
        selected,
        week,
        "official",
        ALGORITHM_VERSION,
        generated_at or iso_utc(),
        (start_snapshot.observed_at, end_snapshot.observed_at),
        demo=False,
    )


def score_trial(
    candidates: Iterable[Candidate],
    snapshot: Snapshot,
    activities: Iterable[PathActivity],
    week: WeekRange,
    *,
    top_n: int = 10,
    max_per_repository: int = 2,
    generated_at: str | None = None,
    demo: bool = False,
) -> Ranking:
    repositories = {item.repository_id: item for item in snapshot.repositories}
    activity_by_key = {item.candidate_key: item for item in activities if item.complete}
    rows: list[dict[str, Any]] = []
    for candidate in candidates:
        if not candidate.eligible or candidate.repository_id not in repositories:
            continue
        repository = repositories[candidate.repository_id]
        rows.append(
            {
                "candidate": candidate,
                "repository_end": repository,
                "total_stars": repository.stars,
                "total_forks": repository.forks,
                "path_commits": (
                    activity_by_key[candidate.key].commits
                    if candidate.key in activity_by_key
                    else 0
                ),
            }
        )
    star_percentiles = percentile_ranks(
        {row["candidate"].key: math.log1p(row["total_stars"]) for row in rows}
    )
    fork_percentiles = percentile_ranks(
        {row["candidate"].key: math.log1p(row["total_forks"]) for row in rows}
    )
    commit_percentiles = percentile_ranks(
        {row["candidate"].key: math.log1p(row["path_commits"]) for row in rows}
    )
    for row in rows:
        key = row["candidate"].key
        row["components"] = {
            "total_star_percentile": star_percentiles[key],
            "total_fork_percentile": fork_percentiles[key],
            "recent_path_commit_percentile": commit_percentiles[key],
        }
        row["score"] = 100 * (
            0.50 * star_percentiles[key]
            + 0.15 * fork_percentiles[key]
            + 0.35 * commit_percentiles[key]
        )
    selected = _select(rows, top_n, max_per_repository, trial=True)
    limitations = (
        *LIMITATIONS,
        "This trial ranking uses current cumulative repository totals because "
        "a full week is unavailable.",
    )
    return _ranking(
        selected,
        week,
        "trial",
        TRIAL_ALGORITHM_VERSION,
        generated_at or iso_utc(),
        (snapshot.observed_at,),
        demo=demo,
        limitations=limitations,
    )


def _select(
    rows: list[dict[str, Any]], top_n: int, max_per_repository: int, *, trial: bool = False
) -> list[dict[str, Any]]:
    star_key = "total_stars" if trial else "allocated_star_delta"
    ordered = sorted(
        rows,
        key=lambda row: (
            -row["score"],
            -row[star_key],
            -row["path_commits"],
            row["candidate"].repository.casefold(),
            row["candidate"].path.casefold(),
        ),
    )
    selected: list[dict[str, Any]] = []
    repository_counts: dict[int, int] = defaultdict(int)
    for row in ordered:
        repository_id = row["candidate"].repository_id
        if repository_counts[repository_id] >= max_per_repository:
            continue
        selected.append(row)
        repository_counts[repository_id] += 1
        if len(selected) == top_n:
            break
    return selected


def _ranking(
    rows: list[dict[str, Any]],
    week: WeekRange,
    status: RankingStatus,
    algorithm_version: str,
    generated_at: str,
    source_observed_at: tuple[str, ...],
    *,
    demo: bool,
    limitations: tuple[str, ...] = LIMITATIONS,
) -> Ranking:
    entries: list[RankingEntry] = []
    for index, row in enumerate(rows, start=1):
        candidate: Candidate = row["candidate"]
        repository: RepositorySnapshot = row["repository_end"]
        excluded = {"candidate", "repository_end", "components", "score"}
        metrics = {
            key: round(value, 4) if isinstance(value, float) else value
            for key, value in row.items()
            if key not in excluded and isinstance(value, int | float)
        }
        metrics["repository_stars"] = repository.stars
        metrics["repository_forks"] = repository.forks
        entries.append(
            RankingEntry(
                rank=index,
                candidate_key=candidate.key,
                name=candidate.name,
                description=candidate.description,
                repository=candidate.repository,
                path=candidate.path,
                source_url=candidate.source_url,
                repository_url=candidate.repository_url,
                score=round(row["score"], 2),
                metrics=metrics,
                components={key: round(value, 6) for key, value in row["components"].items()},
            )
        )
    return Ranking(
        schema_version=SCHEMA_VERSION,
        algorithm_version=algorithm_version,
        ranking_status=status,
        week=Week(week.start.isoformat(), week.end.isoformat(), "Asia/Shanghai"),
        generated_at=generated_at,
        source_observed_at=source_observed_at,
        complete=len(entries) > 0,
        demo=demo,
        entries=tuple(entries),
        limitations=limitations,
    )


def _validate_official_inputs(
    candidates: tuple[Candidate, ...],
    start_snapshot: Snapshot,
    end_snapshot: Snapshot,
    activity_by_key: dict[str, PathActivity],
    week: WeekRange,
) -> None:
    if not start_snapshot.complete or not end_snapshot.complete:
        raise ValueError("Official ranking requires complete boundary snapshots")
    if start_snapshot.timezone != "Asia/Shanghai" or end_snapshot.timezone != "Asia/Shanghai":
        raise ValueError("Official ranking boundary snapshots must use Asia/Shanghai")
    if start_snapshot.scheduled_date != week.start.isoformat():
        raise ValueError("Official ranking start snapshot does not match the requested week")
    if end_snapshot.scheduled_date != week.next_boundary.isoformat():
        raise ValueError("Official ranking end snapshot does not match the requested week")

    expected_start = boundary_datetime(week.start)
    expected_end = boundary_datetime(week.next_boundary)
    for candidate in candidates:
        activity = activity_by_key.get(candidate.key)
        if activity is None:
            continue
        if activity.repository_id != candidate.repository_id or activity.path != candidate.path:
            raise ValueError(f"Path activity identity mismatch for {candidate.key}")
        if not _same_instant(activity.interval_start, expected_start) or not _same_instant(
            activity.interval_end, expected_end
        ):
            raise ValueError(f"Path activity interval mismatch for {candidate.key}")
        if activity.complete and not activity.default_branch_sha:
            raise ValueError(f"Path activity is missing branch provenance for {candidate.key}")
        if len(set(activity.commit_shas)) != len(activity.commit_shas):
            raise ValueError(f"Path activity contains duplicate commits for {candidate.key}")


def _same_instant(value: str, expected: datetime) -> bool:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed == expected
