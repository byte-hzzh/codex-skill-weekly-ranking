from pathlib import Path

from skill_ranker.config import Policy
from skill_ranker.discovery import DiscoveryResult, preserve_cached_candidates
from skill_ranker.fixtures import load_demo_fixture

FIXTURE = Path(__file__).parent / "fixtures" / "demo.json"


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
