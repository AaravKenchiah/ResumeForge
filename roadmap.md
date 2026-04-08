# ResumeForge Roadmap

## Vision

Build an AI-powered resume tailoring tool that takes a GitHub username, an existing resume, and a job description, then produces a customized resume that preserves the user's original structure and style while aligning content to the target role.

## Product Goal

ResumeForge should help users generate a role-specific resume quickly, accurately, and without fabricating experience. The core value is combining real project evidence from GitHub, real resume history from an uploaded file, and real hiring signals from a job description into one tailored output.

## Core Scope

### Inputs
- GitHub username
- Existing resume as PDF or plain text
- Job description as pasted text or URL

### Outputs
- Tailored resume content
- Optional missing-skill or gap notes
- Exportable result in Markdown and PDF

### Core Functional Requirements
- Fetch public GitHub repositories, metadata, languages, and optional READMEs
- Parse resume text and infer structure separately from content
- Ingest a job description from pasted text or a scraped URL
- Generate a tailored resume using Claude
- Preserve original resume section order, formatting conventions, and tone
- Display results in a clean UI with copy and download actions

## Development Phases

## Phase 1: Foundation

### Goal
Set up the base project structure and get a minimal end-to-end flow working.

### Deliverables
- Initialize frontend app
- Create optional backend scaffold
- Add environment variable handling
- Add prompt file structure
- Define shared data models for:
  - resume content
  - resume structure
  - GitHub project summaries
  - job description text
  - tailored resume output

### Success Criteria
- Project runs locally
- Frontend can collect all three user inputs
- Backend can accept requests if server-side mode is enabled

## Phase 2: GitHub Integration

### Goal
Turn a GitHub username into meaningful project context for tailoring.

### Deliverables
- Fetch recent public repos via GitHub REST API
- Extract repo name, description, language, topics, and updated date
- Optionally fetch README content for top repositories
- Summarize project relevance and tech stack for AI input
- Handle empty accounts, rate limits, and missing READMEs gracefully

### Success Criteria
- User can enter a GitHub username and preview fetched projects
- App produces a concise GitHub summary suitable for prompting Claude

## Phase 3: Resume Parsing

### Goal
Extract both resume text and formatting structure from uploaded files.

### Deliverables
- Support PDF upload
- Support plain text input or upload
- Extract resume text client-side or server-side
- Detect section headings and section order
- Infer formatting patterns such as:
  - bullet style
  - date format
  - heading style
  - grouped vs inline skills format
- Separate parsed output into:
  - content representation
  - structure representation

### Success Criteria
- Parsed resume data reflects both what the resume says and how it is organized
- The app can pass structure metadata to the AI prompt

## Phase 4: Job Description Ingestion

### Goal
Support both pasted job descriptions and URL-based extraction.

### Deliverables
- Add job description text area
- Add optional URL input
- Scrape and clean job posting text on the backend
- Remove boilerplate and navigation noise where possible
- Normalize the job description into a clean prompt-ready format

### Success Criteria
- User can provide job description text directly or by URL
- Extracted text is readable and useful for model prompting

## Phase 5: AI Tailoring Engine

### Goal
Generate a high-quality tailored resume while preserving the original format.

### Deliverables
- Create `prompts/tailor_prompt.txt`
- Integrate Anthropic Messages API
- Build prompt assembly pipeline using:
  - original resume text
  - resume structure data
  - GitHub project summary
  - cleaned job description
- Add strong prompt rules for:
  - preserving section names and order
  - preserving formatting conventions
  - factual accuracy
  - no fabricated experience
  - keyword alignment to the job description
- Add optional gap-highlighting output

### Success Criteria
- App returns a tailored resume that matches the original structure
- Output emphasizes relevant experience and projects without inventing facts

## Phase 6: Output Rendering and Export

### Goal
Let users review, copy, and export the tailored resume easily.

### Deliverables
- Render tailored resume in a readable layout
- Add copy-to-clipboard action
- Add Markdown download
- Add PDF export
- Preserve formatting as closely as possible to the original resume
- Provide simple before-and-after visibility if feasible

### Success Criteria
- User can review and export their tailored resume in at least one portable format

## Phase 7: Quality, Reliability, and UX

### Goal
Make the experience stable, understandable, and safe for real users.

### Deliverables
- Loading states and error handling across the full flow
- Validation for missing or invalid inputs
- Retry guidance for GitHub and AI API failures
- Clear warnings around privacy and API key usage
- Security improvement by moving API keys server-side
- Friendly explanations when some inputs cannot be parsed

### Success Criteria
- Users can complete the workflow without confusion
- Failures are actionable and do not break the app silently

## Phase 8: Post-MVP Enhancements

### Goal
Expand ResumeForge beyond the first release.

### Potential Deliverables
- DOCX export via `python-docx`
- Side-by-side diff view
- ATS keyword score before and after tailoring
- Cover letter generation
- LinkedIn profile ingestion
- Saved tailoring history
- Multiple resume templates
- User authentication and saved sessions

## MVP Definition

The first shippable version should include:
- GitHub username input
- Resume upload or paste
- Job description paste
- Claude-powered tailored resume generation
- Preservation of original section order and formatting style
- Copy and Markdown export

## Suggested Technical Milestones

### Milestone 1
- Set up frontend and backend structure
- Implement base UI for inputs

### Milestone 2
- Finish GitHub data ingestion
- Finish resume parsing flow

### Milestone 3
- Finish pasted job description support
- Integrate Claude API and prompt pipeline

### Milestone 4
- Render tailored resume output
- Add export actions

### Milestone 5
- Polish UX, validation, and edge-case handling
- Prepare MVP for demo or deployment

## Risks and Considerations

- Resume structure extraction may be inconsistent across PDF formats
- GitHub repos may not always reflect the user's strongest work
- Job posting pages may block scraping or include noisy content
- AI output quality will depend heavily on prompt design and input cleanup
- Exposing the Anthropic API key in frontend code is not safe for production

## Build Priorities

### Highest Priority
- Reliable input collection
- Resume parsing
- Strong prompt construction
- Format-preserving tailored output

### Medium Priority
- URL-based job scraping
- PDF export fidelity
- Gap analysis

### Lower Priority
- DOCX export
- Diff view
- ATS scoring
- LinkedIn support

## Definition of Done

ResumeForge is ready for MVP when:
- A user can input a GitHub username, resume, and job description
- The app produces a tailored resume in one flow
- The tailored output keeps the same section order and style as the original
- The system does not fabricate facts
- The user can copy or export the result
