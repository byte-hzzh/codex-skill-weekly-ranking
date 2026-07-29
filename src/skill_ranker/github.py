from __future__ import annotations

import json
import time
from base64 import b64decode
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from .io import atomic_write_json, read_json

API_ROOT = "https://api.github.com"
API_VERSION = "2022-11-28"


class GitHubError(RuntimeError):
    def __init__(self, message: str, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


@dataclass(frozen=True)
class GitHubResponse:
    data: Any
    headers: dict[str, str]
    status: int
    cached: bool


def _next_link(value: str | None) -> str | None:
    if not value:
        return None
    for part in value.split(","):
        sections = [section.strip() for section in part.split(";")]
        if len(sections) > 1 and sections[1] == 'rel="next"':
            return sections[0].strip("<>")
    return None


class GitHubClient:
    """Small serialized GitHub REST client with bounded retries and ETag caching."""

    def __init__(
        self,
        token: str | None = None,
        *,
        cache_dir: Path | None = None,
        timeout: float = 20,
        max_retries: int = 3,
        sleeper: Callable[[float], None] = time.sleep,
        opener: Callable[..., Any] = urlopen,
    ) -> None:
        self._token = token
        self._cache_dir = cache_dir
        self._timeout = timeout
        self._max_retries = max_retries
        self._sleep = sleeper
        self._opener = opener

    @property
    def authenticated(self) -> bool:
        return bool(self._token)

    def _cache_path(self, url: str) -> Path | None:
        if self._cache_dir is None:
            return None
        return self._cache_dir / f"{sha256(url.encode()).hexdigest()}.json"

    def get(self, url: str, *, use_cache: bool = True) -> GitHubResponse:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "codex-skill-weekly-ranking/0.1",
            "X-GitHub-Api-Version": API_VERSION,
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"

        cache_path = self._cache_path(url) if use_cache else None
        cached_payload: dict[str, Any] | None = None
        if cache_path and cache_path.exists():
            loaded = read_json(cache_path)
            if isinstance(loaded, dict):
                cached_payload = loaded
                etag = loaded.get("etag")
                if isinstance(etag, str):
                    headers["If-None-Match"] = etag

        for attempt in range(self._max_retries + 1):
            request = Request(url, headers=headers)
            try:
                with self._opener(request, timeout=self._timeout) as response:
                    raw = response.read()
                    response_headers = {
                        key.casefold(): value for key, value in response.headers.items()
                    }
                    data = json.loads(raw.decode("utf-8")) if raw else None
                    if cache_path:
                        atomic_write_json(
                            cache_path,
                            {
                                "etag": response_headers.get("etag"),
                                "data": data,
                                "saved_at": int(time.time()),
                            },
                        )
                    return GitHubResponse(data, response_headers, int(response.status), False)
            except HTTPError as error:
                error_headers = {key.casefold(): value for key, value in error.headers.items()}
                if error.code == 304 and cached_payload is not None:
                    return GitHubResponse(cached_payload["data"], error_headers, 304, True)
                retryable = error.code in {429, 500, 502, 503, 504} or (
                    error.code == 403
                    and (
                        "retry-after" in error_headers
                        or error_headers.get("x-ratelimit-remaining") == "0"
                    )
                )
                if retryable and attempt < self._max_retries:
                    self._sleep(self._retry_delay(error_headers, attempt))
                    continue
                detail = error.read(512).decode("utf-8", errors="replace")
                raise GitHubError(f"GitHub HTTP {error.code}: {detail}", error.code) from error
            except URLError as error:
                if attempt < self._max_retries:
                    self._sleep(min(2**attempt, 8))
                    continue
                raise GitHubError(f"GitHub connection failed: {error.reason}") from error
        raise AssertionError("retry loop must return or raise")

    def _retry_delay(self, headers: dict[str, str], attempt: int) -> float:
        retry_after = headers.get("retry-after")
        if retry_after and retry_after.isdigit():
            return min(float(retry_after), 60)
        reset = headers.get("x-ratelimit-reset")
        if reset and reset.isdigit():
            return min(max(float(reset) - time.time(), 1), 60)
        return min(float(2**attempt), 8)

    def paginate(self, url: str, *, item_key: str | None = None) -> Iterator[dict[str, Any]]:
        next_url: str | None = url
        while next_url:
            response = self.get(next_url)
            payload = response.data
            values = (
                payload.get(item_key, []) if item_key and isinstance(payload, dict) else payload
            )
            if not isinstance(values, list):
                raise GitHubError(f"Expected a list from {next_url}")
            for item in values:
                if isinstance(item, dict):
                    yield item
            next_url = _next_link(response.headers.get("link"))

    def repository(self, full_name: str) -> dict[str, Any]:
        return self._mapping(f"{API_ROOT}/repos/{_repo_slug(full_name)}")

    def tree(self, full_name: str, ref: str) -> list[dict[str, Any]]:
        payload = self._mapping(
            f"{API_ROOT}/repos/{_repo_slug(full_name)}/git/trees/{quote(ref, safe='')}?recursive=1"
        )
        if payload.get("truncated"):
            raise GitHubError(f"Recursive tree for {full_name} was truncated")
        tree = payload.get("tree")
        if not isinstance(tree, list):
            raise GitHubError(f"Invalid tree response for {full_name}")
        return [item for item in tree if isinstance(item, dict)]

    def content_text(
        self, full_name: str, path: str, ref: str, *, max_bytes: int | None = None
    ) -> str:
        query = urlencode({"ref": ref})
        payload = self._mapping(
            f"{API_ROOT}/repos/{_repo_slug(full_name)}/contents/{_path(path)}?{query}"
        )
        if payload.get("encoding") != "base64" or not isinstance(payload.get("content"), str):
            raise GitHubError(f"Unsupported content response for {full_name}/{path}")
        reported_size = payload.get("size")
        if max_bytes is not None and isinstance(reported_size, int) and reported_size > max_bytes:
            raise GitHubError(f"Content exceeds the size limit: {full_name}/{path}")
        try:
            # GitHub wraps base64 content with newlines. Remove ASCII whitespace before
            # strict decoding so valid Contents API responses are accepted without
            # relaxing alphabet validation.
            encoded = "".join(payload["content"].split())
            decoded = b64decode(encoded, validate=True)
            if max_bytes is not None and len(decoded) > max_bytes:
                raise GitHubError(f"Content exceeds the size limit: {full_name}/{path}")
            return decoded.decode("utf-8")
        except (ValueError, UnicodeDecodeError) as error:
            raise GitHubError(f"Content is not valid base64 UTF-8: {full_name}/{path}") from error

    def search_skill_files(self, query: str) -> Iterator[dict[str, Any]]:
        if not self.authenticated:
            raise GitHubError("Global code search requires DISCOVERY_GITHUB_TOKEN")
        url = f"{API_ROOT}/search/code?{urlencode({'q': query, 'per_page': 100, 'page': 1})}"
        payload = self.get(url).data
        if not isinstance(payload, dict):
            raise GitHubError(f"Expected an object from {url}")
        if payload.get("incomplete_results") is True:
            raise GitHubError("GitHub code search returned incomplete results")
        items = payload.get("items")
        if not isinstance(items, list):
            raise GitHubError(f"Expected search items from {url}")
        for item in items[:100]:
            if isinstance(item, dict):
                yield item

    def commits(
        self, full_name: str, path: str, since: str, until: str
    ) -> Iterator[dict[str, Any]]:
        query = urlencode({"path": path, "since": since, "until": until, "per_page": 100})
        url = f"{API_ROOT}/repos/{_repo_slug(full_name)}/commits?{query}"
        yield from self.paginate(url)

    def branch(self, full_name: str, branch: str) -> dict[str, Any]:
        return self._mapping(
            f"{API_ROOT}/repos/{_repo_slug(full_name)}/branches/{quote(branch, safe='')}"
        )

    def _mapping(self, url: str) -> dict[str, Any]:
        value = self.get(url).data
        if not isinstance(value, dict):
            raise GitHubError(f"Expected an object from {url}")
        return value


def _repo_slug(value: str) -> str:
    parts = value.split("/")
    if len(parts) != 2 or not all(parts):
        raise ValueError(f"Invalid GitHub repository: {value}")
    return "/".join(quote(part, safe=".-_") for part in parts)


def _path(value: str) -> str:
    parts = value.replace("\\", "/").split("/")
    if not parts or any(part in {"", ".", ".."} for part in parts):
        raise ValueError(f"Invalid repository path: {value}")
    return "/".join(quote(part, safe=".-_") for part in parts)
