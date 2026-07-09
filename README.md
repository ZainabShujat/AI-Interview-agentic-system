# HireIntel

Agentic hiring platform that screens candidates with adaptive AI interviews and evidence-backed reports.

Recruiters create role blueprints, parse candidates, run adaptive interviews, rank applicants, and review full diagnostic reports. Students can self-assess against a target job and see where they rank.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                             │
│  React 18 · Vite · Recharts · Framer Motion · Dark mode     │
│  localhost:3000                                              │
├─────────────────────────────────────────────────────────────┤
│                        Backend                              │
│  FastAPI · SQLite · Gemini 2.5 Flash · PyMuPDF              │
│  localhost:8000                                              │
├─────────────────────────────────────────────────────────────┤
│                      TypeScript SDK                         │
│  @hireintel/sdk · Zero deps · ESM + CJS                     │
│  packages/sdk/                                               │
└─────────────────────────────────────────────────────────────┘
```

## AI Agents & Workflow

The platform operates through an orchestrated network of specialized AI agents, categorized into four distinct modules (`Organized-Agents/`):

### 1. Pre-Interview Screening (`1_Pre_Interview_Screening/`)
- **Resume Agent (`resume_agent.py`)**: Extracts candidate metadata, skills, experience, and projects from uploaded files (PDF/DOCX/TXT).
- **JD Agent (`jd_agent.py`)**: Parses job descriptions and converts them into structured hiring blueprints, isolating required skills, experience levels, and core competencies.
- **Match Agent (`match_agent.py`)**: Takes the outputs from the Resume and JD agents to perform a deterministic skill-gap analysis, providing explainable justifications (matched vs. gaps) to assess candidate readiness.

### 2. Evaluation and Reporting (`2_Evaluation_and_Reporting/`)
- **Judge Agent (`judge_agent.py`)**: Evaluates the candidate's answers in real-time or post-interview, scoring them on accuracy, depth, communication, and problem-solving.
- **Report Agent (`report_agent.py`)**: Aggregates the evaluations from the Judge Agent to compile a comprehensive performance report, including scores, visual charts, transcript reviews, and a final Hire/No Hire recommendation.

### 3. Planning and Roadmap (`3_Planning_and_Roadmap/`)
- **Planner Agent (`planner_agent.py`)**: Acts as the interview architect. It uses the JD blueprint to map out a structured category roadmap (e.g., Technical → Scenario → Behavioral → Leadership) before the interview begins.
- **Roadmap Agent (`roadmap_agent.py`)**: Used primarily for students and candidates to generate a personalized career and skill development plan based on their readiness gaps.

### 4. Full Automated Interviewer (`4_Full_Automated_Interviewer/`)
- **Gemini Core (`gemini_core.py`)**: The central intelligence engine that interfaces with the Google Gemini API, powering the reasoning capabilities of all other agents.
- **Memory Agent (`memory_agent.py`)**: Tracks the state of the interview, keeping a record of demonstrated strengths, weak areas, and previous answers to provide context for follow-up questions.
- **Interview Agent (`interview_agent.py`)**: The dynamic host of the interview. It reads the Planner's roadmap and Memory's context to generate adaptive questions and follow-ups. It integrates with external tools (like Zoom for meeting creation and Gmail for automated email dispatch) to run a fully autonomous, end-to-end interview experience.

### How They Link Together:
1. **Intake**: A recruiter uploads a JD and a Resume. The **JD Agent** and **Resume Agent** parse the documents.
2. **Screening**: The **Match Agent** evaluates the parsed data to determine if the candidate meets the baseline requirements.
3. **Preparation**: If approved, the **Planner Agent** outlines an interview structure based on the JD.
4. **Execution**: The **Interview Agent** conducts the interview (via Zoom/Gmail integration), while the **Memory Agent** tracks the flow.
5. **Grading**: The **Judge Agent** evaluates each response provided to the Interview Agent.
6. **Finalization**: The **Report Agent** compiles the Judge's scores into a final diagnostic PDF report for the recruiter.

## Project Structure

```
├── backend/                  # FastAPI server
│   ├── main.py               # App entry point + middleware
│   ├── models.py             # SQLAlchemy models (Resume, JD, Interview, Answer, Report)
│   ├── schemas.py            # Pydantic request/response schemas
│   ├── middleware.py          # API key authentication
│   ├── routers/
│   │   ├── resume_router.py   # Resume upload + parsing
│   │   ├── jd_router.py       # JD text/file parsing + blueprint editing
│   │   ├── match_router.py    # Deterministic match by ID or raw JSON
│   │   ├── interview_router.py # Start, answer, report, judge, PDF export
│   │   └── roadmap_router.py  # Career roadmap generation
│   └── services/
│       ├── gemini_service.py  # All AI agent logic
│       ├── pdf_service.py     # Report PDF generation
│       └── speech_service.py  # Vocal telemetry analysis
│
├── frontend/                 # React + Vite client
│       ├── pages/
│       │   ├── Landing.tsx     # Marketing landing page
│       │   ├── Login.tsx       # Role-based login (student / recruiter)
│       │   ├── Dashboard.tsx   # Recruiter OS workspace
│       │   ├── Upload.tsx      # Resume + JD upload with ATS preview
│       │   ├── MatchAnalysis.tsx # Readiness match with gap analysis
│       │   ├── Interview.tsx   # Live adaptive interview UI
│       │   ├── Report.tsx      # Full diagnostic report with charts
│       │   ├── StudentAssessment.tsx # Student self-assessment flow
│       │   ├── RoleReadiness.tsx # Student readiness dashboard
│       │   └── JobLeaderboard.tsx # Candidate ranking by job
│       └── components/         # Shared UI components
│
├── packages/
│   └── sdk/                  # @hireintel/sdk TypeScript SDK
│       ├── src/
│       │   ├── client.ts      # HireIntel main class
│       │   ├── types.ts       # Full TypeScript interfaces
│       │   ├── errors.ts      # Typed error hierarchy
│       │   ├── http.ts        # Fetch wrapper with retries + interceptors
│       │   └── api/           # resumes, jds, match, interview, reports, judge, roadmap
│       ├── examples/
│       │   └── quickstart.ts  # End-to-end pipeline example
│       └── README.md
│
├── agent-playground/         # Standalone agent sandbox HTML
└── docs/                     # Product Bible (chapters 1–6), architecture, roadmap
```

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- A Gemini API key

### 1. Backend

```bash
cd backend
pip install -r requirements.txt

# Create .env with your Gemini key
echo "GEMINI_API_KEY=your-key-here" > .env

python main.py
# Server starts on http://localhost:8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
# Dev server starts on http://localhost:3000
```

### 3. SDK (optional)

```bash
cd packages/sdk
npm install
npm run build
```

```typescript
import { HireIntel } from '@hireintel/sdk';

const client = new HireIntel({ baseUrl: 'http://localhost:8000' });

const resume = await client.resumes.parse(pdfBuffer, { filename: 'cv.pdf' });
const jd     = await client.jds.create({ text: 'Senior Python Engineer...' });
const match  = await client.match.evaluate(resume.id, jd.id);

console.log(match.matchScore);       // 82
console.log(match.justifications);   // [{ type: 'success', text: '...' }]
```

## Authentication

The backend supports API key authentication via the `X-API-Key` header.

| Environment | Behavior |
|-------------|----------|
| `HIREINTEL_API_KEY` **not set** | Auth disabled — all requests pass through (dev mode) |
| `HIREINTEL_API_KEY` **set** | Every request must include a matching `X-API-Key` header |

Health check (`GET /`), OpenAPI docs (`/docs`), and CORS preflight requests are always open.

## API Documentation

With the backend running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Key Features

**Resume Parser**
- PDF, DOCX, TXT support via PyMuPDF
- Hybrid extraction: Gemini LLM + local regex heuristics
- SHA-256 content caching — duplicate uploads return instantly
- Filename fallback for candidate name when parsing fails

**Match Engine**
- Deterministic scoring — no LLM randomness in the match score
- Explainable justifications (✓ matched, △ gap) for every skill
- Auto-generates an assessment blueprint for the interview planner

**Adaptive Interview**
- Category roadmap: Technical → Scenario → Behavioral → Leadership
- Difficulty adapts based on weighted average of last 2 answers
- Follow-up state machine — probes shallow answers up to 2 times
- Memory agent tracks demonstrated strengths and weak areas

**Judge Agent**
- Scores accuracy, depth, communication, problem-solving
- Analyzes confidence signals (WPM, filler words, response latency)

**Reports**
- Performance breakdown by category with Recharts visualizations
- Overall score, recommendation (Hire / No Hire / Maybe)
- Full interview transcript with per-answer evaluation
- PDF export

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript, Vite, Recharts, Framer Motion, Lucide Icons |
| Backend | Python 3.10+, FastAPI, SQLAlchemy, SQLite, PyMuPDF |
| AI | Google Gemini 2.5 Flash |
| SDK | TypeScript, tsup (ESM + CJS), zero runtime dependencies |
| Styling | Tailwind CSS, CSS custom properties, dark/light theme |

## License

All rights reserved. This software is proprietary and confidential.