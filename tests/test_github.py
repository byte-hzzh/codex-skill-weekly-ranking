import io
import json
from base64 import b64encode
from email.message import Message
from urllib.error import HTTPError

import pytest

from skill_ranker.github import GitHubClient, GitHubError


class Response:
    def __init__(self, body: bytes, *, headers: dict[str, str] | None = None, status: int = 200):
        self.body = body
        self.status = status
        self.headers = Message()
        for key, value in (headers or {}).items():
            self.headers[key] = value

    def __enter__(self) -> "Response":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return self.body


def test_pagination_follows_link_header() -> None:
    responses = iter(
        [
            Response(
                b'[{"id": 1}]',
                headers={"Link": '<https://api.github.test/page2>; rel="next"'},
            ),
            Response(b'[{"id": 2}]'),
        ]
    )
    client = GitHubClient(opener=lambda *_args, **_kwargs: next(responses))
    assert [item["id"] for item in client.paginate("https://api.github.test/page1")] == [1, 2]


def test_rate_limit_retries_are_bounded() -> None:
    calls = 0
    sleeps: list[float] = []

    def opener(*_args: object, **_kwargs: object) -> Response:
        nonlocal calls
        calls += 1
        headers = Message()
        headers["Retry-After"] = "1"
        raise HTTPError("https://api.github.test", 429, "limited", headers, io.BytesIO(b"{}"))

    client = GitHubClient(opener=opener, sleeper=sleeps.append, max_retries=2)
    with pytest.raises(GitHubError, match="429"):
        client.get("https://api.github.test")
    assert calls == 3
    assert sleeps == [1.0, 1.0]


def test_code_search_requires_explicit_discovery_token() -> None:
    client = GitHubClient()
    with pytest.raises(GitHubError, match="DISCOVERY_GITHUB_TOKEN"):
        list(client.search_skill_files("filename:SKILL.md"))


def test_contents_api_accepts_wrapped_base64_and_enforces_size() -> None:
    content = b"---\nname: Test\ndescription: A valid test skill.\n---\nCodex\n"
    encoded = b64encode(content).decode("ascii")
    wrapped = f"{encoded[:12]}\n{encoded[12:]}\n"
    body = json.dumps({"encoding": "base64", "content": wrapped, "size": len(content)}).encode()
    client = GitHubClient(opener=lambda *_args, **_kwargs: Response(body))
    assert client.content_text("owner/repo", "SKILL.md", "main") == content.decode()

    oversized = GitHubClient(opener=lambda *_args, **_kwargs: Response(body))
    with pytest.raises(GitHubError, match="size limit"):
        oversized.content_text("owner/repo", "SKILL.md", "main", max_bytes=8)


def test_incomplete_code_search_is_rejected() -> None:
    body = json.dumps({"incomplete_results": True, "items": [{"path": "SKILL.md"}]}).encode()
    client = GitHubClient("token", opener=lambda *_args, **_kwargs: Response(body))
    with pytest.raises(GitHubError, match="incomplete"):
        list(client.search_skill_files("Codex filename:SKILL.md"))
