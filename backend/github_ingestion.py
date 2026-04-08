"""Utilities for collecting and summarizing public GitHub profile data."""

from __future__ import annotations

import base64
import json
import os
from dataclasses import asdict, dataclass
from typing import Callable
from urllib import error, parse, request


GITHUB_API_BASE = "https://api.github.com"
DEFAULT_REPO_LIMIT = 5
README_PREVIEW_LIMIT = 600
SUMMARY_LIMIT = 280


JsonFetcher = Callable[[str, dict[str, str]], object]
TextFetcher = Callable[[str, dict[str, str]], str | None]


@dataclass(slots=True)
class GitHubRepo:
    """Normalized repository metadata used by the app prompt pipeline."""

    name: str
    description: str
    language: str
    topics: list[str]
    html_url: str
    updated_at: str
    stargazers_count: int
    fork: bool
    readme_excerpt: str = ""


def build_github_headers(token: str | None = None) -> dict[str, str]:
    """Build standard GitHub API headers, including optional auth."""
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "ResumeForge",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    api_token = token or os.getenv("GITHUB_TOKEN")
    if api_token and api_token.strip().lower() not in {"optional", "your_github_token_here"}:
        headers["Authorization"] = f"Bearer {api_token}"

    return headers


def default_json_fetch(url: str, headers: dict[str, str]) -> object:
    """Fetch and decode JSON from an HTTP endpoint."""
    req = request.Request(url, headers=headers)
    with request.urlopen(req, timeout=15) as response:
        return json.load(response)


def default_text_fetch(url: str, headers: dict[str, str]) -> str | None:
    """Fetch plain text or base64-decoded content from an HTTP endpoint."""
    req = request.Request(url, headers=headers)
    try:
        with request.urlopen(req, timeout=15) as response:
            payload = json.load(response)
    except error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise

    if isinstance(payload, dict) and payload.get("encoding") == "base64":
        content = payload.get("content", "")
        decoded = base64.b64decode(content).decode("utf-8", errors="ignore")
        return decoded

    return None


def normalize_repo_payload(repo_payload: dict) -> GitHubRepo:
    """Convert a GitHub REST API repository payload into a stable app model."""
    return GitHubRepo(
        name=repo_payload.get("name", ""),
        description=repo_payload.get("description") or "",
        language=repo_payload.get("language") or "Unknown",
        topics=repo_payload.get("topics") or [],
        html_url=repo_payload.get("html_url", ""),
        updated_at=repo_payload.get("updated_at", ""),
        stargazers_count=int(repo_payload.get("stargazers_count") or 0),
        fork=bool(repo_payload.get("fork", False)),
    )


def build_readme_excerpt(readme_text: str | None, max_chars: int = README_PREVIEW_LIMIT) -> str:
    """Trim README content into a single prompt-friendly excerpt."""
    if not readme_text:
        return ""

    normalized = " ".join(readme_text.split())
    if len(normalized) <= max_chars:
        return normalized

    return normalized[: max_chars - 3].rstrip() + "..."


def build_repo_summary(repo: GitHubRepo, max_chars: int = SUMMARY_LIMIT) -> str:
    """Create a concise single-line project summary for prompt assembly."""
    parts = [repo.name]

    if repo.language and repo.language != "Unknown":
        parts.append(repo.language)

    if repo.description:
        parts.append(repo.description)

    if repo.topics:
        parts.append(f"Topics: {', '.join(repo.topics[:4])}")

    if repo.readme_excerpt:
        parts.append(f"README: {repo.readme_excerpt}")

    summary = " | ".join(parts)
    if len(summary) <= max_chars:
        return summary

    return summary[: max_chars - 3].rstrip() + "..."


def fetch_user_repositories(
    username: str,
    repo_limit: int = DEFAULT_REPO_LIMIT,
    json_fetcher: JsonFetcher = default_json_fetch,
    token: str | None = None,
) -> list[GitHubRepo]:
    """Fetch and normalize a user's most recently updated public repositories."""
    quoted_username = parse.quote(username.strip())
    params = parse.urlencode({"sort": "updated", "per_page": repo_limit})
    url = f"{GITHUB_API_BASE}/users/{quoted_username}/repos?{params}"
    payload = json_fetcher(url, build_github_headers(token))

    if not isinstance(payload, list):
        raise ValueError("Unexpected GitHub repository response shape.")

    return [normalize_repo_payload(repo) for repo in payload]


def fetch_repository_readme(
    username: str,
    repo_name: str,
    text_fetcher: TextFetcher = default_text_fetch,
    token: str | None = None,
) -> str:
    """Fetch a repository README excerpt, returning an empty string when missing."""
    quoted_username = parse.quote(username.strip())
    quoted_repo = parse.quote(repo_name.strip())
    url = f"{GITHUB_API_BASE}/repos/{quoted_username}/{quoted_repo}/readme"
    try:
        readme_text = text_fetcher(url, build_github_headers(token))
    except error.HTTPError as exc:
        if exc.code in {403, 429}:
            return ""
        raise
    return build_readme_excerpt(readme_text)


def collect_github_profile(
    username: str,
    repo_limit: int = DEFAULT_REPO_LIMIT,
    include_readmes: bool = True,
    json_fetcher: JsonFetcher = default_json_fetch,
    text_fetcher: TextFetcher = default_text_fetch,
    token: str | None = None,
) -> dict:
    """Collect repositories and prompt-ready summaries for a public GitHub user."""
    repositories = fetch_user_repositories(
        username=username,
        repo_limit=repo_limit,
        json_fetcher=json_fetcher,
        token=token,
    )

    hydrated_repositories: list[GitHubRepo] = []
    for repo in repositories:
        readme_excerpt = ""
        if include_readmes and not repo.fork:
            readme_excerpt = fetch_repository_readme(
                username=username,
                repo_name=repo.name,
                text_fetcher=text_fetcher,
                token=token,
            )

        hydrated_repositories.append(
            GitHubRepo(
                name=repo.name,
                description=repo.description,
                language=repo.language,
                topics=repo.topics,
                html_url=repo.html_url,
                updated_at=repo.updated_at,
                stargazers_count=repo.stargazers_count,
                fork=repo.fork,
                readme_excerpt=readme_excerpt,
            )
        )

    summaries = [build_repo_summary(repo) for repo in hydrated_repositories]
    return {
        "username": username,
        "repoCount": len(hydrated_repositories),
        "repos": [asdict(repo) for repo in hydrated_repositories],
        "summary": "\n".join(f"- {summary}" for summary in summaries),
    }
