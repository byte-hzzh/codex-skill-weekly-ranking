from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import Policy
from .dates import iso_utc
from .eligibility import EligibilityError, build_candidate, denial_reason
from .github import GitHubClient, GitHubError
from .io import atomic_write_json
from .models import SCHEMA_VERSION, Candidate


@dataclass(frozen=True)
class DiscoveryResult:
    candidates: tuple[Candidate, ...]
    errors: tuple[str, ...]
    search_degraded: bool


def discover(
    client: GitHubClient,
    policy: Policy,
    *,
    include_search: bool = False,
    checked_at: str | None = None,
) -> DiscoveryResult:
    checked = checked_at or iso_utc()
    locations: dict[tuple[str, str], tuple[str, bool]] = {}
    errors: list[str] = []

    for seed in policy.seeds:
        try:
            seed_repository_data = client.repository(seed.repository)
            branch = str(seed_repository_data.get("default_branch", "main"))
            for tree_item in client.tree(seed.repository, branch):
                path = tree_item.get("path")
                if (
                    tree_item.get("type") == "blob"
                    and isinstance(path, str)
                    and _is_skill_path(path)
                ):
                    locations[(seed.repository, path)] = ("seed", False)
        except (GitHubError, ValueError) as error:
            errors.append(f"{seed.repository}: {error}")

    for explicit_candidate in policy.allowlist:
        locations[(explicit_candidate.repository, explicit_candidate.path)] = (
            "allowlist",
            True,
        )

    search_degraded = False
    if include_search:
        try:
            for search_item in client.search_skill_files("Codex in:file filename:SKILL.md"):
                repository = search_item.get("repository")
                path = search_item.get("path")
                if isinstance(repository, dict) and isinstance(path, str):
                    full_name = repository.get("full_name")
                    if isinstance(full_name, str) and _is_skill_path(path):
                        locations[(full_name, path)] = ("code-search", False)
        except GitHubError as error:
            search_degraded = True
            errors.append(f"global search skipped: {error}")

    repository_cache: dict[str, dict[str, Any]] = {}
    candidates: dict[str, Candidate] = {}
    for (repository_name, path), (source, allowlisted) in sorted(locations.items()):
        try:
            candidate_repository_data = repository_cache.get(repository_name)
            if candidate_repository_data is None:
                candidate_repository_data = client.repository(repository_name)
                repository_cache[repository_name] = candidate_repository_data
            content = client.content_text(
                repository_name,
                path,
                str(candidate_repository_data.get("default_branch", "main")),
                max_bytes=policy.max_skill_bytes,
            )
            candidate = build_candidate(
                candidate_repository_data,
                path,
                content,
                discovered_via=source,
                checked_at=checked,
                policy=policy,
                allowlisted=allowlisted,
            )
            candidates[candidate.key] = candidate
        except (GitHubError, EligibilityError, KeyError, ValueError) as error:
            errors.append(f"{repository_name}/{path}: {error}")

    return DiscoveryResult(
        candidates=tuple(sorted(candidates.values(), key=lambda item: item.key)),
        errors=tuple(errors),
        search_degraded=search_degraded,
    )


def write_catalog(path: Path, result: DiscoveryResult) -> None:
    if not result.candidates:
        raise ValueError("Refusing to replace candidate catalog with an empty result")
    atomic_write_json(
        path,
        {
            "schema_version": SCHEMA_VERSION,
            "generated_at": iso_utc(),
            "search_degraded": result.search_degraded,
            "errors": list(result.errors),
            "candidates": [candidate.to_dict() for candidate in result.candidates],
        },
    )


def merge_candidates(groups: Iterable[Iterable[Candidate]]) -> tuple[Candidate, ...]:
    merged: dict[str, Candidate] = {}
    for group in groups:
        for candidate in group:
            merged[candidate.key] = candidate
    return tuple(sorted(merged.values(), key=lambda item: item.key))


def preserve_cached_candidates(
    result: DiscoveryResult, cached: Iterable[Candidate], policy: Policy
) -> DiscoveryResult:
    """Keep prior validated candidates when a bounded discovery pass omits them.

    Code search and seed scans are discovery aids, not authoritative deletion
    ledgers. New validated records replace cached provenance for the same stable
    key, while denylist changes still take effect immediately.
    """

    merged = merge_candidates((cached, result.candidates))
    allowed = tuple(
        candidate
        for candidate in merged
        if denial_reason(policy, candidate.key, candidate.repository, candidate.path) is None
    )
    return DiscoveryResult(
        candidates=allowed,
        errors=result.errors,
        search_degraded=result.search_degraded,
    )


def _is_skill_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return normalized == "SKILL.md" or normalized.endswith("/SKILL.md")
