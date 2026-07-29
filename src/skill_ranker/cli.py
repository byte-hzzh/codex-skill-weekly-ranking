from __future__ import annotations

import argparse
import os
import sys
from contextlib import suppress
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from .config import load_policy
from .dates import (
    SHANGHAI,
    WeekRange,
    previous_completed_week,
    week_containing,
    within_boundary_tolerance,
)
from .discovery import discover, preserve_cached_candidates, write_catalog
from .fixtures import load_demo_fixture
from .github import GitHubClient
from .io import read_json
from .models import Candidate, PathActivity, Snapshot
from .publishing import latest_ranking_path, load_ranking, mark_publication_stale, publish
from .scoring import score_official, score_trial
from .snapshots import (
    collect_snapshot,
    collect_week_activity,
    write_activity,
    write_snapshot,
)
from .validation import validate_document


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    commands = parser.add_subparsers(dest="command", required=True)

    discovery = commands.add_parser("discover", help="refresh the candidate catalog")
    discovery.add_argument(
        "--search", action="store_true", help="include authenticated code search"
    )

    collection = commands.add_parser("collect", help="collect a complete daily snapshot")
    collection.add_argument("--date", type=date.fromisoformat)

    activity = commands.add_parser("activity", help="collect path commit activity for a week")
    activity.add_argument("--week-start", required=True, type=date.fromisoformat)

    ranking = commands.add_parser("rank", help="build a trial or official ranking")
    ranking.add_argument("--week-start", required=True, type=date.fromisoformat)
    ranking.add_argument("--trial", action="store_true")

    publishing = commands.add_parser("publish", help="render README and Pages from ranking JSON")
    publishing.add_argument("--ranking", type=Path)

    commands.add_parser("build-demo", help="render the deterministic, explicitly non-live demo")
    commands.add_parser("run-daily", help="Actions entry point: discover, collect, and finalize")
    commands.add_parser("validate", help="validate tracked JSON and publication parity")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.resolve()
    try:
        if args.command == "discover":
            _discover(root, args.search)
        elif args.command == "collect":
            _collect(root, args.date)
        elif args.command == "activity":
            _activity(root, args.week_start)
        elif args.command == "rank":
            _rank(root, args.week_start, args.trial)
        elif args.command == "publish":
            path = args.ranking or latest_ranking_path(root)
            publish(root, load_ranking(path if path.is_absolute() else root / path))
        elif args.command == "build-demo":
            _build_demo(root)
        elif args.command == "run-daily":
            _run_daily(root)
        elif args.command == "validate":
            _validate(root)
        else:
            raise AssertionError(f"Unhandled command: {args.command}")
    except (FileNotFoundError, ValueError, RuntimeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


def _client(root: Path, *, discovery: bool = False) -> GitHubClient:
    token_name = "DISCOVERY_GITHUB_TOKEN" if discovery else "GITHUB_TOKEN"
    token = os.environ.get(token_name)
    if not token and not discovery:
        token = os.environ.get("DISCOVERY_GITHUB_TOKEN")
    return GitHubClient(token, cache_dir=root / ".cache" / "github")


def _discover(root: Path, include_search: bool) -> None:
    policy = load_policy(root)
    result = discover(
        _client(root, discovery=include_search), policy, include_search=include_search
    )
    catalog = root / "data" / "candidates.json"
    if catalog.exists():
        result = preserve_cached_candidates(result, _load_candidates(root), policy)
    write_catalog(catalog, result)
    print(
        f"discovered {len(result.candidates)} candidates"
        f" ({len(result.errors)} exclusions/errors, search_degraded={result.search_degraded})"
    )


def _collect(root: Path, scheduled_date: date | None) -> Snapshot:
    candidates = _load_candidates(root)
    snapshot = collect_snapshot(_client(root), candidates, scheduled_date=scheduled_date)
    target = root / "data" / "snapshots" / f"{snapshot.scheduled_date}.json"
    validate_document(root, "snapshot.schema.json", snapshot.to_dict())
    write_snapshot(target, snapshot)
    print(f"wrote complete snapshot {target.relative_to(root)}")
    return snapshot


def _activity(root: Path, start: date) -> tuple[PathActivity, ...]:
    week = WeekRange(start, start + timedelta(days=6))
    values = collect_week_activity(
        _client(root), _load_candidates(root), week.start, week.next_boundary
    )
    target = root / "data" / "activity" / f"{week.key}.json"
    write_activity(target, values)
    print(f"wrote complete activity {target.relative_to(root)}")
    return values


def _rank(root: Path, start: date, trial: bool) -> None:
    week = WeekRange(start, start + timedelta(days=6))
    candidates = _load_candidates(root)
    policy = load_policy(root)
    if trial:
        paths = sorted((root / "data" / "snapshots").glob("*.json"))
        if not paths:
            raise FileNotFoundError("A snapshot is required for trial scoring")
        snapshot = _load_snapshot(paths[-1])
        activities = _load_activity_optional(root / "data" / "activity" / f"{week.key}.json")
        ranking = score_trial(
            candidates,
            snapshot,
            activities,
            week,
            top_n=policy.top_n,
            max_per_repository=policy.max_skills_per_repository,
        )
    else:
        start_snapshot = _load_snapshot(root / "data" / "snapshots" / f"{week.start}.json")
        end_snapshot = _load_snapshot(root / "data" / "snapshots" / f"{week.next_boundary}.json")
        tolerance = timedelta(hours=policy.boundary_tolerance_hours)
        if not within_boundary_tolerance(
            start_snapshot.observed_at, week.start, tolerance
        ) or not within_boundary_tolerance(end_snapshot.observed_at, week.next_boundary, tolerance):
            raise ValueError(
                "Official ranking requires both observations within boundary tolerance"
            )
        activities = _load_activity(root / "data" / "activity" / f"{week.key}.json")
        ranking = score_official(
            candidates,
            start_snapshot,
            end_snapshot,
            activities,
            week,
            top_n=policy.top_n,
            max_per_repository=policy.max_skills_per_repository,
        )
    publish(root, ranking)
    print(f"published {ranking.ranking_status} ranking for {week.label}")


def _build_demo(root: Path) -> None:
    candidates, snapshot, activities = load_demo_fixture(root / "tests" / "fixtures" / "demo.json")
    fixture_date = date.fromisoformat(snapshot.scheduled_date)
    week = week_containing(fixture_date)
    policy = load_policy(root)
    ranking = score_trial(
        candidates,
        snapshot,
        activities,
        week,
        top_n=policy.top_n,
        max_per_repository=policy.max_skills_per_repository,
        generated_at=snapshot.observed_at,
        demo=True,
    )
    publish(root, ranking)
    print(f"published non-live demo ranking for {week.label}")


def _run_daily(root: Path) -> None:
    today = datetime.now(tz=SHANGHAI).date()
    current_week = week_containing(today)
    attempted_week = previous_completed_week(today) if today.weekday() == 0 else current_week
    try:
        catalog = root / "data" / "candidates.json"
        force_discovery = os.environ.get("FORCE_DISCOVERY") == "1"
        if force_discovery or today.weekday() == 0 or not catalog.exists():
            _discover(root, include_search=bool(os.environ.get("DISCOVERY_GITHUB_TOKEN")))
        snapshot_path = root / "data" / "snapshots" / f"{today}.json"
        if snapshot_path.exists():
            print(f"reusing immutable snapshot {snapshot_path.relative_to(root)}")
        else:
            _collect(root, today)
        boundary_paths = (
            root / "data" / "snapshots" / f"{attempted_week.start}.json",
            root / "data" / "snapshots" / f"{attempted_week.next_boundary}.json",
        )
        has_live_ranking = _has_live_ranking(root)
        if today.weekday() == 0:
            if all(path.exists() for path in boundary_paths):
                _activity(root, attempted_week.start)
                _rank(root, attempted_week.start, trial=False)
            elif has_live_ranking:
                mark_publication_stale(root, attempted_week.start.isoformat())
            else:
                _rank(root, current_week.start, trial=True)
        elif not has_live_ranking:
            _rank(root, current_week.start, trial=True)
    except Exception:
        # A first-ever failed collection may have no prior ranking to preserve.
        with suppress(FileNotFoundError):
            mark_publication_stale(root, attempted_week.start.isoformat())
        raise


def _has_live_ranking(root: Path) -> bool:
    for path in (root / "data" / "rankings").glob("*.json"):
        value = read_json(path)
        if isinstance(value, dict) and not bool(value.get("demo")):
            return True
    return False


def _validate(root: Path) -> None:
    for path in (root / "data" / "rankings").glob("*.json"):
        validate_document(root, "ranking.schema.json", read_json(path))
    for path in (root / "data" / "snapshots").glob("*.json"):
        validate_document(root, "snapshot.schema.json", read_json(path))
    latest = latest_ranking_path(root)
    archived = load_ranking(latest)
    served_path = root / "docs" / "data" / "latest.json"
    validate_document(root, "ranking.schema.json", read_json(served_path))
    ranking = load_ranking(served_path)
    index = (root / "docs" / "index.html").read_text(encoding="utf-8")
    readme = (root / "README.md").read_text(encoding="utf-8")
    if ranking.week.start_date not in index or ranking.week.start_date not in readme:
        raise ValueError("README/site/ranking week parity failed")
    archived_keys = [entry.candidate_key for entry in archived.entries]
    served_keys = [entry.candidate_key for entry in ranking.entries]
    if served_keys != archived_keys:
        raise ValueError("served ranking differs from the latest successful archive")
    for entry in ranking.entries:
        if entry.candidate_key not in index or entry.source_url not in readme:
            raise ValueError(f"site is missing {entry.candidate_key}")
    print("JSON schemas and publication parity validated")


def _load_candidates(root: Path) -> tuple[Candidate, ...]:
    value = read_json(root / "data" / "candidates.json")
    validate_document(root, "candidates.schema.json", value)
    return tuple(Candidate.from_dict(item) for item in value["candidates"])


def _load_snapshot(path: Path) -> Snapshot:
    value = read_json(path)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return Snapshot.from_dict(value)


def _load_activity(path: Path) -> tuple[PathActivity, ...]:
    value = read_json(path)
    return tuple(_decode_activity(item) for item in value["activities"])


def _load_activity_optional(path: Path) -> tuple[PathActivity, ...]:
    return _load_activity(path) if path.exists() else ()


def _decode_activity(value: dict[str, Any]) -> PathActivity:
    return PathActivity(
        candidate_key=str(value["candidate_key"]),
        repository_id=int(value["repository_id"]),
        path=str(value["path"]),
        interval_start=str(value["interval_start"]),
        interval_end=str(value["interval_end"]),
        default_branch_sha=str(value["default_branch_sha"]),
        commit_shas=tuple(str(item) for item in value["commit_shas"]),
        complete=bool(value["complete"]),
        method=str(value.get("method", "github-rest-path")),
    )


if __name__ == "__main__":
    raise SystemExit(main())
