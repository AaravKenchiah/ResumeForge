"""Unit tests for skill-gap analysis helpers."""

import unittest

from backend.gap_analysis import analyze_skill_gaps, extract_skill_matches, normalize_text_for_matching


class GapAnalysisTests(unittest.TestCase):
    """Verify keyword extraction and gap analysis behavior."""

    def test_normalize_text_for_matching_collapses_whitespace(self):
        self.assertEqual(normalize_text_for_matching("Python \n  AWS"), "python aws")

    def test_extract_skill_matches_finds_known_keywords(self):
        matches = extract_skill_matches("Built APIs with Python, FastAPI, PostgreSQL, and AWS.")

        self.assertEqual(matches, ["aws", "fastapi", "postgresql", "python"])

    def test_analyze_skill_gaps_reports_matched_and_missing_skills(self):
        analysis = analyze_skill_gaps(
            resume_text="Software engineer using Python, FastAPI, and PostgreSQL.",
            github_summary="- infra-tool | Terraform | AWS",
            job_description="Looking for Python, AWS, Kubernetes, and PostgreSQL experience.",
        )

        self.assertEqual(analysis["matchedSkills"], ["aws", "postgresql", "python"])
        self.assertEqual(analysis["missingSkills"], ["kubernetes"])
        self.assertEqual(analysis["matchCount"], 3)
        self.assertEqual(analysis["missingCount"], 1)


if __name__ == "__main__":
    unittest.main()
