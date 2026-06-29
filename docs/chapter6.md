# 📖 HireIntel Product Bible

## Chapter 6: Version History & Platform Roadmap

This chapter charts the platform version evolution history, build milestones, and the roadmap for upcoming packages.

---

## 1. Release Version History

*   **v1.0.0 — Initial REST Prototype**: Basic FastAPI matching and parsing endpoints connected directly to raw LLM chains.
*   **v1.1.0 — Cache & Resilience Fallbacks**: Relational database storage, text hashing, and local python fallback rules if Gemini limits are reached.
*   **v1.2.0 — Recruiter Greetings & Dashboard Alerts**: Dynamic greeting variables, custom initials tags, and mockup notice banners on dashboards.
*   **v1.3.0 — Precision Extraction Heuristics**: Top-line header scans for candidate names, skipping job credentials/certs, and filename-fallback parsing.
*   **v1.4.0 — Developer Observability Telemetry**: Interactive telemetry metrics (WPM, token count, call volumes, costs) and collapsible Developer Tools panel.
*   **v1.5.0 — Match & Domain Explainability (Current)**: Explainable match score justifications ($\checkmark$/$\triangle$ flags) and primary domain derivation why tags.

---

## 2. Platform Integration Roadmap

We will develop three separate developer-native platform components next:

### Component A: TypeScript SDK (`@hireintel/sdk`)
A wrapper package client that handles standard authorization, connection retries, and returns type-safe candidate objects.

### Component B: React UI Library (`@hireintel/react`)
Ready-to-use React widgets (upload cards, matching meters, dashboard scorecards) utilizing Vanilla CSS styling and supporting `theme="inherit"` variables.

### Component C: Model Context Protocol Server (`@hireintel/mcp-server`)
MCP Server that exposes HireIntel Client calls as discoverable, LLM-native tools for AI interfaces.
