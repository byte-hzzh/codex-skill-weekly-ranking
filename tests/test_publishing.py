import json
import shutil
from datetime import date
from pathlib import Path

from skill_ranker.dates import WeekRange
from skill_ranker.fixtures import load_demo_fixture
from skill_ranker.publishing import mark_publication_stale, publish
from skill_ranker.scoring import score_trial

PROJECT_ROOT = Path(__file__).parents[1]


def test_readme_html_json_are_rendered_from_one_ranking(tmp_path: Path) -> None:
    shutil.copytree(PROJECT_ROOT / "templates", tmp_path / "templates")
    shutil.copytree(PROJECT_ROOT / "schemas", tmp_path / "schemas")
    shutil.copy2(PROJECT_ROOT / "METHODOLOGY.md", tmp_path / "METHODOLOGY.md")
    (tmp_path / "README.md").write_text(
        "# Test\n\n<!-- ranking:start -->\nold\n<!-- ranking:end -->\n", encoding="utf-8"
    )
    candidates, snapshot, activities = load_demo_fixture(
        PROJECT_ROOT / "tests" / "fixtures" / "demo.json"
    )
    candidates = (
        candidates[0].__class__(
            **{
                **candidates[0].to_dict(),
                "name": "Unsafe <script>",
                "description": "A [link](bad) and <b>markup</b> fixture.",
            }
        ),
        *candidates[1:],
    )
    ranking = score_trial(
        candidates,
        snapshot,
        activities,
        WeekRange(date(2026, 7, 27), date(2026, 8, 2)),
        generated_at=snapshot.observed_at,
        demo=True,
    )
    publish(tmp_path, ranking)
    readme = (tmp_path / "README.md").read_text(encoding="utf-8")
    index = (tmp_path / "docs" / "index.html").read_text(encoding="utf-8")
    history = (tmp_path / "docs" / "weeks" / "2026-07-27.html").read_text(encoding="utf-8")
    canonical = (tmp_path / "data" / "rankings" / "2026-07-27.json").read_text(encoding="utf-8")
    assert "2026-07-27 — 2026-08-02" in readme
    assert "2026-07-27 — 2026-08-02" in index
    assert "non-live fixture data" in readme
    assert "&lt;script&gt;" in index
    assert "<script>" not in index
    assert "\\[link\\]" in readme
    assert ranking.entries[0].candidate_key in canonical
    assert "../assets/styles.css" in history
    assert 'href="../data/2026-07-27.json"' in history


def test_stale_recovery_updates_served_view_without_rewriting_history(tmp_path: Path) -> None:
    shutil.copytree(PROJECT_ROOT / "templates", tmp_path / "templates")
    shutil.copytree(PROJECT_ROOT / "schemas", tmp_path / "schemas")
    shutil.copy2(PROJECT_ROOT / "METHODOLOGY.md", tmp_path / "METHODOLOGY.md")
    (tmp_path / "README.md").write_text(
        "# Test\n\n<!-- ranking:start -->\nold\n<!-- ranking:end -->\n", encoding="utf-8"
    )
    candidates, snapshot, activities = load_demo_fixture(
        PROJECT_ROOT / "tests" / "fixtures" / "demo.json"
    )
    ranking = score_trial(
        candidates,
        snapshot,
        activities,
        WeekRange(date(2026, 7, 27), date(2026, 8, 2)),
        generated_at=snapshot.observed_at,
        demo=True,
    )
    publish(tmp_path, ranking)
    archive_path = tmp_path / "data" / "rankings" / "2026-07-27.json"
    history_path = tmp_path / "docs" / "weeks" / "2026-07-27.html"
    archive_before = archive_path.read_bytes()
    history_before = history_path.read_bytes()

    stale = mark_publication_stale(tmp_path, "2026-08-03")

    served = json.loads((tmp_path / "docs" / "data" / "latest.json").read_text())
    assert stale.ranking_status == "stale"
    assert served["ranking_status"] == "stale"
    assert served["stale_from_week"] == "2026-08-03"
    assert "Data is stale" in (tmp_path / "docs" / "index.html").read_text(encoding="utf-8")
    assert "Stale — last successful ranking" in (tmp_path / "README.md").read_text(encoding="utf-8")
    assert archive_path.read_bytes() == archive_before
    assert history_path.read_bytes() == history_before


def test_responsive_and_accessibility_contracts_are_present() -> None:
    css = (PROJECT_ROOT / "templates" / "styles.css").read_text(encoding="utf-8")
    template = (PROJECT_ROOT / "templates" / "index.html.j2").read_text(encoding="utf-8")
    assert "@media (max-width: 800px)" in css
    assert "@media (max-width: 460px)" in css
    assert "prefers-reduced-motion" in css
    assert "focus-visible" in css
    assert 'class="skip-link"' in template
    assert "<main>" in template
    assert "<ol" in template
