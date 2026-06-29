# 📖 HireIntel Product Bible

## Chapter 4: REST API Gateway & Schema Specifications

This chapter acts as the reference specification for the HireIntel API endpoints.

---

## 1. Endpoints Catalog

### A. Resume Ingestion API
*   **`POST /api/resume`**
*   **Payload**: `multipart/form-data` containing PDF `file`.
*   **Response (`ResumeResponse`)**:
    ```json
    {
      "id": "res_84d72f91-2ca3-485d-8ba1-8c467a840e72",
      "filename": "Zainab_Shujat_Resume.pdf",
      "parsed": {
        "candidate_name": "Zainab Shujat",
        "headline": "Full Stack Engineer",
        "email": "zainab@email.com",
        "skills": ["React", "TypeScript"]
      },
      "telemetry": {
        "cached": false,
        "model": "Gemini 2.5 Flash",
        "cost": 0.00008,
        "mode": "Hybrid",
        "llm_calls": 1,
        "tokens": 3428
      }
    }
    ```

### B. Job Blueprint API
*   **`POST /api/jd`**
*   **Request**: `{ "text": "Raw JD requirements..." }`
*   **Response**: Structured job JSON model and ID.

### C. Readiness Match API
*   **`POST /api/match`** (Default Workflow)
*   **Request**: `{ "resume_id": "UUID", "jd_id": "UUID" }`
*   **Response**:
    *   `matchScore`: Compatibility score (0-100).
    *   `justifications`: Match checks and shortfall warnings.
*   **`POST /api/match/raw`** (Developer Tools Override)
*   **Request**: `{ "resume_json": {...}, "jd_json": {...} }`

### D. Interview Simulation API
*   **`POST /api/interview/start`**: Starts the interview.
*   **`POST /api/interview/answer`**: Submits responses and returns the next question.
*   **`POST /api/interview/judge`**: Rubric scoring for standalone answers.

### E. Career Roadmap API
*   **`POST /api/roadmap`**: Returns weekly milestones and target bridge projects.
