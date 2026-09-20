# Codex Skill Weekly Ranking

A data-first weekly ranking of public Codex-compatible Skills, generated from reproducible GitHub snapshots. Weeks run Monday through Sunday in `Asia/Shanghai`.

The checked-in page currently contains an **explicitly non-live demo** so layout, parity, and scoring can be verified before the first collection. Run `skill-ranker run-daily` with network access to begin real observations; a formal ranking requires two valid Monday boundary snapshots.

<!-- ranking:start -->
## Latest ranking

> **Stale — last successful ranking.** > A safe replacement could not be generated for the week beginning 2026-09-14. The period and timestamps below are from the last successful ranking.

**Week:** 2026-09-07 — 2026-09-13 (Asia/Shanghai)  
**Generated:** 2026-09-13T18:53:11.849878Z · **Algorithm:** `weekly-v1`

| # | Skill | Description | Repository | Score | Allocated Δ stars | Allocated Δ forks | Path commits |
|---:|---|---|---|---:|---:|---:|---:|
| 1 | [unified-memory](https://github.com/affaan-m/ECC/blob/main/.agents/skills/unified-memory/SKILL.md) | Share durable, inspectable context and handoffs between Claude, Codex, Hermes, Cursor, OpenCode, and other agents through the local ECC Memory Vault. Use when an agent must save work state, transfer context, resume another agent's task, or search shared project knowledge. | `affaan-m/ECC` | 97.39 | 836.00 | 99.88 | 1 |
| 2 | [unified-memory](https://github.com/affaan-m/ECC/blob/main/.cursor/skills/unified-memory/SKILL.md) | Share durable, inspectable context and handoffs between Claude, Codex, Hermes, Cursor, OpenCode, and other agents through the local ECC Memory Vault. Use when an agent must save work state, transfer context, resume another agent's task, or search shared project knowledge. | `affaan-m/ECC` | 97.39 | 836.00 | 99.88 | 1 |
| 3 | [openclaw-ci-limits](https://github.com/openclaw/openclaw/blob/main/.agents/skills/openclaw-ci-limits/SKILL.md) | Manage OpenClaw GitHub Actions and Blacksmith CI capacity, runner-registration budgets, fanout caps, main-push single-flight, shard sizing, hosted-runner offload, queue health, and safe ramp-down/ramp-up changes. Use when tuning \`.github/workflows/\*\`, \`docs/ci.md\`, CI runner labels, matrix \`max-parallel\`, ClawSweeper/Blacksmith burst protection, CodeQL runner placement, or investigating slow/queued OpenClaw CI. | `openclaw/openclaw` | 93.66 | 147.87 | 40.52 | 7 |
| 4 | [init-deep](https://github.com/code-yeongyu/oh-my-openagent/blob/dev/packages/omo-codex/plugin/skills/init-deep/SKILL.md) | (builtin) Initialize hierarchical AGENTS.md knowledge base | `code-yeongyu/oh-my-openagent` | 93.03 | 151.20 | 15.60 | 2 |
| 5 | [autoreview](https://github.com/openclaw/openclaw/blob/main/.agents/skills/autoreview/SKILL.md) | Structured Codex, Claude, Amp, Pi, or Kimi code review when explicitly requested. | `openclaw/openclaw` | 90.64 | 73.94 | 20.26 | 3 |
| 6 | [autoplan](https://github.com/garrytan/gstack/blob/main/autoplan/SKILL.md) | Auto-review pipeline — reads the full CEO, design, eng, and DX review skills from disk and runs them sequentially with auto-decisions using 6 decision principles. (gstack) | `garrytan/gstack` | 90.46 | 93.25 | 8.00 | 1 |
| 7 | [benchmark](https://github.com/garrytan/gstack/blob/main/benchmark/SKILL.md) | Performance regression detection using the browse daemon. (gstack) | `garrytan/gstack` | 90.46 | 93.25 | 8.00 | 1 |
| 8 | [database-lookup](https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/skills/database-lookup/SKILL.md) | Query documented public database APIs with explicit endpoints, filters, pagination, and provenance. Use when a scientific, regulatory, financial, or other database-backed fact must be retrieved reproducibly from a named source rather than inferred from general knowledge. | `K-Dense-AI/scientific-agent-skills` | 90.32 | 93.06 | 7.25 | 3 |
| 9 | [using-superpowers](https://github.com/obra/superpowers/blob/main/skills/using-superpowers/SKILL.md) | Use when starting any conversation - establishes how to find and use skills, requiring skill invocation before ANY response including clarifying questions | `obra/superpowers` | 89.05 | 3788.00 | 293.00 | 0 |
| 10 | [config-codex-cli](https://github.com/diegosouzapw/OmniRoute/blob/release%2Fv3.8.51/skills/config-codex-cli/SKILL.md) | Step-by-step agent workflow to configure the OpenAI Codex CLI on any machine (Linux, macOS, Windows) to use OmniRoute as an OpenAI-compatible backend. Detects OS and shell, writes config.toml and 7 named profiles, sets environment variables, and verifies the setup. | `diegosouzapw/OmniRoute` | 88.64 | 1850.50 | 269.50 | 0 |

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

