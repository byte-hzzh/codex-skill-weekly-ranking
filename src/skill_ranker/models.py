from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal, cast

SCHEMA_VERSION = "1.0"
ALGORITHM_VERSION = "weekly-v1"
TRIAL_ALGORITHM_VERSION = "trial-v1"

RankingStatus = Literal["official", "trial", "stale"]
RequestStatus = Literal["fresh", "cached"]


def _ranking_status(value: object) -> RankingStatus:
    if value not in {"official", "trial", "stale"}:
        raise ValueError(f"Invalid ranking status: {value}")
    return cast(RankingStatus, value)


def _request_status(value: object) -> RequestStatus:
    if value not in {"fresh", "cached"}:
        raise ValueError(f"Invalid request status: {value}")
    return cast(RequestStatus, value)


@dataclass(frozen=True)
class Candidate:
    key: str
    repository_id: int
    repository_node_id: str
    repository: str
    default_branch: str
    path: str
    name: str
    description: str
    source_url: str
    repository_url: str
    discovered_via: str
    checked_at: str
    eligible: bool = True
    exclusion_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> Candidate:
        return cls(
            key=str(value["key"]),
            repository_id=int(value["repository_id"]),
            repository_node_id=str(value.get("repository_node_id", "")),
            repository=str(value["repository"]),
            default_branch=str(value["default_branch"]),
            path=str(value["path"]),
            name=str(value["name"]),
            description=str(value["description"]),
            source_url=str(value["source_url"]),
            repository_url=str(value["repository_url"]),
            discovered_via=str(value["discovered_via"]),
            checked_at=str(value["checked_at"]),
            eligible=bool(value.get("eligible", True)),
            exclusion_reason=(
                str(value["exclusion_reason"]) if value.get("exclusion_reason") else None
            ),
        )


@dataclass(frozen=True)
class RepositorySnapshot:
    repository_id: int
    repository_node_id: str
    repository: str
    default_branch: str
    default_branch_sha: str
    stars: int
    forks: int
    archived: bool
    visibility: str
    request_status: RequestStatus

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> RepositorySnapshot:
        return cls(
            repository_id=int(value["repository_id"]),
            repository_node_id=str(value.get("repository_node_id", "")),
            repository=str(value["repository"]),
            default_branch=str(value["default_branch"]),
            default_branch_sha=str(value.get("default_branch_sha", "")),
            stars=int(value["stars"]),
            forks=int(value["forks"]),
            archived=bool(value.get("archived", False)),
            visibility=str(value.get("visibility", "public")),
            request_status=_request_status(value.get("request_status", "fresh")),
        )


@dataclass(frozen=True)
class Snapshot:
    schema_version: str
    scheduled_date: str
    timezone: str
    observed_at: str
    complete: bool
    repositories: tuple[RepositorySnapshot, ...]
    errors: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "repositories": [repository.to_dict() for repository in self.repositories],
            "errors": list(self.errors),
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> Snapshot:
        return cls(
            schema_version=str(value["schema_version"]),
            scheduled_date=str(value["scheduled_date"]),
            timezone=str(value["timezone"]),
            observed_at=str(value["observed_at"]),
            complete=bool(value["complete"]),
            repositories=tuple(
                RepositorySnapshot.from_dict(item) for item in value["repositories"]
            ),
            errors=tuple(str(item) for item in value.get("errors", [])),
        )


@dataclass(frozen=True)
class PathActivity:
    candidate_key: str
    repository_id: int
    path: str
    interval_start: str
    interval_end: str
    default_branch_sha: str
    commit_shas: tuple[str, ...]
    complete: bool
    method: str = "github-rest-path"

    @property
    def commits(self) -> int:
        return len(self.commit_shas)

    def to_dict(self) -> dict[str, Any]:
        return {**asdict(self), "commit_shas": list(self.commit_shas), "commits": self.commits}


@dataclass(frozen=True)
class Week:
    start_date: str
    end_date: str
    timezone: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class RankingEntry:
    rank: int
    candidate_key: str
    name: str
    description: str
    repository: str
    path: str
    source_url: str
    repository_url: str
    score: float
    metrics: dict[str, int | float]
    components: dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Ranking:
    schema_version: str
    algorithm_version: str
    ranking_status: RankingStatus
    week: Week
    generated_at: str
    source_observed_at: tuple[str, ...]
    complete: bool
    demo: bool
    entries: tuple[RankingEntry, ...]
    limitations: tuple[str, ...] = field(default_factory=tuple)
    stale_from_week: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "week": self.week.to_dict(),
            "source_observed_at": list(self.source_observed_at),
            "entries": [entry.to_dict() for entry in self.entries],
            "limitations": list(self.limitations),
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> Ranking:
        week = value["week"]
        return cls(
            schema_version=str(value["schema_version"]),
            algorithm_version=str(value["algorithm_version"]),
            ranking_status=_ranking_status(value["ranking_status"]),
            week=Week(
                start_date=str(week["start_date"]),
                end_date=str(week["end_date"]),
                timezone=str(week["timezone"]),
            ),
            generated_at=str(value["generated_at"]),
            source_observed_at=tuple(str(item) for item in value["source_observed_at"]),
            complete=bool(value["complete"]),
            demo=bool(value.get("demo", False)),
            entries=tuple(
                RankingEntry(
                    rank=int(item["rank"]),
                    candidate_key=str(item["candidate_key"]),
                    name=str(item["name"]),
                    description=str(item["description"]),
                    repository=str(item["repository"]),
                    path=str(item["path"]),
                    source_url=str(item["source_url"]),
                    repository_url=str(item["repository_url"]),
                    score=float(item["score"]),
                    metrics={
                        str(key): float(metric) if isinstance(metric, float) else int(metric)
                        for key, metric in item["metrics"].items()
                    },
                    components={
                        str(key): float(component) for key, component in item["components"].items()
                    },
                )
                for item in value["entries"]
            ),
            limitations=tuple(str(item) for item in value.get("limitations", [])),
            stale_from_week=(
                str(value["stale_from_week"]) if value.get("stale_from_week") else None
            ),
        )
