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

## AI Agents

| Agent | What it does | Endpoint |
|-------|-------------|----------|
| **Resume Intelligence** | Extracts candidate metadata, skills, experience, projects from PDF/DOCX/TXT | `POST /api/resume` |
| **JD Intelligence** | Parses job descriptions into structured hiring blueprints | `POST /api/jd` |
| **Readiness Match** | Deterministic skill-gap analysis with explainable justifications | `POST /api/match` |
| **Interview Planner** | Plans category roadmap (Technical → Scenario → Behavioral → Leadership) | `POST /api/interview/start` |
| **Adaptive Interview** | Generates follow-up questions based on previous answers, difficulty adapts | `POST /api/interview/answer` |
| **Judge** | Evaluates answers for accuracy, depth, communication, problem-solving | `POST /api/interview/judge` |
| **Report** | Compiles performance report with scores, recommendations, and transcripts | `GET /api/interview/report` |
| **Career Roadmap** | Generates personalized skill development plans | `POST /api/roadmap` |

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