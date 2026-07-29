from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from skill_ranker.dates import (
    boundary_datetime,
    previous_completed_week,
    week_containing,
    within_boundary_tolerance,
)


def test_week_crosses_month_and_year_boundary() -> None:
    week = week_containing(date(2026, 1, 1))
    assert week.start == date(2025, 12, 29)
    assert week.end == date(2026, 1, 4)
    assert week.label == "2025-12-29 — 2026-01-04"


def test_datetime_is_converted_to_shanghai_before_week_calculation() -> None:
    utc = ZoneInfo("UTC")
    value = datetime(2026, 7, 26, 17, 0, tzinfo=utc)
    assert week_containing(value).start == date(2026, 7, 27)


def test_previous_completed_week() -> None:
    week = previous_completed_week(date(2026, 7, 30))
    assert week.start == date(2026, 7, 20)
    assert week.end == date(2026, 7, 26)


def test_shanghai_boundary_is_dst_independent() -> None:
    winter = boundary_datetime(date(2026, 1, 5))
    summer = boundary_datetime(date(2026, 7, 27))
    assert winter.utcoffset() == summer.utcoffset() == timedelta(hours=8)


def test_boundary_tolerance() -> None:
    assert within_boundary_tolerance("2026-07-26T16:17:00Z", date(2026, 7, 27))
    assert not within_boundary_tolerance("2026-07-27T08:00:00Z", date(2026, 7, 27))
