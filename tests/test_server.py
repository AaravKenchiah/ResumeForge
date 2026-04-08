"""API tests for the ResumeForge backend server."""

import unittest
from unittest.mock import patch
from urllib import error

from fastapi.testclient import TestClient

from backend.server import app


class ServerTests(unittest.TestCase):
    """Verify the FastAPI routes that expose GitHub ingestion."""

    def setUp(self):
        self.client = TestClient(app)

    def test_health_check_returns_ok(self):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_preview_github_profile_returns_profile_payload(self):
        with patch("backend.server.collect_github_profile") as mock_collect:
            mock_collect.return_value = {
                "username": "janedev",
                "repoCount": 1,
                "repos": [{"name": "resume-forge"}],
                "summary": "- resume-forge | Python | AI resume tool",
            }

            response = self.client.get("/github/janedev")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["username"], "janedev")
        mock_collect.assert_called_once_with(username="janedev", include_readmes=False)

    def test_preview_github_profile_translates_not_found(self):
        with patch(
            "backend.server.collect_github_profile",
            side_effect=error.HTTPError(
                url="https://api.github.com/users/missing/repos",
                code=404,
                msg="Not Found",
                hdrs=None,
                fp=None,
            ),
        ):
            response = self.client.get("/github/missing")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "GitHub user not found.")

    def test_preview_github_profile_explains_rate_limit_fix(self):
        with patch(
            "backend.server.collect_github_profile",
            side_effect=error.HTTPError(
                url="https://api.github.com/users/missing/repos",
                code=403,
                msg="Forbidden",
                hdrs=None,
                fp=None,
            ),
        ):
            response = self.client.get("/github/missing")

        self.assertEqual(response.status_code, 403)
        self.assertIn("GITHUB_TOKEN", response.json()["detail"])

    def test_parse_resume_accepts_pasted_text(self):
        response = self.client.post(
            "/parse-resume",
            json={
                "resumeText": "EXPERIENCE\nBuilt APIs\nSKILLS\nPython, FastAPI",
                "fileName": "",
                "fileContentBase64": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["source"], "text")
        self.assertIn("EXPERIENCE", response.json()["structure"]["sectionOrder"])

    def test_parse_resume_accepts_uploaded_text_file(self):
        response = self.client.post(
            "/parse-resume",
            json={
                "resumeText": "",
                "fileName": "resume.txt",
                "fileContentBase64": "SGVsbG8gUmVzdW1l",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["source"], "file")
        self.assertEqual(response.json()["content"], "Hello Resume")

    def test_parse_resume_returns_bad_request_for_missing_input(self):
        response = self.client.post(
            "/parse-resume",
            json={
                "resumeText": "",
                "fileName": "",
                "fileContentBase64": "",
            },
        )

        self.assertEqual(response.status_code, 400)

    def test_parse_resume_translates_pdf_dependency_error(self):
        with patch(
            "backend.server.parse_resume_source",
            side_effect=RuntimeError("PDF parsing requires the optional 'pypdf' package."),
        ):
            response = self.client.post(
                "/parse-resume",
                json={
                    "resumeText": "",
                    "fileName": "resume.pdf",
                    "fileContentBase64": "JVBERi0xLjQ=",
                },
            )

        self.assertEqual(response.status_code, 501)
        self.assertIn("pypdf", response.json()["detail"])

    def test_parse_job_description_accepts_pasted_text(self):
        response = self.client.post(
            "/parse-job-description",
            json={
                "jobDescriptionText": "Apply Now\nBackend Engineer\nBuild APIs",
                "jobDescriptionUrl": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["source"], "text")
        self.assertEqual(response.json()["content"], "Backend Engineer\nBuild APIs")

    def test_parse_job_description_accepts_url_input(self):
        with patch("backend.server.parse_job_description_source") as mock_parse:
            mock_parse.return_value = {
                "source": "url",
                "url": "https://company.com/jobs/123",
                "content": "Senior Backend Engineer\nBuild APIs",
                "lineCount": 2,
            }

            response = self.client.post(
                "/parse-job-description",
                json={
                    "jobDescriptionText": "",
                    "jobDescriptionUrl": "https://company.com/jobs/123",
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["source"], "url")
        mock_parse.assert_called_once()

    def test_parse_job_description_returns_bad_request_for_missing_input(self):
        response = self.client.post(
            "/parse-job-description",
            json={
                "jobDescriptionText": "",
                "jobDescriptionUrl": "",
            },
        )

        self.assertEqual(response.status_code, 400)

    def test_parse_job_description_translates_fetch_errors(self):
        with patch(
            "backend.server.parse_job_description_source",
            side_effect=error.HTTPError(
                url="https://company.com/jobs/123",
                code=404,
                msg="Not Found",
                hdrs=None,
                fp=None,
            ),
        ):
            response = self.client.post(
                "/parse-job-description",
                json={
                    "jobDescriptionText": "",
                    "jobDescriptionUrl": "https://company.com/jobs/123",
                },
            )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "Job posting URL not found.")

    def test_tailor_resume_includes_github_summary_when_available(self):
        with patch("backend.server.collect_github_profile") as mock_collect, patch(
            "backend.server.generate_tailored_resume"
        ) as mock_generate:
            mock_collect.return_value = {
                "summary": "- resume-forge | Python | AI resume tool",
            }
            mock_generate.return_value = "Tailored output"

            response = self.client.post(
                "/tailor",
                json={
                    "githubUsername": "janedev",
                    "resumeText": "Software engineer with backend experience.",
                    "jobDescription": "Looking for a Python engineer.",
                },
            )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["tailoredResume"], "Tailored output")
        self.assertIn("- resume-forge | Python | AI resume tool", body["githubSummary"])
        self.assertIn("Software engineer with backend experience.", body["resumeStructure"]["sections"][0]["lines"][0])
        mock_generate.assert_called_once()

    def test_tailor_resume_handles_github_failures_gracefully(self):
        with patch(
            "backend.server.collect_github_profile",
            side_effect=error.HTTPError(
                url="https://api.github.com/users/janedev/repos",
                code=403,
                msg="Forbidden",
                hdrs=None,
                fp=None,
            ),
        ), patch("backend.server.generate_tailored_resume") as mock_generate:
            mock_generate.return_value = "Tailored output"
            response = self.client.post(
                "/tailor",
                json={
                    "githubUsername": "janedev",
                    "resumeText": "Software engineer with backend experience.",
                    "jobDescription": "Looking for a Python engineer.",
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["githubSummary"], "GitHub summary unavailable.")

    def test_tailor_resume_returns_server_error_for_missing_api_key(self):
        with patch(
            "backend.server.generate_tailored_resume",
            side_effect=RuntimeError("Missing GEMINI_API_KEY for Gemini API integration."),
        ):
            response = self.client.post(
                "/tailor",
                json={
                    "githubUsername": "",
                    "resumeText": "Software engineer with backend experience.",
                    "jobDescription": "Looking for a Python engineer.",
                },
            )

        self.assertEqual(response.status_code, 500)
        self.assertIn("GEMINI_API_KEY", response.json()["detail"])

    def test_tailor_resume_translates_gemini_http_errors(self):
        with patch(
            "backend.server.generate_tailored_resume",
            side_effect=error.HTTPError(
                url="https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent",
                code=401,
                msg="Unauthorized",
                hdrs=None,
                fp=None,
            ),
        ):
            response = self.client.post(
                "/tailor",
                json={
                    "githubUsername": "",
                    "resumeText": "Software engineer with backend experience.",
                    "jobDescription": "Looking for a Python engineer.",
                },
            )

        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json()["detail"], "Invalid Gemini API key.")

    def test_tailor_resume_includes_gap_analysis(self):
        with patch("backend.server.generate_tailored_resume", return_value="Tailored output"), patch(
            "backend.server.analyze_skill_gaps",
            return_value={"matchedSkills": ["python"], "missingSkills": ["aws"], "matchCount": 1, "missingCount": 1},
        ):
            response = self.client.post(
                "/tailor",
                json={
                    "githubUsername": "",
                    "resumeText": "Python engineer",
                    "jobDescription": "Need Python and AWS experience",
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["gapAnalysis"]["missingSkills"], ["aws"])

    def test_recommend_projects_returns_ranked_project_payload(self):
        with patch("backend.server.collect_github_profile") as mock_collect, patch(
            "backend.server.generate_project_recommendations"
        ) as mock_recommend:
            mock_collect.return_value = {
                "username": "janedev",
                "summary": "- resume-forge | Python | AI resume tool",
                "repos": [{"name": "resume-forge"}],
            }
            mock_recommend.return_value = [
                {
                    "rank": 1,
                    "name": "resume-forge",
                    "relevanceSummary": "Strong fit for AI workflow roles.",
                    "bullets": ["Built FastAPI workflow", "Connected GitHub and Gemini"],
                }
            ]

            response = self.client.post(
                "/recommend-projects",
                json={
                    "githubUsername": "janedev",
                    "jobDescription": "Need Python and AI experience.",
                },
            )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["githubUsername"], "janedev")
        self.assertEqual(body["rankedProjects"][0]["name"], "resume-forge")
        mock_collect.assert_called_once_with(username="janedev")
        mock_recommend.assert_called_once()

    def test_recommend_projects_translates_missing_api_key(self):
        with patch(
            "backend.server.generate_project_recommendations",
            side_effect=RuntimeError("Missing GEMINI_API_KEY for Gemini API integration."),
        ), patch(
            "backend.server.collect_github_profile",
            return_value={"username": "janedev", "summary": "", "repos": []},
        ):
            response = self.client.post(
                "/recommend-projects",
                json={
                    "githubUsername": "janedev",
                    "jobDescription": "Need Python experience.",
                },
            )

        self.assertEqual(response.status_code, 500)
        self.assertIn("GEMINI_API_KEY", response.json()["detail"])

    def test_analyze_gaps_returns_gap_analysis_payload(self):
        with patch(
            "backend.server.analyze_skill_gaps",
            return_value={"matchedSkills": ["python"], "missingSkills": ["aws"], "matchCount": 1, "missingCount": 1},
        ) as mock_gap:
            response = self.client.post(
                "/analyze-gaps",
                json={
                    "githubUsername": "",
                    "resumeText": "Python engineer",
                    "jobDescription": "Need Python and AWS experience",
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["matchedSkills"], ["python"])
        mock_gap.assert_called_once()

    def test_export_docx_returns_attachment_response(self):
        with patch("backend.server.create_docx_bytes", return_value=b"docx-bytes"):
            response = self.client.post(
                "/export-docx",
                json={
                    "resumeText": "EXPERIENCE\nBuilt APIs",
                    "fileName": "resume_export.docx",
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"docx-bytes")
        self.assertIn("attachment;", response.headers["content-disposition"])

    def test_export_docx_translates_missing_dependency(self):
        with patch(
            "backend.server.create_docx_bytes",
            side_effect=RuntimeError("DOCX export requires the optional 'python-docx' package."),
        ):
            response = self.client.post(
                "/export-docx",
                json={
                    "resumeText": "EXPERIENCE\nBuilt APIs",
                    "fileName": "resume_export.docx",
                },
            )

        self.assertEqual(response.status_code, 501)
        self.assertIn("python-docx", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
