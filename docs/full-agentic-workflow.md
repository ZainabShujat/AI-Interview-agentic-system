# Full Autonomous Multi-Agent Workflow

This document details the complete end-to-end multi-agent orchestration pipeline, spanning from the initial document upload, through the capability screening, the interactive audio interview, and finally to the downstream human handoff.

---

## Stage 1: Ingestion & Parsing
The workflow begins when the recruiter or system provides a Job Description and a Candidate's Resume. These raw text inputs are sent to two specialized intelligence agents.

### 1. JD Intelligence Agent (`/api/jd`)
*   **Role:** Analyzes the raw Job Description.
*   **Action:** Extracts core requirements, preferred skills, seniority levels, and target experience years.
*   **Output:** Generates a structured JSON "Hiring Blueprint" which acts as the absolute truth for all subsequent evaluations.

### 2. Resume Intelligence Agent (`/api/resume`)
*   **Role:** Analyzes the candidate's PDF or text resume.
*   **Action:** Uses heuristics and LLM semantic enrichment to extract the candidate's contact details, career domains, technical skills, highlights, and potential experience gaps.
*   **Output:** Generates a structured JSON "Candidate Profile".

---

## Stage 2: Capability Screening
Once both documents are parsed into structured data, the system evaluates if the candidate is fundamentally suited for an interview.

### 3. Readiness Match Agent (`/api/match/raw`)
*   **Role:** Compares the Candidate Profile against the Hiring Blueprint.
*   **Action:** Performs deterministic weighted matching. Required skills carry a 70% weight, preferred skills 20%, and domain overlap 10%.
*   **Output:** Calculates a final **Readiness Score (0-100)**. Crucially, it provides logic explainability by generating specific success checkmarks ($\checkmark$) and warning flags ($\triangle$) detailing *why* the candidate is missing certain requirements. These gaps are passed directly to the Interview Planner.

---

## Stage 3: The Adaptive Interview (Audio/Text)
If the candidate clears the readiness check, they are invited to the autonomous interview session.

### 4. Interview Simulator Agent (`/api/interview/start`)
*   **Role:** Plans and initiates the interview.
*   **Action:** Reads the screening gaps ($\triangle$) identified by the Match Agent and generates a targeted roadmap of categories (Technical, Behavioral, Scenario).
*   **Output:** Generates the very first targeted question to begin the session.

### 5. Audio Transcription & Telemetry (`/api/interview/audio-answer`)
*   **Role:** Processes the candidate's live spoken answer.
*   **Action:** The raw microphone audio (`.wav`) is streamed to the backend. The **Deepgram Speech Service** transcribes it with sub-second latency. Simultaneously, the **OpenSMILE Acoustic Analyzer** extracts vocal telemetry like `speakingRate` and `jitter` (confidence metrics).
*   **Output:** A high-fidelity text transcript coupled with rich acoustic signals.

### 6. Judge & Memory Agents (The Evaluation Loop)
*   **Role:** Evaluates the candidate's answer and adapts the interview state.
*   **Action:** 
    1.  The **Judge Agent** grades the transcribed answer against strict rubrics: Accuracy, Depth, and Communication (augmented by the acoustic telemetry).
    2.  The **Memory Agent** updates the candidate's profile with newly demonstrated competencies or persistent weaknesses.
    3.  If the Judge Agent scores `depth` or `communication` poorly, the orchestrator triggers a follow-up loop to probe deeper. Otherwise, it adapts the difficulty (Easy/Medium/Hard) based on the trailing average score and moves to the next category.
*   **Output:** The next adaptive question, returning to Step 5 until the roadmap is complete.

---

## Stage 4: Assessment & Downstream Execution
Once the interview roadmap is exhausted, the session concludes and the data is synthesized.

### 7. Report Agent (`/api/interview/report`)
*   **Role:** Compiles the final assessment.
*   **Action:** Aggregates all Q&A logs, rubric evaluations, and vocal telemetry to calculate a final Candidate Scorecard and an overall pass/fail recommendation.
*   **Output:** A comprehensive PDF and JSON report for the recruiter.

### 8. Career Roadmap Agent
*   **Role:** Provides value back to the candidate.
*   **Action:** Reviews the specific gaps the candidate struggled with during the interview and generates a personalized study guide and weekly upskilling milestones.

### 9. Downstream Orchestrator (The Handoff)
*   **Role:** Bridges the AI loop back to humans.
*   **Action:** If the candidate achieves a passing overall score, the central orchestrator automatically triggers external API integrations.
    *   **Zoom API:** Provisions a private meeting room for the final human interview round.
    *   **SendGrid API:** Dispatches encrypted email invitations containing the meeting link to both the recruiter and the successful candidate.
