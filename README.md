# ResumeForge

ResumeForge is a GitHub-project targeting tool for resume editing.

![ResumeForge preview](docs/assets/resumeforge-preview.svg)

Live Demo: currently local-only. Run the backend and frontend with the included scripts, then open `http://127.0.0.1:4173`.

Instead of trying to generate a full one-page resume, the app now:
- fetches a user's recent GitHub repositories
- cleans a pasted or URL-based job description
- ranks the repositories from most relevant to least relevant for the role
- generates 3 to 4 copy-pasteable resume bullets for each ranked project

The goal is simple: help you decide which projects belong on your resume and give you strong, role-aligned bullets you can paste in manually.

## Current Workflow

1. Enter a GitHub username.
2. Paste a job description or fetch one from a job-posting URL.
3. Click `Fetch Projects` to preview recent repos.
4. Click `Rank Projects + Draft Bullets` to get ranked project recommendations and resume-ready bullets.
5. Copy the bullets you want into your actual resume.

## What The App Does Now

### GitHub project ingestion

GitHub ingestion lives in [`backend/github_ingestion.py`](backend/github_ingestion.py).

It supports:
- fetching a user's recent public repositories
- normalizing repo metadata for prompt use
- optionally fetching README excerpts for richer project evidence
- building concise project summaries for preview and Gemini prompting

Preview endpoint:

```text
GET /github/{username}
```

Notes:
- the preview route skips README fetches to reduce GitHub rate-limit pressure
- adding `GITHUB_TOKEN` to `.env` improves reliability when hitting the GitHub API repeatedly

### Job description parsing

Job description parsing lives in [`backend/scrape_jd.py`](backend/scrape_jd.py).

It supports:
- pasted job description text
- job-posting URLs
- HTML cleanup and boilerplate removal
- extracting likely description content from common page structures

Endpoint:

```text
POST /parse-job-description
```

Accepted JSON fields:
- `jobDescriptionText`
- `jobDescriptionUrl`

### Project ranking and bullet generation

The ranking flow lives in [`backend/project_recommendations.py`](backend/project_recommendations.py).

It uses Gemini to:
- compare GitHub repo evidence against the target role
- rank repos from most relevant to least relevant
- write 3 to 4 concise bullets for each project
- keep bullets grounded in repo metadata and README evidence
- avoid inventing tools, outcomes, or metrics

Prompt:
- [`prompts/project_bullets_prompt.txt`](prompts/project_bullets_prompt.txt)

Endpoint:

```text
POST /recommend-projects
```

Accepted JSON fields:
- `githubUsername`
- `jobDescription`

Example response fields:
- `githubUsername`
- `cleanedJobDescription`
- `githubSummary`
- `rankedProjects`

Each ranked project includes:
- `rank`
- `name`
- `relevanceSummary`
- `language`
- `url`
- `description`
- `bullets`

### Frontend UI

The frontend is a static app in [`frontend/index.html`](frontend/index.html) with behavior in [`frontend/app.js`](frontend/app.js).

It supports:
- GitHub username input and repo preview
- pasted or URL-fetched job descriptions
- ranked project cards
- per-project bullet copying
- copy-all output for quick resume editing

Rendering helpers live in [`frontend/rendering.js`](frontend/rendering.js).
Validation and request-state helpers live in [`frontend/workflow.js`](frontend/workflow.js).

## Environment Variables

```env
GEMINI_API_KEY=your_gemini_key_here
GEMINI_MODEL=gemini-flash-latest
GITHUB_TOKEN=ghp_...
```

Notes:
- `GEMINI_API_KEY` is required for ranked project bullets
- `GEMINI_MODEL` defaults to `gemini-flash-latest`
- `GITHUB_TOKEN` is optional but strongly recommended for higher GitHub API rate limits
- see [`.env.example`](.env.example) for a starter file

## Local Run

Dependency manifests and startup helpers:
- [`requirements.txt`](requirements.txt)
- [`package.json`](package.json)
- [`scripts/start_backend.sh`](scripts/start_backend.sh)
- [`scripts/start_frontend.sh`](scripts/start_frontend.sh)
- [`LOCAL_SETUP.md`](LOCAL_SETUP.md)

Backend:

```bash
./scripts/start_backend.sh
```

Frontend:

```bash
./scripts/start_frontend.sh
```

Open:

```text
http://127.0.0.1:4173
```

Backend API:

```text
http://127.0.0.1:8000
```

## Testing

Backend tests:

```bash
python -m unittest tests/test_github_ingestion.py tests/test_parse_resume.py tests/test_scrape_jd.py tests/test_claude_tailor.py tests/test_gap_analysis.py tests/test_export_resume.py tests/test_project_recommendations.py tests/test_server.py
```

Frontend tests:

```bash
node --test tests/frontend/rendering.test.js tests/frontend/workflow.test.js tests/frontend/diffing.test.js tests/frontend/gapAnalysis.test.js
```

## Notes

- Resume parsing and the older tailoring/export helpers still exist in the codebase, but the product direction is now centered on ranked GitHub projects and manual resume editing.
- If GitHub preview fails with a rate-limit message, add a real `GITHUB_TOKEN` to `.env` and restart the backend.
- Gemini calls are made server-side so the API key is not exposed in frontend code.
- The GitHub remote may still be named `ResumeBuilder`; renaming the GitHub repository itself to `ResumeForge` is the last public-facing cleanup step to do on GitHub.
