# Chapter 10 — Development Standards

---

# Purpose

This chapter defines how HireIntel should be built.

The objective is to ensure that every contributor, whether human or AI, follows the same engineering standards.

Consistency is more valuable than speed.

Every feature should feel like it belongs to the same product.

---

# Development Philosophy

Before writing code, answer three questions:

1. Does this solve a real recruiter problem?
2. Does this align with the Product Bible?
3. Will this remain maintainable as the platform grows?

If the answer to any question is "No", redesign the solution before implementation.

---

# General Principles

Follow:

* Single Responsibility Principle
* DRY (Don't Repeat Yourself)
* Separation of Concerns
* Modular Architecture
* Reusable Components
* Explainable Logic
* Testable Code

Avoid unnecessary complexity.

Simple solutions should always be preferred.

---

# Frontend Standards

* Use reusable components.
* Avoid duplicate layouts.
* Keep business logic out of UI components.
* Use consistent spacing and typography.
* Every page should follow the same design system.
* Never hardcode API URLs.
* Use centralized services for API communication.

---

# Backend Standards

* Each router has one responsibility.
* Each AI agent has one responsibility.
* Keep orchestration separate from business logic.
* Validate every request.
* Never expose internal errors to users.
* Use environment variables for configuration.

---

# AI Agent Standards

Every AI agent should:

* Receive structured input.
* Return structured JSON.
* Never modify database state directly.
* Never call another agent independently.
* Be orchestrated by the Interview Orchestrator.

Agents should remain replaceable without affecting the rest of the system.

---

# Prompt Standards

Prompts should:

* Be version-controlled.
* Live in dedicated prompt files.
* Be descriptive.
* Return structured output.
* Avoid unnecessary verbosity.
* Minimize hallucination.

Prompt changes should be documented.

---

# API Standards

Every endpoint should:

* Validate input.
* Return predictable responses.
* Include meaningful status codes.
* Handle failures gracefully.
* Be documented.

Example response:

```json
{
  "success": true,
  "message": "Assessment created successfully.",
  "data": {}
}
```

---

# Database Standards

* Never delete critical data permanently without policy.
* Preserve raw uploads.
* Store AI outputs separately from user data.
* Use foreign keys appropriately.
* Keep migrations version-controlled.

---

# Logging Standards

Log important events.

Do not log sensitive information such as:

* Passwords
* API Keys
* Access Tokens

Logs should help debugging without compromising security.

---

# Testing Standards

Every major feature should include:

Unit Tests

Integration Tests

API Tests

Manual Verification Checklist

AI outputs should be validated against expected JSON schemas.

---

# Git Standards

Use meaningful commit messages.

Examples:

feat: add Planner Agent

fix: improve follow-up logic

refactor: separate communication service

Avoid vague commits such as:

update

changes

fixed stuff

---

# Documentation Standards

Every major feature should include:

Purpose

Inputs

Outputs

Dependencies

Failure Cases

Future Improvements

Documentation should remain synchronized with implementation.

---

# Performance Standards

Optimize for:

Fast page loads

Efficient API calls

Minimal AI requests

Reusable caches

Graceful loading states

Avoid unnecessary AI invocations where deterministic code is sufficient.

---

# Security Standards

Always:

Validate user input.

Sanitize uploaded files.

Protect secrets.

Use HTTPS.

Hash passwords.

Verify authentication.

Never trust client-side validation.

---

# Code Review Checklist

Before merging any feature, verify:

* Matches Product Bible.
* Uses reusable components.
* Follows architecture.
* Includes error handling.
* Includes validation.
* Includes testing.
* Includes documentation.
* Maintains UI consistency.

---

# AI Coding Guidelines

When using AI coding assistants:

Provide context.

Reference the relevant Product Bible chapter.

Ask for one feature at a time.

Require structured outputs.

Review generated code before merging.

AI should accelerate development, not replace engineering judgment.

---

# Long-Term Vision

HireIntel should remain understandable by any developer joining the project.

The codebase should prioritize clarity over cleverness.

A new engineer should be able to understand the system by reading the Product Bible, exploring the folder structure, and reviewing documented APIs.

The Product Bible is the source of truth.

If implementation and documentation disagree, the discrepancy should be resolved immediately.

Every contribution should move HireIntel closer to becoming a world-class enterprise hiring platform.
