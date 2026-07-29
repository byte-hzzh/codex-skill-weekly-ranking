from pathlib import Path

from skill_ranker.config import Policy, Seed
from skill_ranker.discovery import DiscoveryResult, discover, preserve_cached_candidates
from skill_ranker.fixtures import load_demo_fixture

FIXTURE = Path(__file__).parent / "fixtures" / "demo.json"


class SearchClient:
    def __init__(self) -> None:
        self.queries: list[str] = []

    def search_skill_files(self, query: str) -> tuple[()]:
        self.queries.append(query)
        return ()


class SeedClient:
    def __init__(self) -> None:
        self.content_requests: list[tuple[str, str]] = []
        self.trees = {
            "alpha/skills": (
                "z/SKILL.md",
                "a\\SKILL.md",
                "a/SKILL.md",
                "m/SKILL.md",
            ),
            "beta/skills": ("c/SKILL.md", "b/SKILL.md", "a/SKILL.md"),
        }

    def repository(self, repository: str) -> dict[str, object]:
        return {
            "id": 1 if repository == "alpha/skills" else 2,
            "node_id": f"R_{repository}",
            "full_name": repository,
            "default_branch": "main",
            "private": False,
            "archived": False,
        }

    def tree(self, repository: str, _branch: str) -> list[dict[str, str]]:
        return [{"type": "blob", "path": path} for path in self.trees[repository]]

    def content_text(self, repository: str, path: str, _branch: str, *, max_bytes: int) -> str:
        self.content_requests.append((repository, path))
        return (
            "---\nname: Selected Skill\n"
            "description: A selected Codex-compatible skill.\n---\nCodex\n"
        )


def test_discovery_uses_valid_codex_evidence_query() -> None:
    client = SearchClient()
    policy = Policy(
        seeds=(),
        allowlist=(),
        denied_repositories=frozenset(),
        denied_keys=frozenset(),
        denied_paths=frozenset(),
    )

    result = discover(
        client,  # type: ignore[arg-type]
        policy,
        include_search=True,
        checked_at="2026-07-30T00:00:00Z",
    )

    assert client.queries == ["Codex in:file filename:SKILL.md"]
    assert result.search_degraded is False


def test_seed_scan_sorts_normalized_paths_and_caps_each_repository_independently() -> None:
    client = SeedClient()
    policy = Policy(
        seeds=(Seed("alpha/skills"), Seed("beta/skills")),
        allowlist=(),
        denied_repositories=frozenset(),
        denied_keys=frozenset(),
        denied_paths=frozenset(),
        max_skills_per_seed=2,
    )

    result = discover(
        client,  # type: ignore[arg-type]
        policy,
        checked_at="2026-07-30T00:00:00Z",
    )

    assert client.content_requests == [
        ("alpha/skills", "a/SKILL.md"),
        ("alpha/skills", "m/SKILL.md"),
        ("beta/skills", "a/SKILL.md"),
        ("beta/skills", "b/SKILL.md"),
    ]
    assert len(result.candidates) == 4


def test_partial_discovery_preserves_cached_candidates_but_applies_denylist() -> None:
    candidates, _, _ = load_demo_fixture(FIXTURE)
    denied = candidates[0]
    policy = Policy(
        seeds=(),
        allowlist=(),
        denied_repositories=frozenset(),
        denied_keys=frozenset({denied.key}),
        denied_paths=frozenset(),
    )
    partial = DiscoveryResult(
        candidates=(candidates[-1],), errors=("seed failed",), search_degraded=True
    )

    result = preserve_cached_candidates(partial, candidates[:-1], policy)

    assert denied.key not in {candidate.key for candidate in result.candidates}
    assert len(result.candidates) == len(candidates) - 1
    assert result.errors == ("seed failed",)
    assert result.search_degraded is True
