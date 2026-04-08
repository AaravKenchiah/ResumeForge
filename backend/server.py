from urllib import error
from urllib.parse import quote

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.claude_tailor import generate_tailored_resume
from backend.export_resume import create_docx_bytes
from backend.gap_analysis import analyze_skill_gaps
from backend.github_ingestion import collect_github_profile
from backend.parse_resume import parse_resume_source
from backend.project_recommendations import generate_project_recommendations
from backend.scrape_jd import parse_job_description_source


app = FastAPI(title="ResumeForge API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def extract_http_error_detail(exc: error.HTTPError) -> str:
    """Read and flatten an HTTP error response body when available."""
    try:
        body = exc.read().decode("utf-8", errors="ignore").strip()
    except Exception:
        return ""

    return body.replace("\n", " ")[:500]


class TailorRequest(BaseModel):
    githubUsername: str = ""
    resumeText: str
    jobDescription: str


class ParseResumeRequest(BaseModel):
    resumeText: str = ""
    fileName: str = ""
    fileContentBase64: str = ""


class ParseJobDescriptionRequest(BaseModel):
    jobDescriptionText: str = ""
    jobDescriptionUrl: str = ""


class ExportDocxRequest(BaseModel):
    resumeText: str
    fileName: str = "tailored_resume.docx"


class ProjectRecommendationsRequest(BaseModel):
    githubUsername: str
    jobDescription: str


@app.get("/health")
def health_check():
    """Expose a lightweight liveness check for the frontend and local dev."""
    return {"status": "ok"}


@app.get("/github/{username}")
def preview_github_profile(username: str):
    """Return normalized GitHub project data for a public username."""
    try:
        return collect_github_profile(username=username, include_readmes=False)
    except error.HTTPError as exc:
        detail = "GitHub request failed."
        if exc.code == 404:
            detail = "GitHub user not found."
        elif exc.code == 403:
            detail = "GitHub API rate limit exceeded. Add GITHUB_TOKEN to .env and restart the backend."
        raise HTTPException(status_code=exc.code, detail=detail) from exc
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/parse-resume")
def parse_resume(payload: ParseResumeRequest):
    """Parse pasted resume text or uploaded file content into structure metadata."""
    try:
        return parse_resume_source(
            resume_text=payload.resumeText,
            file_name=payload.fileName,
            file_content_base64=payload.fileContentBase64,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc


@app.post("/parse-job-description")
def parse_job_description(payload: ParseJobDescriptionRequest):
    """Parse pasted job description text or fetch and clean it from a URL."""
    try:
        return parse_job_description_source(
            job_description_text=payload.jobDescriptionText,
            job_description_url=payload.jobDescriptionUrl,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except error.HTTPError as exc:
        detail = "Job description fetch failed."
        if exc.code == 403:
            detail = "The job posting blocked the request."
        elif exc.code == 404:
            detail = "Job posting URL not found."
        raise HTTPException(status_code=exc.code, detail=detail) from exc


@app.post("/tailor")
def tailor_resume(payload: TailorRequest):
    """Generate a tailored resume using parsed resume, GitHub, and job inputs."""
    github_summary = ""
    if payload.githubUsername:
        try:
            github_profile = collect_github_profile(username=payload.githubUsername)
            github_summary = github_profile["summary"]
        except error.HTTPError as exc:
            if exc.code in {403, 429}:
                try:
                    github_profile = collect_github_profile(
                        username=payload.githubUsername,
                        include_readmes=False,
                    )
                    github_summary = github_profile["summary"]
                except error.HTTPError:
                    github_summary = "GitHub summary unavailable."
            else:
                github_summary = "GitHub summary unavailable."

    try:
        parsed_resume = parse_resume_source(resume_text=payload.resumeText)
        parsed_job_description = parse_job_description_source(
            job_description_text=payload.jobDescription
        )
        tailored_resume = generate_tailored_resume(
            resume_text=parsed_resume["content"],
            resume_structure=parsed_resume["structure"],
            github_summary=github_summary,
            job_description=parsed_job_description["content"],
        )
        gap_analysis = analyze_skill_gaps(
            resume_text=parsed_resume["content"],
            job_description=parsed_job_description["content"],
            github_summary=github_summary,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except error.HTTPError as exc:
        detail = "Gemini request failed."
        if exc.code == 401:
            detail = "Invalid Gemini API key."
        elif exc.code == 429:
            detail = "Gemini API rate limit exceeded."
        elif exc.code == 403:
            detail = "Gemini API access denied."
        elif exc.code == 404:
            detail = "Gemini model not found or unavailable."

        body_detail = extract_http_error_detail(exc)
        if body_detail:
            detail = f"{detail} {body_detail}"
        raise HTTPException(status_code=502, detail=detail) from exc

    return {
        "tailoredResume": tailored_resume,
        "resumeStructure": parsed_resume["structure"],
        "githubSummary": github_summary,
        "cleanedJobDescription": parsed_job_description["content"],
        "gapAnalysis": gap_analysis,
    }


@app.post("/recommend-projects")
def recommend_projects(payload: ProjectRecommendationsRequest):
    """Rank GitHub projects and generate copy-ready bullets for the target role."""
    try:
        github_profile = collect_github_profile(username=payload.githubUsername)
        parsed_job_description = parse_job_description_source(job_description_text=payload.jobDescription)
        recommendations = generate_project_recommendations(
            github_profile=github_profile,
            job_description=parsed_job_description["content"],
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except error.HTTPError as exc:
        if exc.code in {401, 403, 404, 429} and "generativelanguage.googleapis.com" in exc.url:
            detail = "Gemini request failed."
            if exc.code == 401:
                detail = "Invalid Gemini API key."
            elif exc.code == 429:
                detail = "Gemini API rate limit exceeded."
            elif exc.code == 403:
                detail = "Gemini API access denied."
            elif exc.code == 404:
                detail = "Gemini model not found or unavailable."

            body_detail = extract_http_error_detail(exc)
            if body_detail:
                detail = f"{detail} {body_detail}"
            raise HTTPException(status_code=502, detail=detail) from exc

        detail = "GitHub request failed."
        if exc.code == 404:
            detail = "GitHub user not found."
        elif exc.code == 403:
            detail = "GitHub API rate limit exceeded. Add GITHUB_TOKEN to .env and restart the backend."
        raise HTTPException(status_code=exc.code, detail=detail) from exc

    return {
        "githubUsername": payload.githubUsername,
        "cleanedJobDescription": parsed_job_description["content"],
        "githubSummary": github_profile["summary"],
        "rankedProjects": recommendations,
    }


@app.post("/analyze-gaps")
def analyze_resume_gaps(payload: TailorRequest):
    """Analyze skill overlap between resume evidence and the job description."""
    github_summary = ""
    if payload.githubUsername:
        try:
            github_profile = collect_github_profile(username=payload.githubUsername)
            github_summary = github_profile["summary"]
        except error.HTTPError as exc:
            if exc.code in {403, 429}:
                try:
                    github_profile = collect_github_profile(
                        username=payload.githubUsername,
                        include_readmes=False,
                    )
                    github_summary = github_profile["summary"]
                except error.HTTPError:
                    github_summary = "GitHub summary unavailable."
            else:
                github_summary = "GitHub summary unavailable."

    try:
        parsed_resume = parse_resume_source(resume_text=payload.resumeText)
        parsed_job_description = parse_job_description_source(
            job_description_text=payload.jobDescription
        )
        return analyze_skill_gaps(
            resume_text=parsed_resume["content"],
            job_description=parsed_job_description["content"],
            github_summary=github_summary,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/export-docx")
def export_docx(payload: ExportDocxRequest):
    """Export tailored resume text as a DOCX document."""
    try:
        document_bytes = create_docx_bytes(payload.resumeText)
    except RuntimeError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc

    file_name = payload.fileName if payload.fileName.endswith(".docx") else f"{payload.fileName}.docx"
    encoded_name = quote(file_name)
    headers = {
        "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_name}",
    }
    return Response(
        content=document_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers=headers,
    )
