import json
from datetime import date, datetime
from pathlib import Path
from unittest.mock import Mock, call

import pytest

from skill_ranker import cli
from skill_ranker.dates import SHANGHAI


def _set_today(monkeypatch: pytest.MonkeyPatch, today: date) -> None:
    current = datetime.combine(today, datetime.min.time(), tzinfo=SHANGHAI)
    clock = Mock()
    clock.now.return_value = current
    monkeypatch.setattr(cli, "datetime", clock)


def _write_live_ranking_marker(root: Path) -> None:
    path = root / "data" / "rankings" / "2026-07-27.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"demo": False}), encoding="utf-8")


def test_run_daily_publishes_current_week_trial_after_first_collection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _set_today(monkeypatch, date(2026, 7, 30))
    monkeypatch.delenv("DISCOVERY_GITHUB_TOKEN", raising=False)
    events = Mock()
    monkeypatch.setattr(cli, "_discover", lambda *args, **kwargs: events.discover(*args, **kwargs))
    monkeypatch.setattr(cli, "_collect", lambda *args, **kwargs: events.collect(*args, **kwargs))
    monkeypatch.setattr(cli, "_activity", lambda *args, **kwargs: events.activity(*args, **kwargs))
    monkeypatch.setattr(cli, "_rank", lambda *args, **kwargs: events.rank(*args, **kwargs))

    cli._run_daily(tmp_path)

    assert events.mock_calls == [
        call.discover(tmp_path, include_search=False),
        call.collect(tmp_path, date(2026, 7, 30)),
        call.rank(tmp_path, date(2026, 7, 27), trial=True),
    ]


def test_run_daily_keeps_monday_official_path_when_boundaries_exist(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _set_today(monkeypatch, date(2026, 8, 3))
    monkeypatch.delenv("DISCOVERY_GITHUB_TOKEN", raising=False)
    snapshots = tmp_path / "data" / "snapshots"
    snapshots.mkdir(parents=True)
    (snapshots / "2026-07-27.json").touch()
    (snapshots / "2026-08-03.json").touch()
    events = Mock()
    monkeypatch.setattr(cli, "_discover", lambda *args, **kwargs: events.discover(*args, **kwargs))
    monkeypatch.setattr(cli, "_collect", lambda *args, **kwargs: events.collect(*args, **kwargs))
    monkeypatch.setattr(cli, "_activity", lambda *args, **kwargs: events.activity(*args, **kwargs))
    monkeypatch.setattr(cli, "_rank", lambda *args, **kwargs: events.rank(*args, **kwargs))

    cli._run_daily(tmp_path)

    assert events.mock_calls == [
        call.discover(tmp_path, include_search=False),
        call.collect(tmp_path, date(2026, 8, 3)),
        call.activity(tmp_path, date(2026, 7, 27)),
        call.rank(tmp_path, date(2026, 7, 27), trial=False),
    ]


def test_run_daily_marks_existing_publication_stale_when_monday_boundary_is_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _set_today(monkeypatch, date(2026, 8, 3))
    monkeypatch.delenv("DISCOVERY_GITHUB_TOKEN", raising=False)
    _write_live_ranking_marker(tmp_path)
    events = Mock()
    monkeypatch.setattr(cli, "_discover", lambda *args, **kwargs: events.discover(*args, **kwargs))
    monkeypatch.setattr(cli, "_collect", lambda *args, **kwargs: events.collect(*args, **kwargs))
    monkeypatch.setattr(cli, "mark_publication_stale", lambda *args: events.mark_stale(*args))

    cli._run_daily(tmp_path)

    assert events.mock_calls == [
        call.discover(tmp_path, include_search=False),
        call.collect(tmp_path, date(2026, 8, 3)),
        call.mark_stale(tmp_path, "2026-07-27"),
    ]


def test_run_daily_does_not_replace_latest_live_ranking_midweek(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _set_today(monkeypatch, date(2026, 8, 4))
    catalog = tmp_path / "data" / "candidates.json"
    catalog.parent.mkdir(parents=True)
    catalog.touch()
    _write_live_ranking_marker(tmp_path)
    collect = Mock()
    rank = Mock()
    monkeypatch.setattr(cli, "_collect", collect)
    monkeypatch.setattr(cli, "_rank", rank)

    cli._run_daily(tmp_path)

    collect.assert_called_once_with(tmp_path, date(2026, 8, 4))
    rank.assert_not_called()


def test_run_daily_marks_attempted_week_stale_when_collection_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _set_today(monkeypatch, date(2026, 7, 30))
    catalog = tmp_path / "data" / "candidates.json"
    catalog.parent.mkdir(parents=True)
    catalog.touch()
    failure = RuntimeError("network unavailable")
    collect = Mock(side_effect=failure)
    rank = Mock()
    mark_stale = Mock()
    monkeypatch.setattr(cli, "_collect", collect)
    monkeypatch.setattr(cli, "_rank", rank)
    monkeypatch.setattr(cli, "mark_publication_stale", mark_stale)

    with pytest.raises(RuntimeError, match="network unavailable"):
        cli._run_daily(tmp_path)

    collect.assert_called_once_with(tmp_path, date(2026, 7, 30))
    rank.assert_not_called()
    mark_stale.assert_called_once_with(tmp_path, "2026-07-27")
