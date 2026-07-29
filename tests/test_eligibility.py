from pathlib import Path

import pytest

from skill_ranker.config import ExplicitCandidate, Policy, Seed, load_policy
from skill_ranker.eligibility import EligibilityError, build_candidate, parse_skill


def policy(*, denied_repositories: frozenset[str] = frozenset()) -> Policy:
    return Policy(
        seeds=(),
        allowlist=(),
        denied_repositories=denied_repositories,
        denied_keys=frozenset(),
        denied_paths=frozenset(),
    )


def valid_skill(description: str = "A useful Codex compatibility workflow.") -> str:
    return (
        f"---\nname: Useful Skill\ndescription: {description}\n---\nUse this Codex Skill safely.\n"
    )


def repository() -> dict[str, object]:
    return {
        "id": 42,
        "node_id": "R_42",
        "full_name": "owner/repository",
        "default_branch": "main",
        "private": False,
        "archived": False,
    }


def test_safe_frontmatter_is_parsed_and_normalized() -> None:
    metadata = parse_skill(valid_skill("A useful   Codex\n  workflow description."))
    assert metadata.name == "Useful Skill"
    assert metadata.description == "A useful Codex workflow description."


@pytest.mark.parametrize(
    ("content", "reason"),
    [
        ("name: no delimiters", "begin"),
        ("---\nname: x\n", "not closed"),
        (
            "---\nname: bad/name\ndescription: A complete valid description.\n---\nCodex",
            "name",
        ),
        ("---\nname: Valid Name\ndescription: short\n---\nCodex", "8-500"),
        ("---\n!!python/object:os.system {}\n---\nCodex", "malformed"),
        (valid_skill() + "\x00", "binary"),
    ],
)
def test_malformed_or_unsafe_skill_is_rejected(content: str, reason: str) -> None:
    with pytest.raises(EligibilityError, match=reason):
        parse_skill(content)


def test_compatibility_evidence_is_required_unless_allowlisted() -> None:
    content = (
        "---\nname: Useful Skill\ndescription: A complete useful description.\n---\nGeneric text.\n"
    )
    with pytest.raises(EligibilityError, match="compatibility"):
        parse_skill(content)
    assert parse_skill(content, require_compatibility_evidence=False).name == "Useful Skill"


def test_denylist_wins_over_allowlist() -> None:
    denied = policy(denied_repositories=frozenset({"owner/repository"}))
    with pytest.raises(EligibilityError, match="denylisted"):
        build_candidate(
            repository(),
            "skills/useful/SKILL.md",
            valid_skill(),
            discovered_via="allowlist",
            checked_at="2026-07-30T00:00:00Z",
            policy=denied,
            allowlisted=True,
        )


def test_candidate_url_and_stable_key_are_derived_from_validated_parts() -> None:
    candidate = build_candidate(
        repository(),
        "skills/useful/SKILL.md",
        valid_skill(),
        discovered_via="seed",
        checked_at="2026-07-30T00:00:00Z",
        policy=policy(),
    )
    assert candidate.key == "42:skills/useful/SKILL.md"
    assert candidate.source_url == (
        "https://github.com/owner/repository/blob/main/skills/useful/SKILL.md"
    )


def test_config_precedence_and_defaults(tmp_path: Path) -> None:
    config = tmp_path / "config"
    config.mkdir()
    (config / "seeds.yml").write_text(
        "repositories:\n  - repository: owner/repo\n", encoding="utf-8"
    )
    (config / "allowlist.yml").write_text(
        "skills:\n  - repository: owner/repo\n    path: SKILL.md\n", encoding="utf-8"
    )
    (config / "denylist.yml").write_text(
        "repositories: [OWNER/REPO]\nkeys: ['42:SKILL.md']\n", encoding="utf-8"
    )
    (config / "policy.yml").write_text("top_n: 7\n", encoding="utf-8")
    loaded = load_policy(tmp_path)
    assert loaded.seeds == (Seed("owner/repo"),)
    assert loaded.allowlist == (ExplicitCandidate("owner/repo", "SKILL.md"),)
    assert loaded.denied_repositories == frozenset({"owner/repo"})
    assert loaded.top_n == 7
    assert loaded.max_skills_per_repository == 2


def test_project_seed_repositories_cover_trusted_skill_sources() -> None:
    project_root = Path(__file__).parents[1]

    loaded = load_policy(project_root)

    assert {seed.repository for seed in loaded.seeds} == {
        "openai/skills",
        "anthropics/skills",
        "MicrosoftDocs/Agent-Skills",
        "github/awesome-copilot",
        "NVIDIA/skills",
        "K-Dense-AI/scientific-agent-skills",
    }
