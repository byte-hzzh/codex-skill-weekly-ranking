# Codex Skill Weekly Ranking

A data-first weekly ranking of public Codex-compatible Skills, generated from reproducible GitHub snapshots. Weeks run Monday through Sunday in `Asia/Shanghai`.

The checked-in page currently contains an **explicitly non-live demo** so layout, parity, and scoring can be verified before the first collection. Run `skill-ranker run-daily` with network access to begin real observations; a formal ranking requires two valid Monday boundary snapshots.

<!-- ranking:start -->
## Latest ranking

> **Stale — last successful ranking.** > A safe replacement could not be generated for the week beginning 2026-10-12. The period and timestamps below are from the last successful ranking.

**Week:** 2026-10-05 — 2026-10-11 (Asia/Shanghai)  
**Generated:** 2026-10-11T20:23:15.508109Z · **Algorithm:** `weekly-v1`

| # | Skill | Description | Repository | Score | Allocated Δ stars | Allocated Δ forks | Path commits |
|---:|---|---|---|---:|---:|---:|---:|
| 1 | [version-bump](https://github.com/thedotmack/claude-mem/blob/main/plugin/skills/version-bump/SKILL.md) | Automated semantic versioning and release workflow for Claude Code plugins. Handles version increments across package.json, marketplace.json, plugin.json manifests, build verification, git tagging, GitHub releases, and changelog generation. NPM publishing is the final human-required handoff because the maintainer raised npm security. | `thedotmack/claude-mem` | 98.32 | 2724.00 | 192.75 | 2 |
| 2 | [autoplan](https://github.com/garrytan/gstack/blob/main/autoplan/SKILL.md) | Auto-review pipeline — reads the full CEO, design, eng, and DX review skills from disk and runs them sequentially with auto-decisions using 6 decision principles. (gstack) | `garrytan/gstack` | 93.36 | 87.93 | 9.68 | 11 |
| 3 | [review](https://github.com/garrytan/gstack/blob/main/review/SKILL.md) | Pre-landing PR review. (gstack) | `garrytan/gstack` | 92.66 | 73.28 | 8.07 | 9 |
| 4 | [openclaw-ci-limits](https://github.com/openclaw/openclaw/blob/main/.agents/skills/openclaw-ci-limits/SKILL.md) | Manage OpenClaw GitHub Actions and Blacksmith CI capacity, runner-registration budgets, fanout caps, main-push single-flight, shard sizing, hosted-runner offload, queue health, and safe ramp-down/ramp-up changes. Use when tuning \`.github/workflows/\*\`, \`docs/ci.md\`, CI runner labels, matrix \`max-parallel\`, ClawSweeper/Blacksmith burst protection, CodeQL runner placement, or investigating slow/queued OpenClaw CI. | `openclaw/openclaw` | 92.01 | 64.48 | 16.55 | 4 |
| 5 | [codebase-memory-mcp](https://github.com/github/awesome-copilot/blob/main/skills/codebase-memory-mcp/SKILL.md) | Use when exploring unfamiliar code, mapping architecture, finding symbols or relationships, tracing callers, callees, data flow or dependencies, assessing impact, auditing dead or complex code, or handling explicit Codebase Memory requests. Otherwise skip tasks confined to a supplied known file, tiny one-file check, exact literal, configuration value, error string, or non-code text. | `github/awesome-copilot` | 92.00 | 91.60 | 18.00 | 1 |
| 6 | [using-superpowers](https://github.com/obra/superpowers/blob/main/skills/using-superpowers/SKILL.md) | Use when starting any conversation - establishes how to find and use skills, requiring skill invocation before ANY response including clarifying questions | `obra/superpowers` | 88.47 | 2372.00 | 204.00 | 0 |
| 7 | [config-codex-cli](https://github.com/diegosouzapw/OmniRoute/blob/release%2Fv3.8.51/skills/config-codex-cli/SKILL.md) | Step-by-step agent workflow to configure the OpenAI Codex CLI on any machine (Linux, macOS, Windows) to use OmniRoute as an OpenAI-compatible backend. Detects OS and shell, writes config.toml and 7 named profiles, sets environment variables, and verifies the setup. | `diegosouzapw/OmniRoute` | 88.24 | 1167.50 | 212.50 | 0 |
| 8 | [omni-cli-tools](https://github.com/diegosouzapw/OmniRoute/blob/release%2Fv3.8.51/skills/omni-cli-tools/SKILL.md) | Manage CLI tool integrations exposed via the API. List, configure, and invoke CLI tool plugins that extend OmniRoute's automation surface. | `diegosouzapw/OmniRoute` | 88.24 | 1167.50 | 212.50 | 0 |
| 9 | [mem-search](https://github.com/thedotmack/claude-mem/blob/main/cowork/skills/mem-search/SKILL.md) | This skill should be used when the user asks to "search memory", "what do you remember about X", "check claude-mem", "mem search", "find past observations", "what did we do last session", or wants prior-session context about a project, decision, file, or task. Searches the user's Claude-Mem (cmem.ai) memory. | `thedotmack/claude-mem` | 87.77 | 908.00 | 64.25 | 0 |
| 10 | [hand-drawn-diagrams](https://github.com/nexu-io/open-design/blob/main/skills/hand-drawn-diagrams/SKILL.md) | Generate hand-drawn Excalidraw diagrams from a prompt — animated SVG, hosted edit link, and PNG export. Works with Claude Code, Codex, Gemini CLI, and any agent supporting standard skill paths. | `nexu-io/open-design` | 86.78 | 571.50 | 41.00 | 0 |

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

