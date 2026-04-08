"""Gemini-powered GitHub project ranking and resume bullet generation."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Callable

from backend.claude_tailor import (
    DEFAULT_MODEL,
    build_gemini_headers,
    build_gemini_url,
    default_json_post,
    extract_text_from_gemini_response,
)


DEFAULT_MAX_TOKENS = 2000
DEFAULT_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "project_bullets_prompt.txt"

JsonPoster = Callable[[str, dict[str, str], dict], dict]


def load_project_prompt(prompt_path: str | Path = DEFAULT_PROMPT_PATH) -> str:
    """Load the project recommendation system prompt from disk."""
    return Path(prompt_path).read_text(encoding="utf-8").strip()


def build_project_recommendation_user_message(github_profile: dict, job_description: str) -> str:
    """Assemble the user prompt for ranking GitHub projects against a target role."""
    repos = github_profile.get("repos", [])
    serialized_repos = json.dumps(repos, indent=2, ensure_ascii=True, sort_keys=True)

    return (
        "## GitHub Username\n"
        f"{github_profile.get('username', '').strip()}\n\n"
        "## GitHub Project Data\n"
        f"{serialized_repos}\n\n"
        "## Job Description\n"
        f"{job_description.strip()}\n\n"
        "## Output Contract\n"
        "- Return valid JSON only.\n"
        "- Rank the repositories from most relevant to least relevant for the role.\n"
        "- For each repository, write 3 or 4 concise, copy-pasteable resume bullets.\n"
        "- Ground every bullet in the provided repository metadata, description, topics, and README excerpt.\n"
        "- Use job-description keywords only when they truthfully match the project evidence.\n"
        "- Do not mention the candidate's resume, formatting advice, or any explanation outside the JSON.\n"
    )


def build_project_recommendation_payload(
    system_prompt: str,
    user_message: str,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> dict:
    """Create the Gemini payload for project recommendation generation."""
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
            "responseMimeType": "application/json",
        },
    }


def strip_json_fence(text: str) -> str:
    """Remove optional markdown code fences around a JSON payload."""
    stripped = text.strip()
    fenced_match = re.match(r"^```(?:json)?\s*(.*?)\s*```$", stripped, re.DOTALL)
    if fenced_match:
        return fenced_match.group(1).strip()
    return stripped


def parse_project_recommendations(text: str) -> dict:
    """Parse Gemini JSON output into a Python dictionary."""
    cleaned = strip_json_fence(text)
    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError("Gemini returned invalid project recommendation JSON.") from exc

    if not isinstance(payload, dict) or not isinstance(payload.get("projects"), list):
        raise ValueError("Gemini project recommendation response was missing a 'projects' list.")

    return payload


def normalize_project_recommendations(payload: dict, github_profile: dict) -> list[dict]:
    """Normalize model output and enrich it with repository metadata."""
    repo_by_name = {repo.get("name", ""): repo for repo in github_profile.get("repos", [])}
    normalized_projects: list[dict] = []

    for index, project in enumerate(payload.get("projects", []), start=1):
        if not isinstance(project, dict):
            continue

        name = str(project.get("name", "")).strip()
        if not name:
            continue

        source_repo = repo_by_name.get(name, {})
        bullets = [
            str(bullet).strip()
            for bullet in project.get("bullets", [])
            if isinstance(bullet, str) and bullet.strip()
        ][:4]

        normalized_projects.append(
            {
                "rank": int(project.get("rank") or index),
                "name": name,
                "relevanceSummary": str(project.get("relevanceSummary", "")).strip(),
                "language": source_repo.get("language", "Unknown"),
                "url": source_repo.get("html_url", ""),
                "description": source_repo.get("description", ""),
                "bullets": bullets,
            }
        )

    normalized_projects.sort(key=lambda project: project["rank"])
    return normalized_projects


def generate_project_recommendations(
    github_profile: dict,
    job_description: str,
    api_key: str | None = None,
    prompt_path: str | Path = DEFAULT_PROMPT_PATH,
    model: str | None = None,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    json_poster: JsonPoster = default_json_post,
) -> list[dict]:
    """Generate ranked, copy-ready bullets for GitHub projects."""
    resolved_api_key = api_key or os.getenv("GEMINI_API_KEY")
    if not resolved_api_key:
        raise RuntimeError("Missing GEMINI_API_KEY for Gemini API integration.")

    system_prompt = load_project_prompt(prompt_path)
    user_message = build_project_recommendation_user_message(github_profile, job_description)
    payload = build_project_recommendation_payload(system_prompt, user_message, max_tokens=max_tokens)
    response_payload = json_poster(
        build_gemini_url(model or os.getenv("GEMINI_MODEL") or DEFAULT_MODEL),
        build_gemini_headers(resolved_api_key),
        payload,
    )
    response_text = extract_text_from_gemini_response(response_payload)
    parsed_payload = parse_project_recommendations(response_text)
    return normalize_project_recommendations(parsed_payload, github_profile)
