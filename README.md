# Codex Skill Weekly Ranking

A data-first weekly ranking of public Codex-compatible Skills, generated from reproducible GitHub snapshots. Weeks run Monday through Sunday in `Asia/Shanghai`.

The checked-in page currently contains an **explicitly non-live demo** so layout, parity, and scoring can be verified before the first collection. Run `skill-ranker run-daily` with network access to begin real observations; a formal ranking requires two valid Monday boundary snapshots.

<!-- ranking:start -->
## Latest ranking

> **Stale — last successful ranking.** > A safe replacement could not be generated for the week beginning 2026-07-27. The period and timestamps below are from the last successful ranking.

**Week:** 2026-07-27 — 2026-08-02 (Asia/Shanghai)  
**Generated:** 2026-07-29T20:55:41.662408Z · **Algorithm:** `trial-v1`

| # | Skill | Description | Repository | Score | Stars | Forks | Path commits |
|---:|---|---|---|---:|---:|---:|---:|
| 1 | [latchshot-page-capture](https://github.com/github/awesome-copilot/blob/main/skills/latchshot-page-capture/SKILL.md) | Use this skill when a user needs a screenshot, website thumbnail, full-page capture, or PDF of a public HTTP(S) webpage saved as a local artifact through Latchshot, including report, QA, archive, and social-preview workflows. Do not use it for private or authenticated pages, raw HTML, scraping or extraction, arbitrary browser actions, CAPTCHA or anti-bot bypass, or local-file capture. | `github/awesome-copilot` | 82.22 | 37199 | 4668 | 0 |
| 2 | [suggest-awesome-github-copilot-skills](https://github.com/github/awesome-copilot/blob/main/skills/suggest-awesome-github-copilot-skills/SKILL.md) | Suggest relevant GitHub Copilot skills from the awesome-copilot repository based on current repository context and chat history, avoiding duplicates with existing skills in this repository, and identifying outdated skills that need updates. | `github/awesome-copilot` | 82.22 | 37199 | 4668 | 0 |
| 3 | [database-lookup](https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/skills/database-lookup/SKILL.md) | Query documented public database APIs with explicit endpoints, filters, pagination, and provenance. Use when a scientific, regulatory, financial, or other database-backed fact must be retrieved reproducibly from a named source rather than inferred from general knowledge. | `K-Dense-AI/scientific-agent-skills` | 81.09 | 32115 | 3185 | 0 |
| 4 | [pathml](https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/skills/pathml/SKILL.md) | Use PathML for local, research-only computational pathology workflows: load and tile slides, build preprocessing and QC pipelines, manage h5path data, quantify multiplex images, construct spatial graphs, and plan bounded model inference. | `K-Dense-AI/scientific-agent-skills` | 81.09 | 32115 | 3185 | 0 |
| 5 | [cli-creator](https://github.com/openai/skills/blob/main/skills/.curated/cli-creator/SKILL.md) | Build a composable CLI for Codex from API docs, an OpenAPI spec, existing curl examples, an SDK, a web app, an admin tool, or a local script. Use when the user wants Codex to create a command-line tool that can run from any repo, expose composable read/write commands, return stable JSON, manage auth, and pair with a companion skill. | `openai/skills` | 74.59 | 24315 | 1652 | 0 |
| 6 | [figma-create-design-system-rules](https://github.com/openai/skills/blob/main/skills/.curated/figma-create-design-system-rules/SKILL.md) | Generates custom design system rules for the user's codebase. Use when user says "create design system rules", "generate rules for my project", "set up design rules", "customize design system guidelines", or wants to establish project-specific conventions for Figma-to-code workflows. Requires Figma MCP server connection. | `openai/skills` | 74.59 | 24315 | 1652 | 0 |
| 7 | [research-writing-assistant](https://github.com/Norman-bury/research-writing-skill/blob/main/SKILL.md) | Use when writing academic papers, theses, or research articles - supports brainstorming, chapter writing, literature review, and LaTeX output | `Norman-bury/research-writing-skill` | 65.50 | 2935 | 198 | 0 |
| 8 | [nvidia-skill-finder](https://github.com/NVIDIA/skills/blob/main/plugins/nvidia-skills/skills/nvidia-skill-finder/SKILL.md) | Use for NVIDIA-related requests where an NVIDIA skill might help, even if the user did not ask for a skill. Trigger on NVIDIA products, hardware, software, SDKs, GPUs, Jetson/JetPack/L4T/BSP/SDK Manager/driver/flashing/setup, CUDA, NIM, NeMo, Omniverse/OpenUSD/SimReady, RAPIDS/cuDF, cuPyNumeric, cuOpt, Dynamo, Holoscan, TensorRT, DeepStream, VSS, TAO, NGC/NVCF. Do not use for generic non-NVIDIA route, optimize, deploy, AI, video, data, or infrastructure tasks. | `NVIDIA/skills` | 62.00 | 2727 | 318 | 0 |
| 9 | [aiq-deploy](https://github.com/NVIDIA/skills/blob/main/skills/aiq-deploy/SKILL.md) | Use when asked to install, deploy, run, validate, troubleshoot, or stop NVIDIA AI-Q Blueprint infrastructure. | `NVIDIA/skills` | 62.00 | 2727 | 318 | 0 |
| 10 | [keep-codex-fast](https://github.com/vibeforge1111/keep-codex-fast/blob/main/SKILL.md) | Use when Codex feels slow or bloated, when local sessions/logs/worktrees/config have grown over time, or when a user wants safe maintenance for Codex Desktop/CLI state. Provides a read-only report by default, backs up before applying changes, archives instead of deleting, normalizes Windows extended paths, prunes dead config projects, rotates large logs, and moves stale worktrees. | `vibeforge1111/keep-codex-fast` | 54.85 | 1489 | 84 | 0 |

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

