from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

SHANGHAI = ZoneInfo("Asia/Shanghai")
UTC = ZoneInfo("UTC")


@dataclass(frozen=True)
class WeekRange:
    start: date
    end: date

    @property
    def next_boundary(self) -> date:
        return self.end + timedelta(days=1)

    @property
    def key(self) -> str:
        return self.start.isoformat()

    @property
    def label(self) -> str:
        return f"{self.start.isoformat()} — {self.end.isoformat()}"


def shanghai_now() -> datetime:
    return datetime.now(tz=SHANGHAI)


def week_containing(value: date | datetime) -> WeekRange:
    local_date = value.astimezone(SHANGHAI).date() if isinstance(value, datetime) else value
    start = local_date - timedelta(days=local_date.weekday())
    return WeekRange(start=start, end=start + timedelta(days=6))


def previous_completed_week(value: date | datetime) -> WeekRange:
    current = week_containing(value)
    end = current.start - timedelta(days=1)
    return WeekRange(start=end - timedelta(days=6), end=end)


def boundary_datetime(value: date) -> datetime:
    return datetime.combine(value, time.min, tzinfo=SHANGHAI)


def within_boundary_tolerance(
    observed_at: str, intended_date: date, tolerance: timedelta = timedelta(hours=6)
) -> bool:
    observed = datetime.fromisoformat(observed_at.replace("Z", "+00:00")).astimezone(SHANGHAI)
    return abs(observed - boundary_datetime(intended_date)) <= tolerance


def iso_utc(value: datetime | None = None) -> str:
    current = value or datetime.now(tz=UTC)
    return current.astimezone(UTC).isoformat().replace("+00:00", "Z")
