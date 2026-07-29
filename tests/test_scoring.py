from dataclasses import replace
from datetime import date
from pathlib import Path

import pytest

from skill_ranker.dates import WeekRange
from skill_ranker.fixtures import load_demo_fixture
from skill_ranker.models import PathActivity
from skill_ranker.scoring import (
    allocate_repository_delta,
    percentile_ranks,
    score_official,
    score_trial,
)

FIXTURE = Path(__file__).parent / "fixtures" / "demo.json"


def official_activities(
    activities: tuple[PathActivity, ...],
) -> tuple[PathActivity, ...]:
    return tuple(
        replace(
            activity,
            interval_start="2026-07-27T00:00:00+08:00",
            interval_end="2026-08-03T00:00:00+08:00",
        )
        for activity in activities
    )


def test_allocation_conserves_repository_delta() -> None:
    allocated = allocate_repository_delta(17, {"a": 0, "b": 2, "c": 8})
    assert sum(allocated.values()) == pytest.approx(17)
    assert allocated["c"] > allocated["b"] > allocated["a"]


def test_percentiles_are_deterministic_for_ties() -> None:
    values = percentile_ranks({"b": 5, "a": 5, "c": 10})
    assert values == {"b": 0.25, "a": 0.25, "c": 1.0}


def test_demo_trial_top_ten_is_deterministic_and_labeled() -> None:
    candidates, snapshot, activities = load_demo_fixture(FIXTURE)
    week = WeekRange(date(2026, 7, 27), date(2026, 8, 2))
    ranking = score_trial(
        candidates,
        snapshot,
        activities,
        week,
        generated_at=snapshot.observed_at,
        demo=True,
    )
    assert ranking.ranking_status == "trial"
    assert ranking.demo is True
    assert len(ranking.entries) == 10
    assert [entry.rank for entry in ranking.entries] == list(range(1, 11))
    assert ranking.entries[0].name == "Code Review"


def test_official_negative_deltas_are_preserved_but_floored_for_score() -> None:
    candidates, end_snapshot, activities = load_demo_fixture(FIXTURE)
    candidates = candidates[:2]
    activities = official_activities(activities[:2])
    start_repositories = tuple(
        replace(repository, stars=repository.stars + 10, forks=repository.forks + 2)
        for repository in end_snapshot.repositories[:2]
    )
    start = replace(
        end_snapshot,
        scheduled_date="2026-07-27",
        observed_at="2026-07-26T16:17:00Z",
        repositories=start_repositories,
    )
    end = replace(
        end_snapshot,
        scheduled_date="2026-08-03",
        observed_at="2026-08-02T16:17:00Z",
        repositories=end_snapshot.repositories[:2],
    )
    ranking = score_official(
        candidates,
        start,
        end,
        activities,
        WeekRange(date(2026, 7, 27), date(2026, 8, 2)),
    )
    assert ranking.ranking_status == "official"
    assert ranking.entries[0].metrics["raw_star_delta"] == -10
    assert ranking.entries[0].metrics["allocated_star_delta"] == 0


def test_official_requires_complete_activity() -> None:
    candidates, snapshot, activities = load_demo_fixture(FIXTURE)
    snapshot = replace(snapshot, scheduled_date="2026-07-27")
    end = replace(snapshot, scheduled_date="2026-08-03")
    incomplete = replace(official_activities(activities[:1])[0], complete=False)
    with pytest.raises(ValueError, match="complete path activity"):
        score_official(
            candidates[:1],
            snapshot,
            end,
            (incomplete,),
            WeekRange(date(2026, 7, 27), date(2026, 8, 2)),
        )


def test_official_rejects_activity_from_a_different_week() -> None:
    candidates, snapshot, activities = load_demo_fixture(FIXTURE)
    start = replace(snapshot, scheduled_date="2026-07-27")
    end = replace(snapshot, scheduled_date="2026-08-03")
    with pytest.raises(ValueError, match="interval mismatch"):
        score_official(
            candidates[:1],
            start,
            end,
            activities[:1],
            WeekRange(date(2026, 7, 27), date(2026, 8, 2)),
        )


def test_repository_diversity_cap() -> None:
    candidates, snapshot, activities = load_demo_fixture(FIXTURE)
    first = candidates[0]
    extras = tuple(
        replace(
            first,
            key=f"{first.repository_id}:skills/extra-{index}/SKILL.md",
            path=f"skills/extra-{index}/SKILL.md",
            name=f"Extra {index}",
        )
        for index in range(4)
    )
    extra_activities = tuple(
        PathActivity(
            candidate_key=item.key,
            repository_id=item.repository_id,
            path=item.path,
            interval_start="",
            interval_end="",
            default_branch_sha="",
            commit_shas=tuple(f"x-{index}" for index in range(20)),
            complete=True,
        )
        for item in extras
    )
    ranking = score_trial(
        extras + candidates,
        snapshot,
        extra_activities + activities,
        WeekRange(date(2026, 7, 27), date(2026, 8, 2)),
    )
    repository_entries = [
        entry for entry in ranking.entries if entry.repository == first.repository
    ]
    assert len(repository_entries) == 2
