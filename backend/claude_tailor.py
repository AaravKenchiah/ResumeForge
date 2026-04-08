"""Prompt assembly and Gemini API integration for resume tailoring."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Callable
from urllib import parse, request


GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
DEFAULT_MODEL = "gemini-flash-latest"
DEFAULT_MAX_TOKENS = 1200
DEFAULT_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "tailor_prompt.txt"


JsonPoster = Callable[[str, dict[str, str], dict], dict]


def load_system_prompt(prompt_path: str | Path = DEFAULT_PROMPT_PATH) -> str:
    """Load the tailoring system prompt from disk."""
    return Path(prompt_path).read_text(encoding="utf-8").strip()


def build_gemini_headers(api_key: str) -> dict[str, str]:
    """Build request headers for the Gemini REST API."""
    return {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key,
    }


def format_structure_for_prompt(resume_structure: dict) -> str:
    """Render parsed resume structure in a readable, deterministic format."""
    return json.dumps(resume_structure, indent=2, ensure_ascii=True, sort_keys=True)


def build_tailor_user_message(
    resume_text: str,
    resume_structure: dict,
    github_summary: str,
    job_description: str,
) -> str:
    """Assemble the user message passed to Gemini for resume tailoring."""
    structure_text = format_structure_for_prompt(resume_structure)
    github_text = github_summary or "No GitHub data available."
    section_order = ", ".join(resume_structure.get("sectionOrder", [])) or "Unknown"
    bullet_style = resume_structure.get("bulletStyle", "unknown")
    date_format = resume_structure.get("dateFormat", "unknown")
    skills_format = resume_structure.get("skillsFormat", "unknown")
    line_count = resume_structure.get("lineCount", "unknown")

    return (
        "## Original Resume\n"
        f"{resume_text.strip()}\n\n"
        "## Formatting Signals To Preserve\n"
        f"- Section order: {section_order}\n"
        f"- Bullet style: {bullet_style}\n"
        f"- Date format: {date_format}\n"
        f"- Skills format: {skills_format}\n"
        f"- Approximate source line count: {line_count}\n\n"
        "## Parsed Resume Structure\n"
        f"{structure_text}\n\n"
        "## GitHub Project Summary\n"
        f"{github_text}\n\n"
        "## Job Description\n"
        f"{job_description.strip()}\n\n"
        "## Output Contract\n"
        "- Return only the resume text.\n"
        "- Preserve the original section names, section order, header style, bullet character, and date style.\n"
        "- Keep the resume to one page by tightening bullets and replacing low-relevance content with stronger evidence when needed.\n"
        "- Use GitHub projects only when they are relevant and truthful.\n"
        "- Do not fabricate tools, metrics, responsibilities, titles, dates, or results.\n"
        "- Keep the final resume dense and polished, with no explanatory notes.\n"
    )


def build_gemini_url(model: str = DEFAULT_MODEL) -> str:
    """Create the Gemini generateContent endpoint URL for a model."""
    return f"{GEMINI_API_BASE}/{parse.quote(model)}:generateContent"


def build_gemini_payload(
    system_prompt: str,
    user_message: str,
    model: str = DEFAULT_MODEL,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> dict:
    """Create the request payload for Gemini generateContent."""
    return {
        "systemInstruction": {
            "parts": [{"text": system_prompt}],
        },
        "contents": [
            {
                "role": "user",
                "parts": [{"text": user_message}],
            }
        ],
        "generationConfig": {
            "maxOutputTokens": max_tokens,
        },
    }


def extract_text_from_gemini_response(response_payload: dict) -> str:
    """Extract concatenated text parts from a Gemini response payload."""
    candidates = response_payload.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("Gemini response did not contain any candidates.")

    parts = candidates[0].get("content", {}).get("parts", [])
    if not isinstance(parts, list):
        raise ValueError("Gemini response did not contain content parts.")

    text_parts = [part.get("text", "") for part in parts if isinstance(part, dict) and part.get("text")]
    combined = "\n".join(part.strip() for part in text_parts if part.strip()).strip()

    if not combined:
        raise ValueError("Gemini response did not contain any text output.")

    return combined


def default_json_post(url: str, headers: dict[str, str], payload: dict) -> dict:
    """Send a JSON POST request and decode the JSON response."""
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=body, headers=headers, method="POST")
    with request.urlopen(req, timeout=60) as response:
        return json.load(response)


def generate_tailored_resume(
    resume_text: str,
    resume_structure: dict,
    github_summary: str,
    job_description: str,
    api_key: str | None = None,
    prompt_path: str | Path = DEFAULT_PROMPT_PATH,
    model: str | None = None,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    json_poster: JsonPoster = default_json_post,
) -> str:
    """Generate a tailored resume using the Gemini REST API."""
    resolved_api_key = api_key or os.getenv("GEMINI_API_KEY")
    if not resolved_api_key:
        raise RuntimeError("Missing GEMINI_API_KEY for Gemini API integration.")

    resolved_model = model or os.getenv("GEMINI_MODEL") or DEFAULT_MODEL
    system_prompt = load_system_prompt(prompt_path)
    user_message = build_tailor_user_message(
        resume_text=resume_text,
        resume_structure=resume_structure,
        github_summary=github_summary,
        job_description=job_description,
    )
    payload = build_gemini_payload(
        system_prompt=system_prompt,
        user_message=user_message,
        model=resolved_model,
        max_tokens=max_tokens,
    )
    response_payload = json_poster(
        build_gemini_url(resolved_model),
        build_gemini_headers(resolved_api_key),
        payload,
    )
    return extract_text_from_gemini_response(response_payload)
