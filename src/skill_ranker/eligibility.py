from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import quote

import yaml

from .config import Policy
from .models import Candidate

NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _.-]{0,79}$")
REPOSITORY_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


class EligibilityError(ValueError):
    pass


@dataclass(frozen=True)
class SkillMetadata:
    name: str
    description: str


def parse_skill(
    content: str,
    *,
    max_skill_bytes: int = 131_072,
    max_frontmatter_bytes: int = 16_384,
    require_compatibility_evidence: bool = True,
) -> SkillMetadata:
    encoded = content.encode("utf-8")
    if len(encoded) > max_skill_bytes:
        raise EligibilityError("SKILL.md exceeds the size limit")
    if "\x00" in content:
        raise EligibilityError("SKILL.md contains binary-like data")
    normalized = content.replace("\r\n", "\n")
    lines = normalized.splitlines()
    if not lines or lines[0].strip() != "---":
        raise EligibilityError("SKILL.md must begin with YAML frontmatter")
    try:
        closing = next(
            index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---"
        )
    except StopIteration as error:
        raise EligibilityError("SKILL.md frontmatter is not closed") from error
    frontmatter = "\n".join(lines[1:closing])
    if len(frontmatter.encode("utf-8")) > max_frontmatter_bytes:
        raise EligibilityError("SKILL.md frontmatter exceeds the size limit")
    try:
        value = yaml.safe_load(frontmatter)
    except yaml.YAMLError as error:
        raise EligibilityError("SKILL.md frontmatter is malformed") from error
    if not isinstance(value, dict):
        raise EligibilityError("SKILL.md frontmatter must be a mapping")
    name = value.get("name")
    description = value.get("description")
    if not isinstance(name, str) or not NAME_PATTERN.fullmatch(name.strip()):
        raise EligibilityError("frontmatter name is missing or invalid")
    if not isinstance(description, str) or not 8 <= len(description.strip()) <= 500:
        raise EligibilityError("frontmatter description must be 8-500 characters")
    body = "\n".join(lines[closing + 1 :]).casefold()
    compatibility_terms = ("codex", "agent skill", "agentskills", "skill instructions")
    if require_compatibility_evidence and not any(term in body for term in compatibility_terms):
        raise EligibilityError("no Codex/Agent Skills compatibility evidence")
    return SkillMetadata(name=name.strip(), description=" ".join(description.split()))


def build_candidate(
    repository_data: dict[str, object],
    path: str,
    content: str,
    *,
    discovered_via: str,
    checked_at: str,
    policy: Policy,
    allowlisted: bool = False,
) -> Candidate:
    repository = str(repository_data.get("full_name", ""))
    if not REPOSITORY_PATTERN.fullmatch(repository):
        raise EligibilityError("repository full_name is invalid")
    normalized_path = path.replace("\\", "/")
    if (
        not normalized_path.endswith("/SKILL.md") and normalized_path != "SKILL.md"
    ) or ".." in normalized_path.split("/"):
        raise EligibilityError("candidate path must point to SKILL.md")
    if bool(repository_data.get("private")):
        raise EligibilityError("private repositories are ineligible")
    if bool(repository_data.get("archived")):
        raise EligibilityError("archived repositories are ineligible")
    raw_repository_id = repository_data.get("id")
    if not isinstance(raw_repository_id, int):
        raise EligibilityError("repository id is missing or invalid")
    repository_id = raw_repository_id
    key = f"{repository_id}:{normalized_path}"
    deny_reason = denial_reason(policy, key, repository, normalized_path)
    if deny_reason:
        raise EligibilityError(deny_reason)
    metadata = parse_skill(
        content,
        max_skill_bytes=policy.max_skill_bytes,
        max_frontmatter_bytes=policy.max_frontmatter_bytes,
        require_compatibility_evidence=not allowlisted,
    )
    default_branch = str(repository_data.get("default_branch", "main"))
    encoded_path = "/".join(quote(part, safe=".-_") for part in normalized_path.split("/"))
    repository_url = f"https://github.com/{repository}"
    return Candidate(
        key=key,
        repository_id=repository_id,
        repository_node_id=str(repository_data.get("node_id", "")),
        repository=repository,
        default_branch=default_branch,
        path=normalized_path,
        name=metadata.name,
        description=metadata.description,
        source_url=f"{repository_url}/blob/{quote(default_branch, safe='.-_')}/{encoded_path}",
        repository_url=repository_url,
        discovered_via=discovered_via,
        checked_at=checked_at,
    )


def denial_reason(policy: Policy, key: str, repository: str, path: str) -> str | None:
    if repository.casefold() in policy.denied_repositories:
        return "repository is denylisted"
    if key in policy.denied_keys:
        return "candidate key is denylisted"
    if path.casefold() in policy.denied_paths:
        return "candidate path is denylisted"
    return None
