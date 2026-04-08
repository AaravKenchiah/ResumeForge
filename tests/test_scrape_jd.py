"""Unit tests for job description scraping and cleanup helpers."""

import unittest

from backend.scrape_jd import (
    clean_job_description,
    extract_candidate_containers,
    extract_description_from_job_posting_schema,
    extract_job_text_from_html,
    extract_job_text_from_json_ld,
    fetch_job_posting,
    looks_like_job_description,
    normalize_job_text,
    parse_job_description_source,
    select_best_candidate_text,
    strip_noise_lines,
)


HTML_SAMPLE = """
<html>
  <body>
    <nav>Sign In</nav>
    <section>
      <h1>Senior Backend Engineer</h1>
      <p>Build resilient APIs for financial systems.</p>
      <div>Responsibilities</div>
      <ul>
        <li>Design backend services</li>
        <li>Improve reliability</li>
      </ul>
      <div>Apply Now</div>
    </section>
    <footer>Privacy Policy</footer>
  </body>
</html>
"""

JSON_LD_HTML = """
<html>
  <head>
    <script type="application/ld+json">
      {
        "@context": "https://schema.org",
        "@type": "JobPosting",
        "title": "Staff Platform Engineer",
        "description": "<p>Build internal platform systems.</p><p>Responsibilities include reliability and developer tooling.</p>",
        "qualifications": "5+ years of backend or platform engineering experience."
      }
    </script>
  </head>
  <body>
    <div id="app">Loading...</div>
  </body>
</html>
"""

CONTAINER_HTML = """
<html>
  <body>
    <div class="hero">Apply now</div>
    <article class="job-description content">
      <h1>Backend Engineer</h1>
      <p>About the role</p>
      <p>Design APIs and improve system reliability.</p>
      <ul>
        <li>Build backend services</li>
        <li>Collaborate with product and infrastructure teams</li>
      </ul>
    </article>
  </body>
</html>
"""


class ScrapeJobDescriptionTests(unittest.TestCase):
    """Verify job description cleanup and HTML extraction helpers."""

    def test_normalize_job_text_decodes_entities_and_line_endings(self):
        normalized = normalize_job_text("Role &amp; Impact\r\nBuild APIs\r\n")

        self.assertEqual(normalized, "Role & Impact\nBuild APIs")

    def test_strip_noise_lines_removes_duplicates_and_boilerplate(self):
        lines = strip_noise_lines(
            [
                "Apply Now",
                "Senior Backend Engineer",
                "Senior Backend Engineer",
                "Privacy Policy",
                "Build APIs",
            ]
        )

        self.assertEqual(lines, ["Senior Backend Engineer", "Build APIs"])

    def test_clean_job_description_returns_prompt_ready_text(self):
        cleaned = clean_job_description("Apply Now\nSenior Backend Engineer\n\nBuild APIs\nApply Now")

        self.assertEqual(cleaned, "Senior Backend Engineer\nBuild APIs")

    def test_looks_like_job_description_detects_real_jd_signals(self):
        self.assertTrue(
            looks_like_job_description(
                "Responsibilities include building APIs and improving reliability. "
                "Qualifications include Python experience and backend systems knowledge."
            )
        )
        self.assertFalse(looks_like_job_description("Backend Engineer"))

    def test_extract_description_from_job_posting_schema_reads_relevant_fields(self):
        extracted = extract_description_from_job_posting_schema(
            {
                "@type": "JobPosting",
                "title": "Platform Engineer",
                "description": "<p>Build platform systems.</p>",
                "qualifications": "Strong Python experience.",
            }
        )

        self.assertIn("Platform Engineer", extracted)
        self.assertIn("Build platform systems.", extracted)
        self.assertIn("Strong Python experience.", extracted)

    def test_extract_job_text_from_json_ld_prefers_job_posting_schema(self):
        extracted = extract_job_text_from_json_ld(JSON_LD_HTML)

        self.assertIn("Staff Platform Engineer", extracted)
        self.assertIn("Build internal platform systems.", extracted)
        self.assertIn("platform engineering experience.", extracted)

    def test_extract_candidate_containers_reads_job_description_regions(self):
        candidates = extract_candidate_containers(CONTAINER_HTML)

        self.assertEqual(len(candidates), 1)
        self.assertIn("Backend Engineer", candidates[0])
        self.assertIn("Build backend services", candidates[0])

    def test_select_best_candidate_text_prefers_jd_like_content(self):
        best = select_best_candidate_text(
            [
                "Short blurb",
                "Backend Engineer\nResponsibilities\nBuild systems\nQualifications\nPython experience required",
            ]
        )

        self.assertIn("Qualifications", best)

    def test_extract_job_text_from_html_uses_json_ld_before_visible_text(self):
        extracted = extract_job_text_from_html(JSON_LD_HTML)

        self.assertIn("Staff Platform Engineer", extracted)
        self.assertNotIn("Loading...", extracted)

    def test_extract_job_text_from_html_uses_candidate_containers_before_fallback(self):
        extracted = extract_job_text_from_html(CONTAINER_HTML)

        self.assertIn("Backend Engineer", extracted)
        self.assertIn("Collaborate with product and infrastructure teams", extracted)
        self.assertNotIn("Apply now", extracted)

    def test_extract_job_text_from_html_discards_blocked_tags_and_noise(self):
        extracted = extract_job_text_from_html(HTML_SAMPLE)

        self.assertIn("Senior Backend Engineer", extracted)
        self.assertIn("Design backend services", extracted)
        self.assertNotIn("Sign In", extracted)
        self.assertNotIn("Apply Now", extracted)

    def test_fetch_job_posting_uses_fetcher_and_returns_cleaned_text(self):
        def fake_fetcher(url, headers):
            self.assertEqual(url, "https://company.com/jobs/123")
            self.assertEqual(headers["User-Agent"], "ResumeForge")
            return JSON_LD_HTML

        result = fetch_job_posting("https://company.com/jobs/123", text_fetcher=fake_fetcher)

        self.assertIn("Staff Platform Engineer", result)
        self.assertIn("platform engineering experience.", result)

    def test_parse_job_description_source_prefers_pasted_text(self):
        parsed = parse_job_description_source(job_description_text="Apply Now\nPython Engineer")

        self.assertEqual(parsed["source"], "text")
        self.assertEqual(parsed["content"], "Python Engineer")

    def test_parse_job_description_source_supports_url_input(self):
        parsed = parse_job_description_source(
            job_description_url="https://company.com/jobs/123",
            text_fetcher=lambda url, headers: CONTAINER_HTML,
        )

        self.assertEqual(parsed["source"], "url")
        self.assertEqual(parsed["url"], "https://company.com/jobs/123")
        self.assertIn("Backend Engineer", parsed["content"])

    def test_parse_job_description_source_requires_input(self):
        with self.assertRaises(ValueError):
            parse_job_description_source()


if __name__ == "__main__":
    unittest.main()
