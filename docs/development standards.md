# HireIntel Platform Development & Coding Standards

This document establishes the coding conventions, architectural rules, and design standards required for modifying the **HireIntel Developer Platform**.

---

## 1. Backend Standards (Python & FastAPI)

*   **PEP 8 Compliance**: Follow standard PEP 8 naming conventions.
*   **Type Hinting**: All router signatures and service helper functions must include type annotations (using `typing` module).
*   **Response Schemas**: Every FastAPI path function must explicitly state a Pydantic `response_model` return schema to enforce data sanitization.
*   **Exception Isolation**:
    *   LLM services must run inside `try-except` blocks.
    *   Always catch specific model exceptions (e.g. timeout, quota limit, invalid api key) and log warning events.
    *   Drop into designated local heuristic fallback routines automatically if external APIs fail.

---

## 2. Relational Database Guidelines (SQLAlchemy)

*   **Transaction Lifecycle**: Always close database sessions inside router functions (utilizing FastAPI `Depends(get_db)` to automate session lifecycles).
*   **Cascades**: Specify delete rules (`cascade="all, delete-orphan"`) on all parent entities to keep SQLite storage clean of orphaned answers or report card rows.
*   **Indexing**: Cache tables must include indices on query fields (e.g., `raw_text_hash` in `ResumeCache`).

---

## 3. Integration Standards (React Components)

*   **Decoupled CSS Styling**: UI components inside `@hireintel/react` must use encapsulated CSS rules to prevent global Tailwind/Bootstrap name overrides.
*   **Styling Modifiers**: Widgets must support `theme="inherit"` (inheriting parent styles) and `unstyled` modes (canceling default layouts).
*   **Direct SDK Usage**: Components should utilize `@hireintel/sdk` client parameters rather than hardcoding local endpoint fetches.

---

## 4. API & Telemetry Contract Design

*   **Explicit Telemetry**: Every parsed response must return execution metadata (cache hits, latency, cost calculations, token counts, and call volumes).
*   **Transparent Scoring**: Matching services must compute scores deterministically using transparent weights, returning an explainable `justifications` list.
*   **SemVer Versioning**: Version tags must align to semantic specifications (major changes, minor extensions, patch fixes).
