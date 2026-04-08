# Local Setup

## Prerequisites

- Python 3.10+
- Node.js 18+

## 1. Create a Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 2. Install Backend Dependencies

```bash
pip install -r requirements.txt
```

## 3. Configure Environment Variables

```bash
cp .env.example .env
```

Set:
- `GEMINI_API_KEY` for live resume tailoring
- `GEMINI_MODEL` optionally, defaulting to `gemini-2.5-pro`
- `GITHUB_TOKEN` optionally for higher GitHub API rate limits

## 4. Start the Backend

Option A:

```bash
python3 -m uvicorn backend.server:app --reload --host 127.0.0.1 --port 8000
```

Option B:

```bash
./scripts/start_backend.sh
```

## 5. Start the Frontend

Option A:

```bash
python3 -m http.server 4173 -d frontend
```

Option B:

```bash
./scripts/start_frontend.sh
```

## 6. Open the App

Open:

```text
http://127.0.0.1:4173
```

## Useful Commands

Run backend tests:

```bash
python -m unittest tests/test_github_ingestion.py tests/test_parse_resume.py tests/test_scrape_jd.py tests/test_claude_tailor.py tests/test_gap_analysis.py tests/test_export_resume.py tests/test_server.py
```

Run frontend tests:

```bash
node --test tests/frontend/rendering.test.js tests/frontend/workflow.test.js tests/frontend/diffing.test.js tests/frontend/gapAnalysis.test.js
```

Or with package scripts:

```bash
npm run test:frontend
```

## Notes

- PDF parsing requires `pypdf`
- DOCX export requires `python-docx`
- The frontend is static and talks directly to the FastAPI backend on `http://127.0.0.1:8000`
