from __future__ import annotations

import html
import json
import re
from dataclasses import replace
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from .io import atomic_write_text, read_json
from .models import Ranking
from .validation import validate_document

START_MARKER = "<!-- ranking:start -->"
END_MARKER = "<!-- ranking:end -->"
MARKDOWN_SPECIAL = re.compile(r"([\\`*_[\]<>|!])")


def markdown_escape(value: object) -> str:
    return MARKDOWN_SPECIAL.sub(r"\\\1", html.escape(str(value), quote=False))


def publish(root: Path, ranking: Ranking) -> None:
    ranking_data = ranking.to_dict()
    validate_document(root, "ranking.schema.json", ranking_data)
    key = ranking.week.start_date
    outputs = _render_outputs(root, ranking, include_archive=True)

    archive_path = root / "data" / "rankings" / f"{key}.json"
    if archive_path.exists():
        prior = read_json(archive_path)
        allowed_upgrade = isinstance(prior, dict) and (
            (prior.get("ranking_status") == "trial" and ranking.ranking_status == "official")
            or (bool(prior.get("demo")) and not ranking.demo)
        )
        if prior != ranking_data and not allowed_upgrade:
            raise FileExistsError(f"Refusing to rewrite immutable ranking: {archive_path}")
    for path, content in outputs.items():
        atomic_write_text(path, content)


def mark_publication_stale(root: Path, attempted_week: str) -> Ranking:
    """Serve the last successful ranking as stale without rewriting its archive."""

    archived = load_ranking(latest_ranking_path(root))
    stale_limitation = (
        "No new valid ranking was produced; this view preserves the last successful "
        "ranking and its original observation times."
    )
    limitations = archived.limitations
    if stale_limitation not in limitations:
        limitations = (*limitations, stale_limitation)
    stale = replace(
        archived,
        ranking_status="stale",
        stale_from_week=attempted_week,
        limitations=limitations,
    )
    validate_document(root, "ranking.schema.json", stale.to_dict())
    for path, content in _render_outputs(root, stale, include_archive=False).items():
        atomic_write_text(path, content)
    return stale


def _render_outputs(root: Path, ranking: Ranking, *, include_archive: bool) -> dict[Path, str]:
    ranking_data = ranking.to_dict()
    key = ranking.week.start_date
    historical = _historical_rankings(root, ranking)
    html_environment = Environment(
        loader=FileSystemLoader(root / "templates"),
        autoescape=True,
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    markdown_environment = Environment(
        loader=FileSystemLoader(root / "templates"),
        autoescape=False,
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    markdown_environment.filters["md"] = markdown_escape
    context: dict[str, Any] = {
        "ranking": ranking_data,
        "status_label": _status_label(ranking),
        "history": historical,
        "is_trial": ranking.ranking_status == "trial",
        "uses_trial_metrics": ranking.algorithm_version == "trial-v1",
        "is_demo": ranking.demo,
        "is_stale": ranking.ranking_status == "stale",
        "request_path": "/",
        "asset_prefix": "",
        "data_href": "data/latest.json",
    }

    html_page = html_environment.get_template("index.html.j2").render(**context)
    historical_page = html_environment.get_template("index.html.j2").render(
        **{
            **context,
            "request_path": f"/weeks/{key}.html",
            "asset_prefix": "../",
            "data_href": f"../data/{key}.json",
        }
    )
    readme_section = markdown_environment.get_template("README-ranking.md.j2").render(**context)
    ranking_json = json.dumps(ranking_data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    css = (root / "templates" / "styles.css").read_text(encoding="utf-8")
    script = (root / "templates" / "site.js").read_text(encoding="utf-8")

    readme_path = root / "README.md"
    readme = readme_path.read_text(encoding="utf-8")
    updated_readme = _replace_marked(readme, readme_section)

    for entry in ranking.entries:
        if (
            html.escape(entry.candidate_key) not in html_page
            or entry.candidate_key not in ranking_json
            or entry.source_url not in readme_section
        ):
            raise ValueError(f"publication parity check failed for {entry.candidate_key}")
    if ranking.week.start_date not in html_page or ranking.week.start_date not in readme_section:
        raise ValueError("publication parity check failed for week key")

    outputs: dict[Path, str] = {
        root / "docs" / "data" / "latest.json": ranking_json,
        root / "docs" / "index.html": html_page,
        root / "docs" / "assets" / "styles.css": css,
        root / "docs" / "assets" / "site.js": script,
        root / "docs" / "METHODOLOGY.md": (root / "METHODOLOGY.md").read_text(encoding="utf-8"),
        readme_path: updated_readme,
    }
    if include_archive:
        outputs.update(
            {
                root / "data" / "rankings" / f"{key}.json": ranking_json,
                root / "docs" / "data" / f"{key}.json": ranking_json,
                root / "docs" / "weeks" / f"{key}.html": historical_page,
            }
        )
    return outputs


def load_ranking(path: Path) -> Ranking:
    value = read_json(path)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return Ranking.from_dict(value)


def latest_ranking_path(root: Path) -> Path:
    paths = sorted((root / "data" / "rankings").glob("*.json"))
    if not paths:
        raise FileNotFoundError("No ranking JSON exists yet")
    return paths[-1]


def _historical_rankings(root: Path, current: Ranking) -> list[dict[str, str]]:
    history: dict[str, dict[str, str]] = {}
    for path in sorted((root / "data" / "rankings").glob("*.json"), reverse=True):
        try:
            value = read_json(path)
            week = value["week"]
            key = str(week["start_date"])
            history[key] = {
                "key": key,
                "label": f"{week['start_date']} — {week['end_date']}",
                "status": str(value["ranking_status"]),
                "href": f"{key}.html",
            }
        except (KeyError, TypeError, ValueError):
            continue
    history[current.week.start_date] = {
        "key": current.week.start_date,
        "label": f"{current.week.start_date} — {current.week.end_date}",
        "status": current.ranking_status,
        "href": f"{current.week.start_date}.html",
    }
    return [history[key] for key in sorted(history, reverse=True)]


def _replace_marked(document: str, replacement: str) -> str:
    if document.count(START_MARKER) != 1 or document.count(END_MARKER) != 1:
        raise ValueError("README ranking markers are missing or duplicated")
    before, rest = document.split(START_MARKER)
    _, after = rest.split(END_MARKER)
    return f"{before}{START_MARKER}\n{replacement.rstrip()}\n{END_MARKER}{after}"


def _status_label(ranking: Ranking) -> str:
    labels = {
        "official": "Official weekly ranking",
        "trial": "Trial ranking",
        "stale": "Stale — last successful ranking",
    }
    if ranking.ranking_status == "stale":
        return labels["stale"]
    if ranking.demo:
        return "Demo trial · non-live fixture data"
    return labels[ranking.ranking_status]
