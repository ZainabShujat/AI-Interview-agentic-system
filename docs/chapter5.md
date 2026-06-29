# 📖 HireIntel Product Bible

## Chapter 5: SQLite Database Schema & Caching Table

This chapter details the SQL database tables, columns, indexes, and database relationship structures.

---

## 1. Database Table Directory

### A. Table `resumes`
Stores candidate profile raw documents and parsed JSON details.
*   `id` (String(36), PK): UUID.
*   `raw_text` (Text, Required): Raw document string.
*   `parsed_json` (JSON, Nullable): Standardized parsed profile.

### B. Table `jds` (Job Descriptions)
Stores recruiter-defined role blueprints.
*   `id` (String(36), PK): UUID.
*   `raw_text` (Text, Required): Job text description.
*   `parsed_json` (JSON, Nullable): Structured hiring criteria.

### C. Table `interviews`
Manages the active state machine of the assessment.
*   `id` (String(36), PK): UUID.
*   `resume_id` (String(36), FK $\rightarrow$ `resumes.id`): Linked resume.
*   `jd_id` (String(36), FK $\rightarrow$ `jds.id`): Linked JD.
*   `status` (String(20)): Default is `active`.
*   `current_question_index` (Integer): Question counter.
*   `memory_json` (JSON, Nullable): Candidate answers and progress context.

### D. Table `answers`
Stores individual candidate response scripts.
*   `id` (String(36), PK): UUID.
*   `interview_id` (String(36), FK $\rightarrow$ `interviews.id`): Parent interview session.
*   `question_text` (Text, Required): Question prompt.
*   `answer_text` (Text, Required): Speech transcript.
*   `evaluation_json` (JSON, Nullable): Scored accuracy, depth, and communication ratings.
*   `confidence_metrics` (JSON, Nullable): Hesitation and pacing parameters.

### E. Table `reports`
Aggregates session parameters into candidate scorecard summaries.
*   `id` (String(36), PK): UUID.
*   `interview_id` (String(36), FK $\rightarrow$ `interviews.id`): Session reference.
*   `report_json` (JSON, Required): Summary text and score arrays.

### F. Table `resume_caches` (Resume Caches)
Optimizes LLM request overhead.
*   `id` (String(36), PK): UUID.
*   `raw_text_hash` (String(64), Unique, Indexed): SHA-256 hash of the cleaned document string.
*   `parsed_json` (JSON, Required): Cached parsed JSON candidate profile.
