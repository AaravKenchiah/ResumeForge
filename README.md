# ResumeForge

ResumeForge is an AI-powered resume tailoring tool that uses a GitHub username, an existing resume, and a job description to generate a targeted resume while preserving the original structure and style.

## Environment Variables

```env
GEMINI_API_KEY=your_gemini_key_here
GEMINI_MODEL=gemini-2.5-pro
GITHUB_TOKEN=ghp_...
```

Notes:
- `GEMINI_API_KEY` is required for live tailoring through the backend
- `GITHUB_TOKEN` is optional and improves GitHub API rate limits
- see [.env.example](/Users/aaravkenchiah/Downloads/Resume:Person%20Projects/Resume%20Proj/ResumeBuilder/.env.example) for a starter file

## Project Structure

```text
ResumeBuilder/
├── README.md
├── roadmap.md
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── style.css
├── backend/
│   ├── server.py
│   ├── parse_resume.py
│   └── scrape_jd.py
└── prompts/
    └── tailor_prompt.txt
```

## First Milestone

This initial scaffold includes:
- a static frontend shell
- a FastAPI backend starter
- resume parsing and job scraping scaffolds
- a first draft of the tailoring system prompt
- GitHub ingestion helpers with unit tests

## GitHub Ingestion

The backend now includes a documented GitHub ingestion module at [backend/github_ingestion.py](/Users/aaravkenchiah/Downloads/Resume:Person%20Projects/Resume%20Proj/ResumeBuilder/backend/github_ingestion.py).

It currently supports:
- fetching a user's recent public repositories
- normalizing repo metadata into a prompt-friendly shape
- fetching README excerpts for non-fork repositories
- building a concise GitHub summary for resume tailoring

### API Endpoint

Run the backend and request:

```text
GET /github/{username}
```

Example response fields:
- `username`
- `repoCount`
- `repos`
- `summary`

The `POST /tailor` endpoint also now includes the GitHub summary when a username is provided.

## Resume Parsing

Resume parsing now lives in [backend/parse_resume.py](/Users/aaravkenchiah/Downloads/Resume:Person%20Projects/Resume%20Proj/ResumeBuilder/backend/parse_resume.py).

It currently supports:
- parsing pasted resume text
- decoding uploaded `.txt`, `.md`, and `.pdf` files
- extracting structure metadata with richer resume heuristics:
  - top-of-resume name and contact block detection
  - section order
  - grouped section content
  - inline section lines such as `Skills: Python, SQL`
  - title-case section headings such as `Technical Skills`
  - bullet style
  - date format
  - skills formatting

### API Endpoint

```text
POST /parse-resume
```

Accepted JSON fields:
- `resumeText`
- `fileName`
- `fileContentBase64`

Notes:
- send `resumeText` for pasted resumes
- send `fileName` plus base64-encoded file content for uploads
- PDF parsing requires the optional `pypdf` package in the backend environment
- the parser is tuned for dense SWE and student resume formats, but PDF extraction quality still depends on the source document text layer

## Job Description Ingestion

Job description ingestion now lives in [backend/scrape_jd.py](/Users/aaravkenchiah/Downloads/Resume:Person%20Projects/Resume%20Proj/ResumeBuilder/backend/scrape_jd.py).

It currently supports:
- cleaning pasted job description text
- fetching HTML from a job posting URL
- extracting JobPosting data from embedded JSON-LD when available
- targeting common job-description containers in HTML before falling back
- extracting visible job content from HTML as a last resort
- removing repeated boilerplate and common noise

### API Endpoint

```text
POST /parse-job-description
```

Accepted JSON fields:
- `jobDescriptionText`
- `jobDescriptionUrl`

Notes:
- send `jobDescriptionText` for pasted content
- send `jobDescriptionUrl` to fetch and clean a job posting page
- the backend now prefers structured metadata and likely description containers before generic page scraping
- some heavily client-rendered job sites may still work better with pasted text if the HTML response contains little usable content

## Gemini Integration

Gemini integration now lives in [backend/claude_tailor.py](/Users/aaravkenchiah/Downloads/Resume:Person%20Projects/Resume%20Proj/ResumeBuilder/backend/claude_tailor.py).

It currently supports:
- loading the system prompt from [prompts/tailor_prompt.txt](/Users/aaravkenchiah/Downloads/Resume:Person%20Projects/Resume%20Proj/ResumeBuilder/prompts/tailor_prompt.txt)
- building a deterministic user message from parsed resume data, GitHub summary, and cleaned job description
- sending requests to the Gemini REST API through a backend-only API key
- extracting text output from the Gemini response

### Tailoring Endpoint

```text
POST /tailor
```

The backend now:
- parses the resume input before prompt assembly
- cleans the job description before prompt assembly
- fetches GitHub project summaries when a username is provided
- sends the combined context to Gemini and returns the generated resume

Notes:
- `GEMINI_API_KEY` must be set in the backend environment
- API calls are performed server-side so the key is not exposed in frontend code

## Export and Rendering

The frontend rendering and export helpers now live in [frontend/rendering.js](/Users/aaravkenchiah/Downloads/Resume:Person%20Projects/Resume%20Proj/ResumeBuilder/frontend/rendering.js).

It currently supports:
- rendering tailored resume text into a cleaner on-page resume preview
- preserving line-based structure with headings and bullet lists
- downloading the generated result as Markdown
- exporting the generated result as DOCX through the backend
- exporting to PDF through the browser print flow with print-friendly styling

Notes:
- Markdown export downloads a `.md` file directly in the browser
- DOCX export uses the backend and requires `python-docx`
- PDF export opens the browser print dialog so the user can save as PDF
- the raw generated text is still shown below the rendered preview for transparency

## Frontend Workflow

The frontend workflow helpers now live in [frontend/workflow.js](/Users/aaravkenchiah/Downloads/Resume:Person%20Projects/Resume%20Proj/ResumeBuilder/frontend/workflow.js).

It currently supports:
- validation for GitHub fetch, resume parsing, JD parsing, and final tailoring
- request-state tracking for in-flight actions
- disabled buttons and loading labels during requests
- clearer form-level status messaging for success, loading, and error states

## Resume Diffing

The side-by-side diff helpers now live in [frontend/diffing.js](/Users/aaravkenchiah/Downloads/Resume:Person%20Projects/Resume%20Proj/ResumeBuilder/frontend/diffing.js).

It currently supports:
- line-level comparison between the original and tailored resume
- change summaries for added, removed, changed, and unchanged lines
- a side-by-side UI to make resume edits easier to review before export

## Skill Gap Analysis

Skill-gap analysis now lives in [backend/gap_analysis.py](/Users/aaravkenchiah/Downloads/Resume:Person%20Projects/Resume%20Proj/ResumeBuilder/backend/gap_analysis.py) and [frontend/gapAnalysis.js](/Users/aaravkenchiah/Downloads/Resume:Person%20Projects/Resume%20Proj/ResumeBuilder/frontend/gapAnalysis.js).

It currently supports:
- extracting common technical skill keywords from the job description
- comparing those keywords against resume and GitHub evidence
- highlighting matched and missing skills in the UI

## Local Run

Dependency manifests and startup helpers are now included:
- [requirements.txt](/Users/aaravkenchiah/Downloads/Resume:Person%20Projects/Resume%20Proj/ResumeBuilder/requirements.txt)
- [package.json](/Users/aaravkenchiah/Downloads/Resume:Person%20Projects/Resume%20Proj/ResumeBuilder/package.json)
- [scripts/start_backend.sh](/Users/aaravkenchiah/Downloads/Resume:Person%20Projects/Resume%20Proj/ResumeBuilder/scripts/start_backend.sh)
- [scripts/start_frontend.sh](/Users/aaravkenchiah/Downloads/Resume:Person%20Projects/Resume%20Proj/ResumeBuilder/scripts/start_frontend.sh)
- [LOCAL_SETUP.md](/Users/aaravkenchiah/Downloads/Resume:Person%20Projects/Resume%20Proj/ResumeBuilder/LOCAL_SETUP.md)

## Testing

Unit tests for GitHub ingestion live in [tests/test_github_ingestion.py](/Users/aaravkenchiah/Downloads/Resume:Person%20Projects/Resume%20Proj/ResumeBuilder/tests/test_github_ingestion.py).
Resume parsing tests live in [tests/test_parse_resume.py](/Users/aaravkenchiah/Downloads/Resume:Person%20Projects/Resume%20Proj/ResumeBuilder/tests/test_parse_resume.py).
Job description tests live in [tests/test_scrape_jd.py](/Users/aaravkenchiah/Downloads/Resume:Person%20Projects/Resume%20Proj/ResumeBuilder/tests/test_scrape_jd.py).
Gemini integration tests live in [tests/test_claude_tailor.py](/Users/aaravkenchiah/Downloads/Resume:Person%20Projects/Resume%20Proj/ResumeBuilder/tests/test_claude_tailor.py).
Gap analysis tests live in [tests/test_gap_analysis.py](/Users/aaravkenchiah/Downloads/Resume:Person%20Projects/Resume%20Proj/ResumeBuilder/tests/test_gap_analysis.py).
DOCX export tests live in [tests/test_export_resume.py](/Users/aaravkenchiah/Downloads/Resume:Person%20Projects/Resume%20Proj/ResumeBuilder/tests/test_export_resume.py).
API tests live in [tests/test_server.py](/Users/aaravkenchiah/Downloads/Resume:Person%20Projects/Resume%20Proj/ResumeBuilder/tests/test_server.py).
Frontend rendering tests live in [tests/frontend/rendering.test.js](/Users/aaravkenchiah/Downloads/Resume:Person%20Projects/Resume%20Proj/ResumeBuilder/tests/frontend/rendering.test.js).
Frontend workflow tests live in [tests/frontend/workflow.test.js](/Users/aaravkenchiah/Downloads/Resume:Person%20Projects/Resume%20Proj/ResumeBuilder/tests/frontend/workflow.test.js).
Frontend diffing tests live in [tests/frontend/diffing.test.js](/Users/aaravkenchiah/Downloads/Resume:Person%20Projects/Resume%20Proj/ResumeBuilder/tests/frontend/diffing.test.js).
Frontend gap-analysis tests live in [tests/frontend/gapAnalysis.test.js](/Users/aaravkenchiah/Downloads/Resume:Person%20Projects/Resume%20Proj/ResumeBuilder/tests/frontend/gapAnalysis.test.js).

Run them with:

```bash
python -m unittest tests/test_github_ingestion.py tests/test_parse_resume.py tests/test_scrape_jd.py tests/test_claude_tailor.py tests/test_gap_analysis.py tests/test_export_resume.py tests/test_server.py
node --test tests/frontend/rendering.test.js tests/frontend/workflow.test.js tests/frontend/diffing.test.js tests/frontend/gapAnalysis.test.js
```

## Updated Next Steps

1. Add more robust deployment artifacts such as Docker or hosted environment configs.
2. Improve skill-gap extraction with role-specific keyword dictionaries or semantic matching.
3. Add persistent saved sessions or export history.
4. Add optional cover-letter generation.
