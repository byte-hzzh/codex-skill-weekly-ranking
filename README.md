# Codex Skill Weekly Ranking

A data-first weekly ranking of public Codex-compatible Skills, generated from reproducible GitHub snapshots. Weeks run Monday through Sunday in `Asia/Shanghai`.

The checked-in page currently contains an **explicitly non-live demo** so layout, parity, and scoring can be verified before the first collection. Run `skill-ranker run-daily` with network access to begin real observations; a formal ranking requires two valid Monday boundary snapshots.

<!-- ranking:start -->
## Latest ranking

> **Stale — last successful ranking.** > A safe replacement could not be generated for the week beginning 2026-07-27. The period and timestamps below are from the last successful ranking.

**Week:** 2026-07-27 — 2026-08-02 (Asia/Shanghai)  
**Generated:** 2026-07-29T20:29:13.701734Z · **Algorithm:** `trial-v1`

| # | Skill | Description | Repository | Score | Stars | Forks | Path commits |
|---:|---|---|---|---:|---:|---:|---:|
| 1 | [cli-creator](https://github.com/openai/skills/blob/main/skills/.curated/cli-creator/SKILL.md) | Build a composable CLI for Codex from API docs, an OpenAPI spec, existing curl examples, an SDK, a web app, an admin tool, or a local script. Use when the user wants Codex to create a command-line tool that can run from any repo, expose composable read/write commands, return stable JSON, manage auth, and pair with a companion skill. | `openai/skills` | 50.00 | 24315 | 1652 | 0 |
| 2 | [figma-create-design-system-rules](https://github.com/openai/skills/blob/main/skills/.curated/figma-create-design-system-rules/SKILL.md) | Generates custom design system rules for the user's codebase. Use when user says "create design system rules", "generate rules for my project", "set up design rules", "customize design system guidelines", or wants to establish project-specific conventions for Figma-to-code workflows. Requires Figma MCP server connection. | `openai/skills` | 50.00 | 24315 | 1652 | 0 |

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

