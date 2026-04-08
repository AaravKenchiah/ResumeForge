"""Unit tests for GitHub project recommendation helpers."""

import os
import tempfile
import unittest

from backend.project_recommendations import (
    build_project_recommendation_payload,
    build_project_recommendation_user_message,
    generate_project_recommendations,
    load_project_prompt,
    normalize_project_recommendations,
    parse_project_recommendations,
)


SAMPLE_GITHUB_PROFILE = {
    "username": "janedev",
    "repos": [
        {
            "name": "resume-forge",
            "description": "AI resume tool",
            "language": "Python",
            "html_url": "https://github.com/janedev/resume-forge",
            "topics": ["fastapi", "gemini"],
            "readme_excerpt": "Builds ranked resume bullets from GitHub projects.",
        },
        {
            "name": "budget-board",
            "description": "Personal finance dashboard",
            "language": "TypeScript",
            "html_url": "https://github.com/janedev/budget-board",
            "topics": ["dashboard"],
            "readme_excerpt": "Visualizes spending and category trends.",
        },
    ],
}


class ProjectRecommendationTests(unittest.TestCase):
    """Verify Gemini prompt assembly and JSON parsing for project ranking."""

    def test_load_project_prompt_reads_prompt_file(self):
        with tempfile.NamedTemporaryFile("w+", delete=False) as handle:
            handle.write("Project prompt body")
            temp_path = handle.name

        try:
            self.assertEqual(load_project_prompt(temp_path), "Project prompt body")
        finally:
            os.unlink(temp_path)

    def test_build_project_recommendation_user_message_contains_inputs(self):
        message = build_project_recommendation_user_message(
            SAMPLE_GITHUB_PROFILE,
            "Need Python, FastAPI, and LLM experience.",
        )

        self.assertIn("## GitHub Project Data", message)
        self.assertIn("resume-forge", message)
        self.assertIn("Need Python, FastAPI, and LLM experience.", message)
        self.assertIn("Return valid JSON only.", message)

    def test_build_project_recommendation_payload_sets_json_response(self):
        payload = build_project_recommendation_payload("system prompt", "user prompt", max_tokens=321)

        self.assertEqual(payload["systemInstruction"]["parts"][0]["text"], "system prompt")
        self.assertEqual(payload["contents"][0]["parts"][0]["text"], "user prompt")
        self.assertEqual(payload["generationConfig"]["maxOutputTokens"], 321)
        self.assertEqual(payload["generationConfig"]["responseMimeType"], "application/json")

    def test_parse_project_recommendations_accepts_fenced_json(self):
        payload = parse_project_recommendations(
            """```json
            {"projects":[{"rank":1,"name":"resume-forge","relevanceSummary":"Great fit","bullets":["Built APIs"]}]}
            ```"""
        )

        self.assertEqual(payload["projects"][0]["name"], "resume-forge")

    def test_normalize_project_recommendations_enriches_repo_metadata(self):
        normalized = normalize_project_recommendations(
            {
                "projects": [
                    {
                        "rank": 2,
                        "name": "budget-board",
                        "relevanceSummary": "Useful dashboard experience.",
                        "bullets": ["Built charts", "Tracked spending trends"],
                    },
                    {
                        "rank": 1,
                        "name": "resume-forge",
                        "relevanceSummary": "Strong fit for AI tooling.",
                        "bullets": ["Built FastAPI workflow", "Connected GitHub and Gemini"],
                    },
                ]
            },
            SAMPLE_GITHUB_PROFILE,
        )

        self.assertEqual([project["name"] for project in normalized], ["resume-forge", "budget-board"])
        self.assertEqual(normalized[0]["language"], "Python")
        self.assertEqual(normalized[0]["url"], "https://github.com/janedev/resume-forge")

    def test_generate_project_recommendations_requires_api_key(self):
        original = os.environ.pop("GEMINI_API_KEY", None)
        try:
            with self.assertRaises(RuntimeError):
                generate_project_recommendations(
                    github_profile=SAMPLE_GITHUB_PROFILE,
                    job_description="Need Python",
                    json_poster=lambda *_: {},
                )
        finally:
            if original is not None:
                os.environ["GEMINI_API_KEY"] = original

    def test_generate_project_recommendations_returns_normalized_projects(self):
        def fake_json_poster(url, headers, payload):
            self.assertIn("x-goog-api-key", headers)
            self.assertEqual(payload["generationConfig"]["responseMimeType"], "application/json")
            return {
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "text": (
                                        '{"projects":[{"rank":1,"name":"resume-forge","relevanceSummary":"Best fit",'
                                        '"bullets":["Built FastAPI workflow","Connected GitHub and Gemini"]}]}'
                                    )
                                }
                            ]
                        }
                    }
                ]
            }

        projects = generate_project_recommendations(
            github_profile=SAMPLE_GITHUB_PROFILE,
            job_description="Need Python and FastAPI experience.",
            api_key="secret-key",
            json_poster=fake_json_poster,
        )

        self.assertEqual(len(projects), 1)
        self.assertEqual(projects[0]["name"], "resume-forge")
        self.assertEqual(projects[0]["language"], "Python")


if __name__ == "__main__":
    unittest.main()
