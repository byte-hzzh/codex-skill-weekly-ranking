# Methodology

## Calendar and status

All intervals use `Asia/Shanghai`. A week is the half-open interval from Monday 00:00 through the next Monday 00:00; displays show the inclusive Monday–Sunday dates. An `official` ranking requires complete repository snapshots within six hours of both boundaries and complete path activity. Before that, output is `trial`. If a new safe artifact cannot be made, the last successful artifact remains published and is marked `stale` by the recovery workflow rather than inventing values.

The repository initially publishes fixture-backed demo output only. Demo artifacts set `demo: true` and say they are non-live in both README and HTML.

## Formal score (`weekly-v1`)

For every repository, raw weekly star and fork deltas are retained. Negative deltas are floored at zero only for the positive heat score. For eligible Skill `i`:

```text
share_i = (1 + path_commits_i) / sum(1 + path_commits_j)
```

The share allocates repository deltas without duplicating the complete repository gain for every Skill. `log1p` allocated stars, allocated forks, and path commits are converted to deterministic average-rank percentiles.

```text
score = 100 × (0.65 × star_percentile
             + 0.15 × fork_percentile
             + 0.20 × commit_percentile)
```

Ties resolve by score, allocated stars, path commits, normalized repository name, and Skill path. At most two Skills per repository can enter the Top 10.

## Trial score (`trial-v1`)

```text
trial_score = 100 × (0.50 × total_star_percentile
                   + 0.15 × total_fork_percentile
                   + 0.35 × recent_path_commit_percentile)
```

Trial and official results use different algorithm versions and visible labels.

## Limitations

- Repository stars and forks are shared aggregate attention signals, not per-Skill installs.
- Daily counters measure net change, not gross stars and unstars.
- GitHub stargazer event times are intentionally not a dependency.
- Commit count is default-branch history touching a path, not effort or quality.
- Path moves, rebases, force pushes, bots, and generated changes can affect activity.
- Code-search and API limits can delay discovery; absence from the pool is not a claim of incompatibility.

Every ranking entry exposes its stable repository-id/path key, public source URLs, raw or cumulative metrics, normalized components, score, algorithm version, generation time, and source observation times.

