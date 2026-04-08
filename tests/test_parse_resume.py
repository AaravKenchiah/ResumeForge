"""Unit tests for resume parsing helpers."""

import base64
import unittest
from unittest.mock import patch

from backend.parse_resume import (
    decode_file_content,
    detect_bullet_style,
    detect_date_format,
    extract_resume_header,
    extract_resume_text,
    group_resume_sections,
    infer_skills_format,
    is_contact_line,
    is_probable_heading,
    is_probable_name,
    normalize_resume_text,
    parse_resume_source,
    parse_resume_text,
    split_inline_heading,
    split_nonempty_lines,
    summarize_resume_structure,
)


SAMPLE_RESUME = """
JANE DEVELOPER
jane@example.com | github.com/janedev | linkedin.com/in/janedev

SUMMARY
Backend engineer focused on APIs and data systems.

EXPERIENCE
Software Engineer
- Built FastAPI services
- Improved job processing throughput

SKILLS
Python, FastAPI, PostgreSQL

EDUCATION
State University
May 2024
"""

INLINE_RESUME = """
Jane Developer
jane@example.com | github.com/janedev
Technical Skills: Python, SQL, AWS, Docker
Projects & Leadership
Built a campus developer club and shipped internal tools.
Education
State University | GPA: 3.9
"""

UNICODE_BULLET_RESUME = """
Jane Developer
jane@example.com | github.com/janedev

SKILLS
● Languages: Python, SQL
● Tools: Git, Jupyter
"""


class ParseResumeTests(unittest.TestCase):
    """Verify resume parsing behavior and structure extraction helpers."""

    def test_normalize_resume_text_preserves_lines_and_trims_edges(self):
        normalized = normalize_resume_text(" \r\nLine one  \r\nLine two\r\n")

        self.assertEqual(normalized, "Line one\nLine two")

    def test_split_nonempty_lines_filters_blank_lines(self):
        lines = split_nonempty_lines("A\n\nB\n  \nC")

        self.assertEqual(lines, ["A", "B", "C"])

    def test_is_contact_line_detects_common_contact_formats(self):
        self.assertTrue(is_contact_line("jane@example.com | github.com/janedev"))
        self.assertTrue(is_contact_line("(555) 123-4567"))
        self.assertFalse(is_contact_line("Software Engineer"))

    def test_is_probable_name_detects_name_lines(self):
        self.assertTrue(is_probable_name("Jane Developer"))
        self.assertFalse(is_probable_name("jane@example.com"))
        self.assertFalse(is_probable_name("EXPERIENCE"))

    def test_is_probable_heading_detects_common_resume_headings(self):
        self.assertTrue(is_probable_heading("EXPERIENCE"))
        self.assertTrue(is_probable_heading("Technical Skills"))
        self.assertTrue(is_probable_heading("Projects & Leadership"))
        self.assertFalse(is_probable_heading("Built FastAPI services"))

    def test_split_inline_heading_detects_inline_section_content(self):
        split = split_inline_heading("Technical Skills: Python, SQL, AWS")

        self.assertEqual(split, ("Technical Skills", "Python, SQL, AWS"))
        self.assertIsNone(split_inline_heading("Backend engineer focused on APIs"))

    def test_extract_resume_header_separates_name_and_contact(self):
        lines = split_nonempty_lines(SAMPLE_RESUME)

        header = extract_resume_header(lines)

        self.assertEqual(header.name, "JANE DEVELOPER")
        self.assertEqual(header.contact_lines, ["jane@example.com | github.com/janedev | linkedin.com/in/janedev"])
        self.assertEqual(header.remaining_lines[0], "SUMMARY")

    def test_group_resume_sections_assigns_lines_under_headings(self):
        lines = split_nonempty_lines(SAMPLE_RESUME)

        sections = group_resume_sections(lines)

        self.assertEqual(sections[0].heading, "General")
        self.assertIn("JANE DEVELOPER", sections[0].lines)
        self.assertEqual(sections[1].heading, "SUMMARY")
        self.assertIn("Backend engineer focused on APIs and data systems.", sections[1].lines)
        self.assertEqual(sections[2].heading, "EXPERIENCE")

    def test_group_resume_sections_handles_inline_and_title_case_sections(self):
        sections = group_resume_sections(split_nonempty_lines(INLINE_RESUME))

        self.assertEqual(sections[0].heading, "General")
        self.assertIn("Jane Developer", sections[0].lines)
        self.assertEqual(sections[1].heading, "Technical Skills")
        self.assertEqual(sections[1].lines, ["Python, SQL, AWS, Docker"])
        self.assertEqual(sections[2].heading, "Projects & Leadership")
        self.assertEqual(sections[3].heading, "Education")

    def test_detect_bullet_style_returns_first_detected_bullet(self):
        style = detect_bullet_style(split_nonempty_lines(SAMPLE_RESUME))

        self.assertEqual(style, "-")

    def test_detect_bullet_style_supports_black_circle_bullets(self):
        style = detect_bullet_style(split_nonempty_lines(UNICODE_BULLET_RESUME))

        self.assertEqual(style, "●")

    def test_detect_date_format_identifies_month_year(self):
        date_format = detect_date_format(split_nonempty_lines(SAMPLE_RESUME))

        self.assertEqual(date_format, "month-year")

    def test_infer_skills_format_identifies_inline_skills(self):
        skills_format = infer_skills_format(split_nonempty_lines(INLINE_RESUME))

        self.assertEqual(skills_format, "inline")

    def test_summarize_resume_structure_returns_expected_metadata(self):
        structure = summarize_resume_structure(SAMPLE_RESUME)

        self.assertEqual(structure["sectionOrder"], ["General", "SUMMARY", "EXPERIENCE", "SKILLS", "EDUCATION"])
        self.assertEqual(structure["bulletStyle"], "-")
        self.assertEqual(structure["dateFormat"], "month-year")
        self.assertEqual(structure["skillsFormat"], "inline")
        self.assertEqual(structure["header"]["name"], "JANE DEVELOPER")
        self.assertEqual(len(structure["header"]["contactLines"]), 1)

    def test_summarize_resume_structure_preserves_dense_one_line_formats(self):
        structure = summarize_resume_structure(INLINE_RESUME)

        self.assertEqual(
            structure["sectionOrder"],
            ["General", "Technical Skills", "Projects & Leadership", "Education"],
        )
        self.assertEqual(structure["sections"][1]["lines"], ["Python, SQL, AWS, Docker"])

    def test_parse_resume_text_returns_content_and_structure(self):
        parsed = parse_resume_text(SAMPLE_RESUME)

        self.assertIn("JANE DEVELOPER", parsed["content"])
        self.assertIn("EXPERIENCE", parsed["structure"]["sectionOrder"])

    def test_decode_file_content_decodes_base64_payload(self):
        encoded = base64.b64encode(b"resume content").decode("utf-8")

        decoded = decode_file_content(encoded)

        self.assertEqual(decoded, b"resume content")

    def test_extract_resume_text_reads_txt_files(self):
        extracted = extract_resume_text("resume.txt", b"Hello world")

        self.assertEqual(extracted, "Hello world")

    def test_extract_resume_text_rejects_unsupported_extensions(self):
        with self.assertRaises(ValueError):
            extract_resume_text("resume.docx", b"binary")

    def test_parse_resume_source_prefers_pasted_text(self):
        parsed = parse_resume_source(resume_text=SAMPLE_RESUME)

        self.assertEqual(parsed["source"], "text")
        self.assertIn("SUMMARY", parsed["structure"]["sectionOrder"])

    def test_parse_resume_source_parses_uploaded_text_file(self):
        encoded = base64.b64encode(SAMPLE_RESUME.encode("utf-8")).decode("utf-8")

        parsed = parse_resume_source(file_name="resume.txt", file_content_base64=encoded)

        self.assertEqual(parsed["source"], "file")
        self.assertEqual(parsed["fileName"], "resume.txt")
        self.assertIn("EDUCATION", parsed["structure"]["sectionOrder"])

    def test_parse_resume_source_raises_when_input_missing(self):
        with self.assertRaises(ValueError):
            parse_resume_source()

    def test_parse_resume_source_raises_when_pdf_support_missing(self):
        encoded = base64.b64encode(b"%PDF-1.4").decode("utf-8")

        with patch("builtins.__import__", side_effect=ImportError()):
            with self.assertRaises(RuntimeError):
                parse_resume_source(file_name="resume.pdf", file_content_base64=encoded)


if __name__ == "__main__":
    unittest.main()
