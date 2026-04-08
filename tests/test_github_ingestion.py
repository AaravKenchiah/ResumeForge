"""Unit tests for GitHub ingestion helpers."""

import base64
import os
import unittest
from urllib import error

from backend.github_ingestion import (
    build_github_headers,
    build_readme_excerpt,
    build_repo_summary,
    collect_github_profile,
    default_text_fetch,
    fetch_repository_readme,
    fetch_user_repositories,
    normalize_repo_payload,
)


class GitHubIngestionTests(unittest.TestCase):
    """Exercise the small, documented functions used for GitHub ingestion."""

    def test_build_github_headers_uses_explicit_token(self):
        headers = build_github_headers("secret-token")

        self.assertEqual(headers["Authorization"], "Bearer secret-token")
        self.assertEqual(headers["User-Agent"], "ResumeForge")

    def test_build_github_headers_falls_back_to_environment_token(self):
        original = os.environ.get("GITHUB_TOKEN")
        os.environ["GITHUB_TOKEN"] = "env-token"
        try:
            headers = build_github_headers()
        finally:
            if original is None:
                os.environ.pop("GITHUB_TOKEN", None)
            else:
                os.environ["GITHUB_TOKEN"] = original

        self.assertEqual(headers["Authorization"], "Bearer env-token")

    def test_normalize_repo_payload_maps_fields_and_defaults(self):
        repo = normalize_repo_payload(
            {
                "name": "resume-forge",
                "description": None,
                "language": None,
                "topics": ["fastapi", "resume"],
                "html_url": "https://github.com/test/resume-forge",
                "updated_at": "2026-04-08T00:00:00Z",
                "stargazers_count": 4,
                "fork": False,
            }
        )

        self.assertEqual(repo.name, "resume-forge")
        self.assertEqual(repo.description, "")
        self.assertEqual(repo.language, "Unknown")
        self.assertEqual(repo.topics, ["fastapi", "resume"])
        self.assertEqual(repo.stargazers_count, 4)
        self.assertFalse(repo.fork)

    def test_build_readme_excerpt_normalizes_whitespace_and_truncates(self):
        excerpt = build_readme_excerpt("Line one.\n\nLine two.\nLine three.", max_chars=18)

        self.assertEqual(excerpt, "Line one. Line...")

    def test_build_repo_summary_includes_available_project_signals(self):
        repo = normalize_repo_payload(
            {
                "name": "resume-forge",
                "description": "AI resume tool",
                "language": "Python",
                "topics": ["fastapi", "llm"],
                "html_url": "https://github.com/test/resume-forge",
                "updated_at": "2026-04-08T00:00:00Z",
                "stargazers_count": 8,
                "fork": False,
            }
        )
        repo.readme_excerpt = "Build resumes from GitHub projects."

        summary = build_repo_summary(repo, max_chars=500)

        self.assertIn("resume-forge", summary)
        self.assertIn("Python", summary)
        self.assertIn("AI resume tool", summary)
        self.assertIn("Topics: fastapi, llm", summary)
        self.assertIn("README: Build resumes from GitHub projects.", summary)

    def test_fetch_user_repositories_uses_fetcher_and_returns_normalized_models(self):
        captured = {}

        def fake_json_fetcher(url, headers):
            captured["url"] = url
            captured["headers"] = headers
            return [
                {
                    "name": "resume-forge",
                    "description": "AI resume tool",
                    "language": "Python",
                    "topics": [],
                    "html_url": "https://github.com/test/resume-forge",
                    "updated_at": "2026-04-08T00:00:00Z",
                    "stargazers_count": 1,
                    "fork": False,
                }
            ]

        repos = fetch_user_repositories("janedev", repo_limit=3, json_fetcher=fake_json_fetcher)

        self.assertEqual(len(repos), 1)
        self.assertEqual(repos[0].name, "resume-forge")
        self.assertIn("/users/janedev/repos", captured["url"])
        self.assertIn("per_page=3", captured["url"])
        self.assertEqual(captured["headers"]["User-Agent"], "ResumeForge")

    def test_fetch_repository_readme_returns_trimmed_excerpt(self):
        def fake_text_fetcher(url, headers):
            self.assertIn("/repos/janedev/resume-forge/readme", url)
            self.assertEqual(headers["User-Agent"], "ResumeForge")
            return "README\n\nwith lots    of spacing"

        excerpt = fetch_repository_readme(
            "janedev",
            "resume-forge",
            text_fetcher=fake_text_fetcher,
        )

        self.assertEqual(excerpt, "README with lots of spacing")

    def test_fetch_repository_readme_returns_empty_on_rate_limit(self):
        def fake_text_fetcher(url, headers):
            raise error.HTTPError(url=url, code=403, msg="Forbidden", hdrs=None, fp=None)

        excerpt = fetch_repository_readme(
            "janedev",
            "resume-forge",
            text_fetcher=fake_text_fetcher,
        )

        self.assertEqual(excerpt, "")

    def test_collect_github_profile_combines_repos_and_summary(self):
        def fake_json_fetcher(url, headers):
            return [
                {
                    "name": "resume-forge",
                    "description": "AI resume tool",
                    "language": "Python",
                    "topics": ["fastapi"],
                    "html_url": "https://github.com/test/resume-forge",
                    "updated_at": "2026-04-08T00:00:00Z",
                    "stargazers_count": 3,
                    "fork": False,
                },
                {
                    "name": "forked-tool",
                    "description": "Forked repo",
                    "language": "TypeScript",
                    "topics": [],
                    "html_url": "https://github.com/test/forked-tool",
                    "updated_at": "2026-04-08T00:00:00Z",
                    "stargazers_count": 0,
                    "fork": True,
                },
            ]

        requested_readmes = []

        def fake_text_fetcher(url, headers):
            requested_readmes.append(url)
            return "Helpful README content"

        profile = collect_github_profile(
            username="janedev",
            repo_limit=2,
            include_readmes=True,
            json_fetcher=fake_json_fetcher,
            text_fetcher=fake_text_fetcher,
        )

        self.assertEqual(profile["username"], "janedev")
        self.assertEqual(profile["repoCount"], 2)
        self.assertEqual(len(profile["repos"]), 2)
        self.assertEqual(len(requested_readmes), 1)
        self.assertIn("- resume-forge | Python | AI resume tool", profile["summary"])
        self.assertIn("Helpful README content", profile["summary"])

    def test_default_text_fetch_decodes_base64_content(self):
        encoded = base64.b64encode(b"Hello from README").decode("utf-8")

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self):
                return f'{{"encoding":"base64","content":"{encoded}"}}'.encode("utf-8")

        from unittest.mock import patch

        with patch("backend.github_ingestion.request.urlopen", return_value=FakeResponse()):
            result = default_text_fetch("https://example.com", {})

        self.assertEqual(result, "Hello from README")

    def test_default_text_fetch_returns_none_for_missing_readme(self):
        from unittest.mock import patch

        with patch(
            "backend.github_ingestion.request.urlopen",
            side_effect=error.HTTPError(
                url="https://example.com",
                code=404,
                msg="Not Found",
                hdrs=None,
                fp=None,
            ),
        ):
            result = default_text_fetch("https://example.com", {})

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
