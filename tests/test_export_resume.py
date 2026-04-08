"""Unit tests for resume DOCX export helpers."""

import unittest
from unittest.mock import patch

from backend.export_resume import create_docx_bytes, is_heading_line


class ExportResumeTests(unittest.TestCase):
    """Verify line formatting and optional DOCX export behavior."""

    def test_is_heading_line_detects_short_uppercase_headings(self):
        self.assertTrue(is_heading_line("EXPERIENCE"))
        self.assertFalse(is_heading_line("Software Engineer"))

    def test_create_docx_bytes_requires_python_docx(self):
        with patch("builtins.__import__", side_effect=ImportError()):
            with self.assertRaises(RuntimeError):
                create_docx_bytes("EXPERIENCE\nBuilt APIs")


if __name__ == "__main__":
    unittest.main()
