# Codex Skill Weekly Ranking

A data-first weekly ranking of public Codex-compatible Skills, generated from reproducible GitHub snapshots. Weeks run Monday through Sunday in `Asia/Shanghai`.

The checked-in page currently contains an **explicitly non-live demo** so layout, parity, and scoring can be verified before the first collection. Run `skill-ranker run-daily` with network access to begin real observations; a formal ranking requires two valid Monday boundary snapshots.

<!-- ranking:start -->
## Latest ranking

> **Stale — last successful ranking.** > A safe replacement could not be generated for the week beginning 2026-08-10. The period and timestamps below are from the last successful ranking.

**Week:** 2026-08-03 — 2026-08-09 (Asia/Shanghai)  
**Generated:** 2026-08-09T16:57:49.658112Z · **Algorithm:** `weekly-v1`

| # | Skill | Description | Repository | Score | Allocated Δ stars | Allocated Δ forks | Path commits |
|---:|---|---|---|---:|---:|---:|---:|
| 1 | [database-lookup](https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/skills/database-lookup/SKILL.md) | Query documented public database APIs with explicit endpoints, filters, pagination, and provenance. Use when a scientific, regulatory, financial, or other database-backed fact must be retrieved reproducibly from a named source rather than inferred from general knowledge. | `K-Dense-AI/scientific-agent-skills` | 89.41 | 327.00 | 19.00 | 0 |
| 2 | [pathml](https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/skills/pathml/SKILL.md) | Use PathML for local, research-only computational pathology workflows: load and tile slides, build preprocessing and QC pipelines, manage h5path data, quantify multiplex images, construct spatial graphs, and plan bounded model inference. | `K-Dense-AI/scientific-agent-skills` | 89.41 | 327.00 | 19.00 | 0 |
| 3 | [latchshot-page-capture](https://github.com/github/awesome-copilot/blob/main/skills/latchshot-page-capture/SKILL.md) | Use this skill when a user needs a screenshot, website thumbnail, full-page capture, or PDF of a public HTTP(S) webpage saved as a local artifact through Latchshot, including report, QA, archive, and social-preview workflows. Do not use it for private or authenticated pages, raw HTML, scraping or extraction, arbitrary browser actions, CAPTCHA or anti-bot bypass, or local-file capture. | `github/awesome-copilot` | 88.07 | 130.50 | 18.50 | 0 |
| 4 | [suggest-awesome-github-copilot-skills](https://github.com/github/awesome-copilot/blob/main/skills/suggest-awesome-github-copilot-skills/SKILL.md) | Suggest relevant GitHub Copilot skills from the awesome-copilot repository based on current repository context and chat history, avoiding duplicates with existing skills in this repository, and identifying outdated skills that need updates. | `github/awesome-copilot` | 88.07 | 130.50 | 18.50 | 0 |
| 5 | [research-writing-assistant](https://github.com/Norman-bury/research-writing-skill/blob/main/SKILL.md) | Use when writing academic papers, theses, or research articles - supports brainstorming, chapter writing, literature review, and LaTeX output | `Norman-bury/research-writing-skill` | 86.87 | 46.00 | 3.00 | 0 |
| 6 | [remctl](https://github.com/viticci/remctl/blob/main/SKILL.md) | Use when an agent needs to read, create, edit, complete, inspect, or troubleshoot Apple Reminders through the RemCTL CLI on macOS. | `viticci/remctl` | 85.46 | 26.00 | 2.00 | 0 |
| 7 | [gpt-image2-ppt](https://github.com/JuneYaooo/gpt-image2-ppt-skills/blob/main/SKILL.md) | Generate visually striking PPT slides via OpenAI's gpt-image-2 -- use any style in styles/&lt;id&gt;.md or mimic a user-supplied .pptx template; outputs high-res slide PNGs and a 16:9 .pptx. Use when the user asks to make a presentation, slides, deck, pitch deck, investor PPT, magazine-style PPT, or 做一份 PPT / 生成幻灯片 / 用 gpt-image 生成 PPT / 按这个模板生成 PPT. | `JuneYaooo/gpt-image2-ppt-skills` | 85.42 | 25.00 | 4.00 | 0 |
| 8 | [keep-codex-fast](https://github.com/vibeforge1111/keep-codex-fast/blob/main/SKILL.md) | Use when Codex feels slow or bloated, when local sessions/logs/worktrees/config have grown over time, or when a user wants safe maintenance for Codex Desktop/CLI state. Provides a read-only report by default, backs up before applying changes, archives instead of deleting, normalizes Windows extended paths, prunes dead config projects, rotates large logs, and moves stale worktrees. | `vibeforge1111/keep-codex-fast` | 85.00 | 29.00 | 1.00 | 0 |
| 9 | [ecom-image2](https://github.com/buluslan/gpt-image2-ecommerce/blob/main/SKILL.md) | Use when generating e-commerce product images, advertising materials, or commercial photography using GPT-Image-2 via Codex CLI. Triggers on requests for product photography, promotional banners, social media assets, UGC-style images, packaging design, flat lay, model shots, livestream scenes, exploded views, ghost mannequin, magazine editorial, seasonal campaigns, luxury atmospherics, device mockups, storefront photography, sports campaigns, and other e-commerce visual content. | `buluslan/gpt-image2-ecommerce` | 84.37 | 23.00 | 2.00 | 0 |
| 10 | [seo](https://github.com/Bhanunamikaze/Agentic-SEO-Skill/blob/main/SKILL.md) | Deterministic LLM-first SEO audits for websites, blog posts, and GitHub repositories. Use this when the user asks to "perform SEO analysis", "run SEO audit", "analyze SEO", "check technical SEO", "review schema", "Core Web Vitals", "E-E-A-T", "hreflang", "GEO", "AEO", or GitHub repository SEO optimization. For full/page/repo audits, run bundled scripts for evidence and return prioritized, confidence-labeled fixes. | `Bhanunamikaze/Agentic-SEO-Skill` | 82.82 | 20.00 | 1.00 | 0 |

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

