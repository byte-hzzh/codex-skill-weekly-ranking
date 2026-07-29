from __future__ import annotations

from pathlib import Path
from typing import Any

from .io import read_json
from .models import Candidate, PathActivity, RepositorySnapshot, Snapshot


def load_demo_fixture(
    path: Path,
) -> tuple[tuple[Candidate, ...], Snapshot, tuple[PathActivity, ...]]:
    value = read_json(path)
    if not isinstance(value, dict):
        raise ValueError("demo fixture must be an object")
    repositories = {int(item["repository_id"]): item for item in value["repositories"]}
    candidates = tuple(
        _candidate(item, repositories[int(item["repository_id"])], str(value["observed_at"]))
        for item in value["skills"]
    )
    snapshot = Snapshot(
        schema_version="1.0",
        scheduled_date=str(value["scheduled_date"]),
        timezone="Asia/Shanghai",
        observed_at=str(value["observed_at"]),
        complete=True,
        repositories=tuple(RepositorySnapshot.from_dict(item) for item in value["repositories"]),
    )
    activities = tuple(_activity(item, str(value["observed_at"])) for item in value["skills"])
    return candidates, snapshot, activities


def _candidate(value: dict[str, Any], repository: dict[str, Any], checked_at: str) -> Candidate:
    repository_id = int(value["repository_id"])
    full_name = str(repository["repository"])
    path = str(value["path"])
    repository_url = f"https://github.com/{full_name}"
    return Candidate(
        key=f"{repository_id}:{path}",
        repository_id=repository_id,
        repository_node_id=str(repository.get("repository_node_id", "")),
        repository=full_name,
        default_branch=str(repository.get("default_branch", "main")),
        path=path,
        name=str(value["name"]),
        description=str(value["description"]),
        source_url=f"{repository_url}/blob/main/{path}",
        repository_url=repository_url,
        discovered_via="fixture",
        checked_at=checked_at,
    )


def _activity(value: dict[str, Any], observed_at: str) -> PathActivity:
    repository_id = int(value["repository_id"])
    path = str(value["path"])
    commits = int(value["commits"])
    return PathActivity(
        candidate_key=f"{repository_id}:{path}",
        repository_id=repository_id,
        path=path,
        interval_start="2026-07-20T00:00:00+08:00",
        interval_end="2026-07-27T00:00:00+08:00",
        default_branch_sha="fixture-not-a-github-sha",
        commit_shas=tuple(f"fixture-{repository_id}-{index}" for index in range(commits)),
        complete=True,
        method="fixture",
    )
