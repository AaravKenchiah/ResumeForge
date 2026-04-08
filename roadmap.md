# ResumeForge Roadmap

## Product Direction

ResumeForge is no longer trying to output a fully formatted final resume.

The current north star is:
- help users identify which GitHub projects best match a role
- generate strong project bullets they can manually place into their resume
- evolve into a real tool that strangers can use, not just a one-off demo

## Current Product

Today the app can:
- fetch recent public GitHub repositories for a username
- preview lightweight repo summaries
- parse job descriptions from pasted text or a URL
- rank repositories against a target role with Gemini
- generate 3 to 4 copy-pasteable bullets per project
- let users copy bullets individually or in bulk from the frontend

## Immediate Priorities

### 1. Deploy the product

Highest priority.

Goal:
- make ResumeForge accessible without local setup

Suggested path:
- deploy the FastAPI backend to Render
- deploy the static frontend to Vercel
- add a real live-demo link to the README

Success criteria:
- a recruiter can click from GitHub to a working public demo
- pushes to `main` update the deployed app

### 2. Add a resume-JD match score

Goal:
- show whether the user's resume evidence is actually moving closer to the job description

Initial approach:
- keyword overlap
- weighted skill matching
- TF-IDF style scoring for role-specific terms

Success criteria:
- the UI shows a clear 0-100 style score
- users can see before/after improvement

### 3. Upgrade skill-gap analysis

Goal:
- move beyond exact keyword matching

Suggested approach:
- semantic matching with `sentence-transformers`
- lightweight model such as `all-MiniLM-L6-v2`

Success criteria:
- related phrases can match even without exact wording overlap
- the missing-skill output feels materially smarter than string matching

## Secondary Priorities

### 4. Add lightweight usage analytics

Goal:
- measure whether people actually use the product

Options:
- Plausible
- CountAPI
- a simple backend event counter

Success criteria:
- track visits and recommendation runs
- gather real usage numbers for product credibility

### 5. Improve README presentation

Goal:
- make the repository read like a product page

Deliverables:
- real UI screenshot or GIF
- live-demo badge
- concise feature and stack sections
- tighter public-facing copy

Success criteria:
- the first screen of the README explains the product quickly
- a recruiter can understand value without digging

## Future Product Features

### Match and analysis improvements

- project confidence score or explanation quality scoring
- stronger evidence extraction from README text
- semantic clustering of job requirements
- better handling for sparse or poorly documented repos

### UX improvements

- save recommendation sessions locally
- let users pin favorite projects
- export selected bullets as markdown snippets
- show why one repo outranked another

### Platform improvements

- background caching for GitHub lookups
- better GitHub rate-limit visibility
- deployment configuration in-repo
- analytics dashboards

## Risks

- GitHub rate limits can still affect users without a token
- repo quality varies heavily depending on README quality and metadata
- JD scraping can fail on heavily client-rendered or blocked job pages
- ranking quality depends on the quality of the repo evidence available

## Definition of Success

ResumeForge is in a strong public state when:
- it is deployed
- the README has a real demo link and product visuals
- users can rank projects against a role end to end
- the app surfaces useful bullet suggestions quickly
- the analysis output is strong enough that users trust it and keep editing from it
