# Codex Skill Weekly Ranking

A data-first weekly ranking of public Codex-compatible Skills, generated from reproducible GitHub snapshots. Weeks run Monday through Sunday in `Asia/Shanghai`.

The checked-in page currently contains an **explicitly non-live demo** so layout, parity, and scoring can be verified before the first collection. Run `skill-ranker run-daily` with network access to begin real observations; a formal ranking requires two valid Monday boundary snapshots.

<!-- ranking:start -->
## Latest ranking

> **Demo trial · non-live fixture data.** These values are deterministic test fixtures, not GitHub observations. The project is awaiting its first live collection.
**Week:** 2026-07-27 — 2026-08-02 (Asia/Shanghai)  
**Generated:** 2026-07-30T02:17:00Z · **Algorithm:** `trial-v1`

| # | Skill | Description | Repository | Score | Stars | Forks | Path commits |
|---:|---|---|---|---:|---:|---:|---:|
| 1 | [Code Review](https://github.com/demo-fixtures/dev-workflows/blob/main/skills/code-review/SKILL.md) | Fixture Skill for structured code review and actionable findings. | `demo-fixtures/dev-workflows` | 90.91 | 720 | 81 | 10 |
| 2 | [Research Brief](https://github.com/demo-fixtures/research-skills/blob/main/skills/research-brief/SKILL.md) | Fixture Skill that turns a question into a sourced research brief. | `demo-fixtures/research-skills` | 90.45 | 860 | 96 | 8 |
| 3 | [Document Editor](https://github.com/demo-fixtures/document-lab/blob/main/skills/document-editor/SKILL.md) | Fixture Skill for editing and visually checking document output. | `demo-fixtures/document-lab` | 67.95 | 540 | 59 | 7 |
| 4 | [Data Audit](https://github.com/demo-fixtures/data-toolkit/blob/main/skills/data-audit/SKILL.md) | Fixture Skill for profiling tabular data and documenting anomalies. | `demo-fixtures/data-toolkit` | 65.91 | 610 | 77 | 5 |
| 5 | [Test Planner](https://github.com/demo-fixtures/quality-suite/blob/main/skills/test-planner/SKILL.md) | Fixture Skill that creates focused risk-based test plans. | `demo-fixtures/quality-suite` | 64.09 | 390 | 42 | 9 |
| 6 | [Accessibility Review](https://github.com/demo-fixtures/accessibility-kit/blob/main/skills/a11y-review/SKILL.md) | Fixture Skill for keyboard, semantics, and contrast verification. | `demo-fixtures/accessibility-kit` | 52.73 | 275 | 29 | 11 |
| 7 | [Browser Check](https://github.com/demo-fixtures/browser-tools/blob/main/skills/browser-check/SKILL.md) | Fixture Skill for repeatable browser-based acceptance checks. | `demo-fixtures/browser-tools` | 50.91 | 450 | 48 | 4 |
| 8 | [API Design](https://github.com/demo-fixtures/api-craft/blob/main/skills/api-design/SKILL.md) | Fixture Skill for explicit API contracts and compatibility review. | `demo-fixtures/api-craft` | 39.55 | 310 | 33 | 6 |
| 9 | [Release Notes](https://github.com/demo-fixtures/release-ops/blob/main/skills/release-notes/SKILL.md) | Fixture Skill that drafts concise releases from verified changes. | `demo-fixtures/release-ops` | 35.91 | 340 | 38 | 3 |
| 10 | [Mobile QA](https://github.com/demo-fixtures/mobile-checks/blob/main/skills/mobile-qa/SKILL.md) | Fixture Skill for responsive layout and touch-target checks. | `demo-fixtures/mobile-checks` | 26.59 | 185 | 19 | 7 |

[Browse the responsive ranking and history](docs/index.html) · [Read the methodology](METHODOLOGY.md)
<!-- ranking:end -->

## Local setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
skill-ranker build-demo
skill-ranker validate
```

Live read-only commands:

```powershell
$env:GITHUB_TOKEN = "a token supplied only through the environment"
skill-ranker discover
skill-ranker collect
```

Global code search is deliberately opt-in and uses `DISCOVERY_GITHUB_TOKEN`; without it, discovery safely degrades to seeds, the cached catalog, and the version-controlled allowlist. Tokens are never included in JSON, HTML, shell arguments, or logs.

Useful commands:

- `skill-ranker discover --search` — weekly seed scan plus authenticated global search.
- `skill-ranker collect --date YYYY-MM-DD` — complete, immutable repository snapshot.
- `skill-ranker activity --week-start YYYY-MM-DD` — path commit provenance.
- `skill-ranker rank --week-start YYYY-MM-DD` — formal weekly ranking.
- `skill-ranker rank --week-start YYYY-MM-DD --trial` — visibly labeled trial.
- `skill-ranker publish` — rebuild README and Pages from the latest canonical JSON.
- `skill-ranker run-daily` — scheduled job entry point.

## Policy maintenance

`config/seeds.yml` provides repository scans. `allowlist.yml` can add a search-invisible `SKILL.md`, but cannot bypass safe parsing or public/non-archived checks. `denylist.yml` is applied last and always wins. Candidate content is fetched as bounded UTF-8 text and is never imported or executed.

## Data and corrections

Daily snapshots and published ranking artifacts are immutable. A failed or partial collection does not replace prior good data. A missed boundary is never reconstructed, copied forward, or interpreted as zero. Corrections require a documented config or algorithm change and a new generated artifact; published historical JSON should not be silently rewritten.

See [METHODOLOGY.md](METHODOLOGY.md) for formulas, status rules, limitations, and provenance.

