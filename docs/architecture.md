# Chapter 4 — Technical Architecture & System Design

---

# Purpose

This chapter defines the complete technical architecture of HireIntel.

It explains how every component communicates, how data flows through the system, how AI agents collaborate, and how the platform should be deployed.

This architecture is designed to be:

* Modular
* Scalable
* Explainable
* Cloud-ready
* Enterprise-ready
* Cost-efficient

---

# High-Level Architecture

```text
                         Browser
                            │
                            ▼
                 React + Tailwind Frontend
                            │
                    HTTPS REST API
                            │
                            ▼
                    FastAPI Backend
                            │
              Interview Orchestrator Engine
                            │
        ┌────────────────────────────────────┐
        │                                    │
        ▼                                    ▼
   AI Agent Layer                    Database Layer
        │                                    │
        ▼                                    ▼
 Gemini / Claude                    PostgreSQL
        │                            (Supabase)
        │
        ▼
 Voice / Coding / Reports
```

---

# System Layers

The application is divided into six independent layers.

## Layer 1 — Presentation Layer

Technology

* React
* TypeScript
* Tailwind CSS
* Framer Motion
* React Router

Purpose

Provide a fast, responsive user interface.

Responsibilities

* Authentication
* Navigation
* Forms
* Uploads
* Dashboard
* Interview UI
* Reports
* Charts

No business logic should exist here.

---

## Layer 2 — API Layer

Technology

FastAPI

Purpose

Expose endpoints for the frontend.

Responsibilities

* Authentication
* Validation
* File Uploads
* Route Protection
* Session Management

The API layer never contains interview intelligence.

It only coordinates requests.

---

## Layer 3 — Orchestration Layer

This is the heart of HireIntel.

Purpose

Coordinate every AI agent.

Responsibilities

* Interview lifecycle
* Agent routing
* State management
* Memory updates
* Difficulty updates
* Error recovery

Think of this as the operating system of HireIntel.

---

## Layer 4 — AI Layer

Contains all AI agents.

Each agent receives

Input JSON

↓

Processing

↓

Output JSON

Agents never return plain text to other agents.

Only structured data.

---

## Layer 5 — Persistence Layer

Technology

PostgreSQL

Supabase

Stores

Users

Companies

Roles

Job Descriptions

Resumes

Interviews

Answers

Memory

Reports

Templates

---

## Layer 6 — External Services

Examples

Gemini

Claude

OpenSMILE

Web Speech API

GitHub

LinkedIn

Email

Storage

These are isolated behind service classes.

The application should never depend directly on third-party APIs.

---

# Frontend Architecture

```text
src/

components/

pages/

hooks/

services/

context/

utils/

types/

assets/
```

---

## Pages

Landing

Login

Dashboard

Company Intake

Assessment Builder

Resume Upload

Match Analysis

Interview

Coding Round

Report

Settings

Templates

---

## Components

Buttons

Cards

Dialogs

Tables

Charts

Timeline

Progress

Skill Chips

Question Cards

Candidate Cards

Report Sections

Everything should be reusable.

---

# Backend Architecture

```text
backend/

routers/

services/

agents/

models/

schemas/

database/

utils/

prompts/

tests/
```

---

# Routers

auth_router

company_router

resume_router

jd_router

match_router

interview_router

coding_router

report_router

dashboard_router

---

# Services

gemini_service

pdf_service

speech_service

storage_service

email_service

analytics_service

---

# Agents Folder

Each AI agent should have its own module.

Example

```text
agents/

intake_agent.py

resume_agent.py

jd_agent.py

planner_agent.py

technical_agent.py

behavioral_agent.py

judge_agent.py

memory_agent.py

communication_agent.py

recommendation_agent.py
```

Each agent should expose one public function.

Example

```python
evaluate_answer()

plan_interview()

extract_resume()

match_candidate()
```

---

# Orchestration Engine

The Interview Orchestrator coordinates all agents.

Flow

```text
Start Interview

↓

Planner Agent

↓

Interview Agent

↓

Candidate Answer

↓

Judge Agent

↓

Memory Agent

↓

Difficulty Engine

↓

Planner Agent

↓

Interview Agent

↓

Repeat
```

The orchestrator owns the interview state.

Agents remain stateless.

---

# State Management

Frontend

React Context

Local Component State

Backend

Database

Interview Session

Memory JSON

Current Question

Current Difficulty

Current Agent

Everything important lives on the backend.

---

# Database Philosophy

The database stores facts.

AI stores intelligence.

Example

Database

Question

Answer

Score

Timestamp

AI

Reasoning

Recommendations

Follow-ups

Memory

---

# AI Communication Protocol

Every AI agent returns JSON.

Never paragraphs.

Example

```json
{
  "skills": [],
  "strengths": [],
  "weaknesses": [],
  "confidence": 84,
  "needs_followup": true
}
```

Structured communication makes orchestration predictable.

---

# Memory Flow

```text
Answer

↓

Judge Agent

↓

Memory Agent

↓

Database

↓

Planner Agent

↓

Next Question
```

Memory should never exist only inside the LLM context.

It must persist between requests.

---

# File Upload Flow

Resume

↓

React Upload

↓

FastAPI

↓

PyMuPDF

↓

Resume Agent

↓

Candidate Profile

↓

Database

---

# Job Description Flow

JD Upload

↓

FastAPI

↓

JD Agent

↓

Structured Job Profile

↓

Database

↓

Planner Agent

---

# Voice Flow

Browser

↓

Web Speech API

↓

Transcript

↓

Communication Agent

↓

Judge Agent

↓

Memory

↓

Report

Future

Audio

↓

OpenSMILE

↓

Prosody Features

↓

Communication Agent

---

# Coding Assessment Flow

Candidate

↓

Monaco Editor

↓

Execution Sandbox

↓

Unit Tests

↓

Judge Agent

↓

Recommendation Agent

---

# Report Generation Flow

All Agent Outputs

↓

Recommendation Agent

↓

Report Agent

↓

PDF

Dashboard

Recruiter Summary

---

# Deployment Architecture

Frontend

Vercel

Backend

Render

Database

Supabase

Storage

Supabase Storage

Future

Docker

Kubernetes

AWS

Azure

---

# Security

Authentication

JWT

Passwords

Hashed

Uploads

Validated

Rate Limiting

Enabled

Secrets

Environment Variables

Never hardcoded.

---

# Scalability

The architecture should allow:

Multiple recruiters

Multiple companies

Thousands of candidates

Parallel interviews

Future multi-tenant support

Future microservices

without redesigning the system.

---

# Cost Philosophy

Prefer open-source and low-cost solutions whenever possible.

Current Stack

React

FastAPI

PostgreSQL

Supabase

Gemini

PyMuPDF

ReportLab

Web Speech API

OpenSMILE

Avoid unnecessary paid dependencies unless they provide significant enterprise value.

The platform should remain affordable to operate while still supporting enterprise-scale deployments.

---

# Architecture Principles

Every architectural decision should satisfy these rules:

* Single Responsibility
* Loose Coupling
* High Cohesion
* Explainability
* Stateless AI Agents
* Persistent Memory
* Structured Data Exchange
* Modular Components
* Easy Testing
* Cloud Independence

The architecture should support adding new AI agents, new assessment types, and new enterprise integrations without requiring major structural changes.
