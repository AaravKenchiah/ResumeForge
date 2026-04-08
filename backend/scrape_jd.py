"""Helpers for cleaning and extracting job descriptions from text or URLs."""

from __future__ import annotations

import html
import json
import re
from html.parser import HTMLParser
from urllib import request


BLOCKED_TAGS = {"script", "style", "noscript", "svg", "footer", "nav", "form"}
STRUCTURED_DATA_SCRIPT_TYPES = {
    "application/ld+json",
    "application/json+ld",
}
NOISE_PATTERNS = (
    re.compile(r"^(apply now|apply|sign in|join now)$", re.IGNORECASE),
    re.compile(r"^(privacy policy|terms of use|cookie preferences)$", re.IGNORECASE),
    re.compile(r"^(share this job|report this job)$", re.IGNORECASE),
)
DESCRIPTION_CONTAINER_HINTS = (
    "job-description",
    "job_description",
    "jobdescription",
    "description",
    "posting",
    "job-posting",
    "jd",
    "details",
    "content",
)


class JobDescriptionHTMLParser(HTMLParser):
    """Extract readable text while skipping common non-content HTML blocks."""

    def __init__(self):
        super().__init__()
        self._ignored_depth = 0
        self._chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs):
        if tag in BLOCKED_TAGS:
            self._ignored_depth += 1
            return

        if self._ignored_depth == 0 and tag in {"p", "br", "li", "div", "section", "h1", "h2", "h3"}:
            self._chunks.append("\n")

    def handle_endtag(self, tag: str):
        if tag in BLOCKED_TAGS and self._ignored_depth > 0:
            self._ignored_depth -= 1
            return

        if self._ignored_depth == 0 and tag in {"p", "li", "div", "section"}:
            self._chunks.append("\n")

    def handle_data(self, data: str):
        if self._ignored_depth > 0:
            return

        text = data.strip()
        if text:
            self._chunks.append(text)

    def get_text(self) -> str:
        """Return the parsed text content."""
        return "\n".join(self._chunks)


def normalize_job_text(raw_text: str) -> str:
    """Normalize whitespace and decode basic HTML entities."""
    decoded = html.unescape(raw_text).replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(line.rstrip() for line in decoded.splitlines())


def strip_noise_lines(lines: list[str]) -> list[str]:
    """Remove boilerplate lines commonly found on job pages."""
    cleaned: list[str] = []
    seen: set[str] = set()

    for line in lines:
        stripped = " ".join(line.split())
        if not stripped:
            continue

        if any(pattern.match(stripped) for pattern in NOISE_PATTERNS):
            continue

        lowered = stripped.lower()
        if lowered in seen:
            continue

        seen.add(lowered)
        cleaned.append(stripped)

    return cleaned


def clean_job_description(raw_text: str) -> str:
    """Clean pasted or extracted job text into a prompt-ready description."""
    normalized = normalize_job_text(raw_text)
    lines = strip_noise_lines(normalized.splitlines())
    return "\n".join(lines)


def looks_like_job_description(text: str) -> bool:
    """Heuristic check for job-description-like content."""
    lowered = text.lower()
    signals = (
        "responsibilities",
        "requirements",
        "qualifications",
        "experience",
        "about the role",
        "what you'll do",
        "preferred",
    )
    return len(text.split()) >= 12 and any(signal in lowered for signal in signals)


def iter_json_objects(payload):
    """Yield dictionaries from nested JSON-LD payloads."""
    if isinstance(payload, dict):
        yield payload
        for value in payload.values():
            yield from iter_json_objects(value)
    elif isinstance(payload, list):
        for item in payload:
            yield from iter_json_objects(item)


def extract_description_from_job_posting_schema(schema_object: dict) -> str:
    """Extract description-like fields from a JobPosting JSON-LD object."""
    if schema_object.get("@type") != "JobPosting":
        return ""

    parts: list[str] = []
    for field in ("title", "description", "qualifications", "responsibilities", "skills"):
        value = schema_object.get(field)
        if isinstance(value, str) and value.strip():
            parts.append(value.strip())
        elif isinstance(value, list):
            flattened = [str(item).strip() for item in value if str(item).strip()]
            if flattened:
                parts.append("\n".join(flattened))

    return clean_job_description("\n".join(parts))


def extract_job_text_from_json_ld(html_text: str) -> str:
    """Extract job text from embedded JSON-LD JobPosting metadata."""
    pattern = re.compile(
        r"<script[^>]*type=[\"'](?:application/ld\+json|application/json\+ld)[\"'][^>]*>(.*?)</script>",
        re.IGNORECASE | re.DOTALL,
    )

    for match in pattern.finditer(html_text):
        script_body = match.group(1).strip()
        if not script_body:
            continue

        try:
            payload = json.loads(script_body)
        except json.JSONDecodeError:
            continue

        for item in iter_json_objects(payload):
            extracted = extract_description_from_job_posting_schema(item)
            if extracted:
                return extracted

    return ""


def extract_candidate_containers(html_text: str) -> list[str]:
    """Extract text from containers that look like job description regions."""
    pattern = re.compile(
        r"<(?P<tag>section|div|article)[^>]*(?:id|class)=[\"'](?P<attr>[^\"']+)[\"'][^>]*>(?P<body>.*?)</(?P=tag)>",
        re.IGNORECASE | re.DOTALL,
    )
    candidates: list[str] = []

    for match in pattern.finditer(html_text):
        attr = match.group("attr").lower()
        if not any(hint in attr for hint in DESCRIPTION_CONTAINER_HINTS):
            continue

        body = match.group("body")
        parser = JobDescriptionHTMLParser()
        parser.feed(body)
        candidate_text = clean_job_description(parser.get_text())
        if candidate_text:
            candidates.append(candidate_text)

    return candidates


def select_best_candidate_text(candidates: list[str]) -> str:
    """Choose the most promising extracted job description candidate."""
    if not candidates:
        return ""

    scored_candidates = []
    for candidate in candidates:
        score = len(candidate.splitlines()) + len(candidate.split()) / 10
        if looks_like_job_description(candidate):
            score += 25
        scored_candidates.append((score, candidate))

    scored_candidates.sort(key=lambda item: item[0], reverse=True)
    return scored_candidates[0][1]


def extract_job_text_from_html(html_text: str) -> str:
    """Extract visible text from job-page HTML using layered fallbacks."""
    json_ld_text = extract_job_text_from_json_ld(html_text)
    if json_ld_text:
        return json_ld_text

    container_text = select_best_candidate_text(extract_candidate_containers(html_text))
    if container_text:
        return container_text

    parser = JobDescriptionHTMLParser()
    parser.feed(html_text)
    return clean_job_description(parser.get_text())


def default_text_fetch(url: str, headers: dict[str, str]) -> str:
    """Fetch text content from a job posting URL."""
    req = request.Request(url, headers=headers)
    with request.urlopen(req, timeout=20) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="ignore")


def fetch_job_posting(url: str, text_fetcher=default_text_fetch) -> str:
    """Fetch a job posting page and return extracted readable text."""
    headers = {"User-Agent": "ResumeForge"}
    html_text = text_fetcher(url, headers)
    return extract_job_text_from_html(html_text)


def parse_job_description_source(
    job_description_text: str = "",
    job_description_url: str = "",
    text_fetcher=default_text_fetch,
) -> dict:
    """Parse either pasted text or a job-posting URL into a common payload."""
    if job_description_text.strip():
        cleaned = clean_job_description(job_description_text)
        return {
            "source": "text",
            "content": cleaned,
            "lineCount": len(cleaned.splitlines()) if cleaned else 0,
        }

    if job_description_url.strip():
        cleaned = fetch_job_posting(job_description_url.strip(), text_fetcher=text_fetcher)
        return {
            "source": "url",
            "url": job_description_url.strip(),
            "content": cleaned,
            "lineCount": len(cleaned.splitlines()) if cleaned else 0,
        }

    raise ValueError("Provide either jobDescriptionText or jobDescriptionUrl.")
