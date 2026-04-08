"""Unit tests for Gemini prompt assembly and client helpers."""

import os
import tempfile
import unittest

from backend.claude_tailor import (
    DEFAULT_MODEL,
    build_gemini_headers,
    build_gemini_payload,
    build_gemini_url,
    build_tailor_user_message,
    extract_text_from_gemini_response,
    format_structure_for_prompt,
    generate_tailored_resume,
    load_system_prompt,
)


class ClaudeTailorTests(unittest.TestCase):
    """Verify deterministic prompt construction and Gemini response handling."""

    def test_load_system_prompt_reads_prompt_file(self):
        with tempfile.NamedTemporaryFile("w+", delete=False) as handle:
            handle.write("Prompt body")
            temp_path = handle.name

        try:
            self.assertEqual(load_system_prompt(temp_path), "Prompt body")
        finally:
            os.unlink(temp_path)

    def test_build_gemini_headers_sets_required_fields(self):
        headers = build_gemini_headers("secret-key")

        self.assertEqual(headers["x-goog-api-key"], "secret-key")
        self.assertEqual(headers["Content-Type"], "application/json")

    def test_format_structure_for_prompt_returns_json_string(self):
        rendered = format_structure_for_prompt({"sectionOrder": ["Summary", "Experience"]})

        self.assertIn('"sectionOrder"', rendered)
        self.assertIn('"Summary"', rendered)

    def test_build_tailor_user_message_contains_all_inputs(self):
        message = build_tailor_user_message(
            resume_text="SUMMARY\nBuilt APIs",
            resume_structure={
                "sectionOrder": ["SUMMARY"],
                "bulletStyle": "●",
                "dateFormat": "month-year",
                "skillsFormat": "bulleted",
                "lineCount": 12,
            },
            github_summary="- repo-a | Python | APIs",
            job_description="Need a backend engineer",
        )

        self.assertIn("## Original Resume", message)
        self.assertIn("Built APIs", message)
        self.assertIn("repo-a", message)
        self.assertIn("Need a backend engineer", message)
        self.assertIn("## Formatting Signals To Preserve", message)
        self.assertIn("Bullet style: ●", message)
        self.assertIn("## Output Contract", message)

    def test_build_gemini_url_matches_generate_content_endpoint(self):
        self.assertEqual(
            build_gemini_url("gemini-2.5-pro"),
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent",
        )

    def test_build_gemini_payload_matches_generate_content_shape(self):
        payload = build_gemini_payload("system prompt", "user prompt", model="gemini-test", max_tokens=123)

        self.assertEqual(payload["systemInstruction"]["parts"][0]["text"], "system prompt")
        self.assertEqual(payload["contents"][0]["parts"][0]["text"], "user prompt")
        self.assertEqual(payload["generationConfig"]["maxOutputTokens"], 123)

    def test_extract_text_from_gemini_response_combines_text_parts(self):
        result = extract_text_from_gemini_response(
            {
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {"text": "Line one"},
                                {"text": "Line two"},
                            ]
                        }
                    }
                ]
            }
        )

        self.assertEqual(result, "Line one\nLine two")

    def test_extract_text_from_gemini_response_rejects_missing_text(self):
        with self.assertRaises(ValueError):
            extract_text_from_gemini_response({"candidates": [{"content": {"parts": [{}]}}]})

    def test_generate_tailored_resume_requires_api_key(self):
        original = os.environ.pop("GEMINI_API_KEY", None)
        try:
            with self.assertRaises(RuntimeError):
                generate_tailored_resume(
                    resume_text="resume",
                    resume_structure={},
                    github_summary="",
                    job_description="job",
                    json_poster=lambda *_: {},
                )
        finally:
            if original is not None:
                os.environ["GEMINI_API_KEY"] = original

    def test_generate_tailored_resume_builds_request_and_returns_text(self):
        captured = {}

        def fake_json_poster(url, headers, payload):
            captured["url"] = url
            captured["headers"] = headers
            captured["payload"] = payload
            return {
                "candidates": [
                    {
                        "content": {
                            "parts": [{"text": "Tailored resume output"}]
                        }
                    }
                ]
            }

        with tempfile.NamedTemporaryFile("w+", delete=False) as handle:
            handle.write("System prompt text")
            temp_path = handle.name

        try:
            result = generate_tailored_resume(
                resume_text="SUMMARY\nBuilt APIs",
                resume_structure={"sectionOrder": ["SUMMARY"]},
                github_summary="- repo-a | Python | APIs",
                job_description="Need a backend engineer",
                api_key="secret-key",
                prompt_path=temp_path,
                json_poster=fake_json_poster,
            )
        finally:
            os.unlink(temp_path)

        self.assertEqual(result, "Tailored resume output")
        self.assertEqual(captured["url"], build_gemini_url(DEFAULT_MODEL))
        self.assertEqual(captured["headers"]["x-goog-api-key"], "secret-key")
        self.assertEqual(captured["payload"]["systemInstruction"]["parts"][0]["text"], "System prompt text")
        self.assertIn("Need a backend engineer", captured["payload"]["contents"][0]["parts"][0]["text"])
