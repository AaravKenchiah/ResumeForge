"""Helpers for extracting resume text and lightweight structure signals."""

from __future__ import annotations

import base64
import re
from dataclasses import asdict, dataclass
from pathlib import Path


COMMON_SECTION_HEADINGS = {
    "summary",
    "professional summary",
    "profile",
    "experience",
    "work experience",
    "professional experience",
    "projects",
    "project experience",
    "skills",
    "technical skills",
    "core competencies",
    "education",
    "certifications",
    "leadership",
    "projects & leadership",
    "activities",
    "awards",
    "publications",
    "contact",
}

DATE_PATTERN = re.compile(
    r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?\s+\d{4}\b"
    r"|\b\d{4}\s*[-/]\s*(?:present|\d{4})\b"
    r"|\b(?:present|current)\b",
    re.IGNORECASE,
)

BULLET_CANDIDATES = ("● ", "- ", "* ", "• ", "▪ ", "◦ ")
EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_PATTERN = re.compile(r"(?:\+?1[\s.-]?)?(?:\(?\d{3}\)?[\s.-]?)\d{3}[\s.-]?\d{4}")
URL_PATTERN = re.compile(r"\b(?:https?://|www\.|linkedin\.com/|github\.com/)\S+\b", re.IGNORECASE)
INLINE_HEADING_PATTERN = re.compile(
    r"^(?P<heading>[A-Za-z][A-Za-z &/,-]{1,40}?)(?::|\s{2,}|\s+\|\s+)(?P<content>.+)$"
)


@dataclass(slots=True)
class ResumeSection:
    """A parsed resume section with its heading and content lines."""

    heading: str
    lines: list[str]


@dataclass(slots=True)
class ResumeHeader:
    """Top-of-resume identity and contact block."""

    name: str
    contact_lines: list[str]
    remaining_lines: list[str]


def normalize_resume_text(raw_text: str) -> str:
    """Collapse line endings and surrounding whitespace while preserving layout."""
    normalized = raw_text.replace("\r\n", "\n").replace("\r", "\n").strip()
    return "\n".join(line.rstrip() for line in normalized.splitlines())


def split_nonempty_lines(text: str) -> list[str]:
    """Return non-empty lines used for lightweight resume analysis."""
    return [line.strip() for line in normalize_resume_text(text).splitlines() if line.strip()]


def is_contact_line(line: str) -> bool:
    """Detect resume header lines containing email, phone, links, or separators."""
    stripped = line.strip()
    if not stripped:
        return False

    return bool(
        EMAIL_PATTERN.search(stripped)
        or PHONE_PATTERN.search(stripped)
        or URL_PATTERN.search(stripped)
        or "@" in stripped
        or "|" in stripped
        or "linkedin" in stripped.lower()
        or "github" in stripped.lower()
    )


def is_probable_name(line: str) -> bool:
    """Detect a likely candidate name at the top of the resume."""
    stripped = line.strip()
    if not stripped:
        return False
    if is_contact_line(stripped):
        return False
    if stripped.lower().strip(":") in COMMON_SECTION_HEADINGS:
        return False

    words = stripped.split()
    if not 2 <= len(words) <= 4:
        return False
    if any(char.isdigit() for char in stripped):
        return False

    alpha_only = [word for word in words if word.replace(".", "").replace("-", "").isalpha()]
    if len(alpha_only) != len(words):
        return False

    return all(word[0].isupper() for word in words if word)


def split_inline_heading(line: str) -> tuple[str, str] | None:
    """Split lines like 'Skills: Python, SQL' into heading and content."""
    match = INLINE_HEADING_PATTERN.match(line.strip())
    if not match:
        return None

    heading = match.group("heading").strip().strip(":")
    content = match.group("content").strip()
    lowered = heading.lower()
    if lowered not in COMMON_SECTION_HEADINGS:
        return None

    return heading, content


def is_probable_heading(line: str) -> bool:
    """Detect likely section headings in common resume formats."""
    stripped = line.strip().strip(":")
    if not stripped:
        return False

    lowered = stripped.lower()
    if lowered in COMMON_SECTION_HEADINGS:
        return True

    words = stripped.split()
    if len(words) > 4:
        return False

    alpha_chars = [char for char in stripped if char.isalpha()]
    if not alpha_chars:
        return False

    if all(word[:1].isupper() for word in words if word.isalpha()):
        lowered = stripped.lower()
        if lowered in COMMON_SECTION_HEADINGS:
            return True

    return stripped.isupper()


def extract_resume_header(lines: list[str]) -> ResumeHeader:
    """Extract probable name and contact lines from the top of the resume."""
    if not lines:
        return ResumeHeader(name="", contact_lines=[], remaining_lines=[])

    index = 0
    name = ""
    contact_lines: list[str] = []

    if is_probable_name(lines[0]):
        name = lines[0]
        index = 1
        while index < len(lines):
            line = lines[index]
            if is_contact_line(line):
                contact_lines.append(line)
                index += 1
                continue
            break

    remaining_lines = lines[index:]
    return ResumeHeader(name=name, contact_lines=contact_lines, remaining_lines=remaining_lines)


def should_start_section(line: str, line_index: int) -> bool:
    """Decide whether a line should start a new section in context."""
    inline_split = split_inline_heading(line)
    if inline_split:
        return True

    if not is_probable_heading(line):
        return False

    lowered = line.strip().strip(":").lower()
    if line.strip().isupper() and lowered not in COMMON_SECTION_HEADINGS:
        return False
    if line_index == 0 and lowered not in COMMON_SECTION_HEADINGS:
        return False

    return True


def extract_section_order(lines: list[str]) -> list[str]:
    """Return section headings in the order they appear in the resume."""
    headings: list[str] = []
    for index, line in enumerate(lines):
        if should_start_section(line, index):
            inline_split = split_inline_heading(line)
            if inline_split:
                headings.append(inline_split[0])
            else:
                headings.append(line.strip().strip(":"))
    return headings


def group_resume_sections(lines: list[str]) -> list[ResumeSection]:
    """Group lines under their nearest detected heading."""
    sections: list[ResumeSection] = []
    header = extract_resume_header(lines)
    current_heading = "General"
    current_lines: list[str] = []

    if header.name:
        current_lines.append(header.name)
    current_lines.extend(header.contact_lines)

    for index, line in enumerate(header.remaining_lines):
        if should_start_section(line, index):
            inline_split = split_inline_heading(line)
            if current_lines or current_heading != "General":
                sections.append(ResumeSection(heading=current_heading, lines=current_lines))
            if inline_split:
                current_heading = inline_split[0]
                current_lines = [inline_split[1]]
            else:
                current_heading = line.strip().strip(":")
                current_lines = []
        else:
            current_lines.append(line)

    if current_lines or current_heading != "General":
        sections.append(ResumeSection(heading=current_heading, lines=current_lines))

    return sections


def detect_bullet_style(lines: list[str]) -> str:
    """Infer the first bullet style used in the resume, if any."""
    for line in lines:
        stripped = line.lstrip()
        for bullet in BULLET_CANDIDATES:
            if stripped.startswith(bullet):
                return bullet.strip()
    return "none"


def detect_date_format(lines: list[str]) -> str:
    """Return a coarse description of the date style used in the resume."""
    for line in lines:
        match = DATE_PATTERN.search(line)
        if not match:
            continue

        value = match.group(0)
        lowered = value.lower()
        if "/" in value or "-" in value:
            return "numeric-range"
        if any(month in lowered for month in ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec")):
            return "month-year"
        if "present" in lowered or "current" in lowered:
            return "open-ended"

    return "unknown"


def infer_skills_format(lines: list[str]) -> str:
    """Guess whether skills are listed inline, bulleted, or not detected."""
    for index, line in enumerate(lines):
        inline_split = split_inline_heading(line)
        if inline_split and inline_split[0].lower() in {"skills", "technical skills", "core competencies"}:
            return "inline"

        if line.lower().startswith("skills") or line.lower().startswith("technical skills"):
            next_line = lines[index + 1] if index + 1 < len(lines) else ""
            if ":" in line and len(line.split(":")[-1].strip()) > 0:
                return "inline"
            if next_line.lstrip().startswith(tuple(BULLET_CANDIDATES)):
                return "bulleted"
            if "," in next_line:
                return "inline"
    return "unknown"


def summarize_resume_structure(text: str) -> dict:
    """Extract lightweight structure metadata needed for format preservation."""
    lines = split_nonempty_lines(text)
    header = extract_resume_header(lines)
    sections = group_resume_sections(lines)
    return {
        "sectionOrder": [section.heading for section in sections],
        "sections": [asdict(section) for section in sections],
        "lineCount": len(lines),
        "bulletStyle": detect_bullet_style(lines),
        "dateFormat": detect_date_format(lines),
        "skillsFormat": infer_skills_format(lines),
        "header": {
            "name": header.name,
            "contactLines": header.contact_lines,
        },
    }


def parse_resume_text(raw_text: str) -> dict:
    """Parse pasted text into content and structure representations."""
    normalized = normalize_resume_text(raw_text)
    return {
        "content": normalized,
        "structure": summarize_resume_structure(normalized),
    }


def decode_file_content(file_content_base64: str) -> bytes:
    """Decode base64 file data sent from the frontend."""
    return base64.b64decode(file_content_base64)


def extract_text_from_txt_bytes(file_bytes: bytes) -> str:
    """Decode UTF-8 text uploads used for plain-text resumes."""
    return file_bytes.decode("utf-8")


def extract_text_from_pdf_bytes(file_bytes: bytes) -> str:
    """Extract text from PDF bytes using pypdf when available."""
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("PDF parsing requires the optional 'pypdf' package.") from exc

    from io import BytesIO

    reader = PdfReader(BytesIO(file_bytes))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(page.strip() for page in pages if page.strip())


def extract_resume_text(file_name: str, file_bytes: bytes) -> str:
    """Dispatch file parsing based on extension."""
    suffix = Path(file_name).suffix.lower()
    if suffix in {".txt", ".md"}:
        return extract_text_from_txt_bytes(file_bytes)
    if suffix == ".pdf":
        return extract_text_from_pdf_bytes(file_bytes)
    raise ValueError(f"Unsupported resume file type: {suffix or 'unknown'}")


def parse_resume_source(
    resume_text: str = "",
    file_name: str = "",
    file_content_base64: str = "",
) -> dict:
    """Parse either pasted text or an uploaded resume file into a common payload."""
    if resume_text.strip():
        parsed = parse_resume_text(resume_text)
        return {"source": "text", **parsed}

    if file_name and file_content_base64:
        file_bytes = decode_file_content(file_content_base64)
        extracted_text = extract_resume_text(file_name, file_bytes)
        parsed = parse_resume_text(extracted_text)
        return {"source": "file", "fileName": file_name, **parsed}

    raise ValueError("Provide either resumeText or both fileName and fileContentBase64.")
