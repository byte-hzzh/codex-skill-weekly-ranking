from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class Seed:
    repository: str


@dataclass(frozen=True)
class ExplicitCandidate:
    repository: str
    path: str


@dataclass(frozen=True)
class Policy:
    seeds: tuple[Seed, ...]
    allowlist: tuple[ExplicitCandidate, ...]
    denied_repositories: frozenset[str]
    denied_keys: frozenset[str]
    denied_paths: frozenset[str]
    max_skills_per_repository: int = 2
    max_skills_per_seed: int = 100
    top_n: int = 10
    max_frontmatter_bytes: int = 16_384
    max_skill_bytes: int = 131_072
    boundary_tolerance_hours: int = 6


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    return value


def load_policy(root: Path) -> Policy:
    seeds_data = _load_yaml(root / "config" / "seeds.yml")
    allow_data = _load_yaml(root / "config" / "allowlist.yml")
    deny_data = _load_yaml(root / "config" / "denylist.yml")
    policy_data = _load_yaml(root / "config" / "policy.yml")
    max_skills_per_seed = policy_data.get("max_skills_per_seed", 100)
    if (
        isinstance(max_skills_per_seed, bool)
        or not isinstance(max_skills_per_seed, int)
        or max_skills_per_seed <= 0
    ):
        raise ValueError("max_skills_per_seed must be a positive integer")
    return Policy(
        seeds=tuple(Seed(str(item["repository"])) for item in seeds_data.get("repositories", [])),
        allowlist=tuple(
            ExplicitCandidate(str(item["repository"]), str(item["path"]))
            for item in allow_data.get("skills", [])
        ),
        denied_repositories=frozenset(
            str(item).casefold() for item in deny_data.get("repositories", [])
        ),
        denied_keys=frozenset(str(item) for item in deny_data.get("keys", [])),
        denied_paths=frozenset(str(item).casefold() for item in deny_data.get("paths", [])),
        max_skills_per_repository=int(policy_data.get("max_skills_per_repository", 2)),
        max_skills_per_seed=max_skills_per_seed,
        top_n=int(policy_data.get("top_n", 10)),
        max_frontmatter_bytes=int(policy_data.get("max_frontmatter_bytes", 16_384)),
        max_skill_bytes=int(policy_data.get("max_skill_bytes", 131_072)),
        boundary_tolerance_hours=int(policy_data.get("boundary_tolerance_hours", 6)),
    )
