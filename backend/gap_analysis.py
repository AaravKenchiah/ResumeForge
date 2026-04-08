"""Lightweight job-description skill gap analysis for resume tailoring."""

from __future__ import annotations

import re


COMMON_SKILL_KEYWORDS = [
    "python",
    "java",
    "javascript",
    "typescript",
    "go",
    "c++",
    "c#",
    "react",
    "node.js",
    "node",
    "fastapi",
    "django",
    "flask",
    "spring",
    "aws",
    "gcp",
    "azure",
    "docker",
    "kubernetes",
    "terraform",
    "postgresql",
    "mysql",
    "redis",
    "mongodb",
    "sql",
    "graphql",
    "rest",
    "microservices",
    "ci/cd",
    "git",
    "linux",
    "machine learning",
    "data analysis",
    "pandas",
    "numpy",
    "spark",
    "airflow",
    "llm",
    "oauth",
    "jwt",
]


def normalize_text_for_matching(text: str) -> str:
    """Normalize free-form text for case-insensitive keyword matching."""
    return re.sub(r"\s+", " ", text.lower()).strip()


def extract_skill_matches(text: str, skill_keywords: list[str] | None = None) -> list[str]:
    """Return sorted skill keywords explicitly mentioned in the text."""
    normalized = normalize_text_for_matching(text)
    keywords = skill_keywords or COMMON_SKILL_KEYWORDS
    matches: list[str] = []

    for skill in keywords:
        pattern = r"(?<![a-z0-9])" + re.escape(skill.lower()) + r"(?![a-z0-9])"
        if re.search(pattern, normalized):
            matches.append(skill)

    return sorted(set(matches), key=str.lower)


def analyze_skill_gaps(
    resume_text: str,
    job_description: str,
    github_summary: str = "",
    skill_keywords: list[str] | None = None,
) -> dict:
    """Compare job-description skills against resume and GitHub evidence."""
    keywords = skill_keywords or COMMON_SKILL_KEYWORDS
    jd_skills = extract_skill_matches(job_description, keywords)
    evidence_text = "\n".join(part for part in [resume_text, github_summary] if part.strip())
    present_skills = extract_skill_matches(evidence_text, keywords)

    present_set = set(skill.lower() for skill in present_skills)
    matched = [skill for skill in jd_skills if skill.lower() in present_set]
    missing = [skill for skill in jd_skills if skill.lower() not in present_set]

    return {
        "jobDescriptionSkills": jd_skills,
        "presentSkills": present_skills,
        "matchedSkills": matched,
        "missingSkills": missing,
        "matchCount": len(matched),
        "missingCount": len(missing),
    }
