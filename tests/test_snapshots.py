from dataclasses import replace
from datetime import date, timedelta
from pathlib import Path

import pytest

from skill_ranker.dates import boundary_datetime
from skill_ranker.fixtures import load_demo_fixture
from skill_ranker.snapshots import (
    collect_snapshot,
    snapshot_for_boundary,
    write_activity,
    write_snapshot,
)

FIXTURE = Path(__file__).parent / "fixtures" / "demo.json"


class FakeClient:
    def __init__(self, values: dict[str, dict[str, object]]) -> None:
        self.values = values
        self.calls: list[str] = []

    def repository(self, repository: str) -> dict[str, object]:
        self.calls.append(repository)
        value = self.values[repository]
        if "error" in value:
            raise ValueError(str(value["error"]))
        return value


def test_collection_deduplicates_repository_requests() -> None:
    candidates, _, _ = load_demo_fixture(FIXTURE)
    duplicate = candidates[0].__class__(
        **{**candidates[0].to_dict(), "key": "900001:other/SKILL.md", "path": "other/SKILL.md"}
    )
    client = FakeClient(
        {
            candidates[0].repository: {
                "id": 900001,
                "node_id": "FIXTURE_1",
                "full_name": candidates[0].repository,
                "default_branch": "main",
                "stargazers_count": 10,
                "forks_count": 2,
                "archived": False,
                "visibility": "public",
            }
        }
    )
    snapshot = collect_snapshot(
        client,  # type: ignore[arg-type]
        (candidates[0], duplicate),
        scheduled_date=date(2026, 7, 27),
        observed_at="2026-07-26T16:17:00Z",
    )
    assert snapshot.complete
    assert client.calls == [candidates[0].repository]


def test_incomplete_snapshot_never_replaces_prior_file(tmp_path: Path) -> None:
    _, snapshot, _ = load_demo_fixture(FIXTURE)
    target = tmp_path / "snapshot.json"
    target.write_text('{"prior": true}\n', encoding="utf-8")
    incomplete = snapshot.__class__(
        **{**snapshot.to_dict(), "complete": False, "errors": ("failed",)}
    )
    with pytest.raises(ValueError, match="incomplete"):
        write_snapshot(target, incomplete)
    assert target.read_text(encoding="utf-8") == '{"prior": true}\n'


def test_boundary_selects_nearest_valid_observation() -> None:
    _, snapshot, _ = load_demo_fixture(FIXTURE)
    boundary = date(2026, 7, 27)
    near = snapshot.__class__(
        **{
            **snapshot.to_dict(),
            "observed_at": boundary_datetime(boundary).isoformat(),
            "repositories": snapshot.repositories,
            "errors": (),
        }
    )
    assert snapshot_for_boundary((snapshot, near), boundary, timedelta(hours=6)) == near


def test_completed_week_activity_is_immutable(tmp_path: Path) -> None:
    _, _, activities = load_demo_fixture(FIXTURE)
    target = tmp_path / "activity.json"
    write_activity(target, activities)
    original = target.read_bytes()
    write_activity(target, activities)
    assert target.read_bytes() == original

    changed = (replace(activities[0], commit_shas=("different",)), *activities[1:])
    with pytest.raises(FileExistsError, match="Immutable activity"):
        write_activity(target, changed)
    assert target.read_bytes() == original
