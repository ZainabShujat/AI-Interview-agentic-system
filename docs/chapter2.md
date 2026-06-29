# 📖 HireIntel Product Bible

## Chapter 2: User Journey & Product Workflow

This chapter maps out the end-to-end candidate and recruiter user journey, identifying where each AI agent enters the workflow.

---

## 1. Recruiter Onboarding & Dashboard Ingestion

### Recruiter Landing (Recruiter OS)
*   **Recruiter Experience**: Recruiter logs in and sees a dynamic personalized greeting (derived from session metadata) and a Demo Notice banner explaining that preloaded lists represent mock candidates.
*   **Action**: The recruiter initiates candidate ingestion by dragging and dropping a Resume PDF.

### Ingestion Flow (Resume Intelligence Agent)
*   **System Action**:
    1.  **Cache Verification**: The system hashes the raw file text. If a database cache match is found, it loads the parsed JSON instantly.
    2.  **Name Extraction (Heuristics $\rightarrow$ Fallback)**: The agent scans the top 8 lines of raw text, skipping certification labels and job titles. If not found, it parses the file name.
    3.  **Entity Regex Extraction**: Scans contact details (emails, phone numbers) and links using regex libraries.
    4.  **Semantic Enrichment**: The Gemini Flash engine extracts career domains, highlights, potential concerns, and academic timelines.
    5.  **Telemetry & Reliability Logging**: Computes reliability classifications (`High`, `Medium`, `Low`) and logs tokens and costs.

---

## 2. Capability Screening & Job Mapping

### Role Definition (JD Intelligence Agent)
*   **Action**: Recruiter creates a hiring role by pasting job description details.
*   **System Action**: The JD Agent extracts required skills, preferred qualifications, seniority, and target experience years to compile a standard hiring blueprint database record.

### Compatibility Analysis (Readiness Match Agent)
*   **Action**: Recruiter links the candidate's resume to the target Job Description blueprint.
*   **System Action**:
    1.  **Deterministic Weight Matching**: Calculates skill coverage (70% weight for required skills, 20% weight for preferred skills) and domain overlap (10% weight).
    2.  **Logic Explainability**: Compiles success checkmarks ($\checkmark$) and warning flags ($\triangle$) detailing *why* the score was achieved.
    3.  **Domain Derivation**: Evaluates candidate skill keywords to justify the primary domain (e.g. `↳ Why? Detected from: React, Next.js`).

---

## 3. Invited Candidate Assessment Session

### Assessment Start (Interview Simulator Agent)
*   **Action**: Recruiter sends an assessment link, generating a unique token. The candidate opens the assessment.
*   **System Action**: The Interview Agent reads the candidate's screening gaps and schedules a gap-targeted category roadmap (Technical, Scenario, Behavioral, Leadership).

### Adaptive Q&A & Vocal Telemetry (Judge Agent)
*   **Action**: Candidate records answers to questions.
*   **System Action**:
    1.  **Adaptive Difficulty**: Escalates or reduces question difficulty level based on the accuracy of the candidate's previous response.
    2.  **Vocal Signal Analytics**: Tracks speaking latency, WPM, filler word count, and word lengths.
    3.  **Rubric Evaluation**: The Judge Agent evaluates responses against Accuracy, Depth, and STAR framework rubrics.

---

## 4. Evaluation Report & Upskilling roadmap

### Scorecard Compilation (Report Agent)
*   **Action**: Recruiter opens the candidate's completed evaluation profile.
*   **System Action**: The Report Agent aggregates all interview logs, computes average category ratings, and prepares data structures for frontend analytics charts.

### Personalized Learning (Career Roadmap Agent)
*   **Action**: Candidate receives study guidelines based on their interview results.
*   **System Action**: The Roadmap Agent reviews candidate gaps and generates weekly learning milestones and target bridge projects.
