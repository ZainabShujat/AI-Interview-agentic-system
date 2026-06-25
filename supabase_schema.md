# Supabase PostgreSQL Database Schema & Migration

This document provides the complete, production-grade PostgreSQL schema for the Career Readiness Simulation platform, ready to be applied directly in the **Supabase SQL Editor** or via CLI migrations.

---

## 1. Migration SQL Script

Run the following SQL script to create extensions, tables, columns, constraints, and automatic triggers.

```sql
-- Enable necessary cryptographic extensions for UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =========================================================================
-- TABLES CREATION
-- =========================================================================

-- 1. Users Profile (Links directly to Supabase auth.users)
CREATE TABLE public.users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 2. Resumes Table
CREATE TABLE public.resumes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.users(id) ON DELETE SET NULL,
    raw_text TEXT NOT NULL,
    parsed_json JSONB, -- Contains Skills, Experience, Projects, Certs
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 3. Job Descriptions (JDs) Table
CREATE TABLE public.jds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.users(id) ON DELETE SET NULL,
    recruiter_id UUID REFERENCES public.users(id) ON DELETE SET NULL, -- Tracks role owner recruiter
    department VARCHAR(100), -- Filters department organization
    raw_text TEXT NOT NULL,
    parsed_json JSONB, -- Contains Title, Required/Preferred Skills, Seniority
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 4. Interviews Table
CREATE TABLE public.interviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    candidate_name VARCHAR(255), -- Display candidate names in tracker
    candidate_email VARCHAR(255), -- Invite recipient
    invitation_token VARCHAR(100), -- Secure link token
    recruiter_id UUID REFERENCES public.users(id) ON DELETE SET NULL, -- Track evaluation reviewer
    hiring_decision VARCHAR(50) DEFAULT 'Pending' CHECK (hiring_decision IN ('Pending', 'Shortlisted', 'Rejected', 'Offered')) NOT NULL, -- Pipeline status
    resume_id UUID REFERENCES public.resumes(id) ON DELETE CASCADE NOT NULL,
    jd_id UUID REFERENCES public.jds(id) ON DELETE CASCADE NOT NULL,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'completed')) NOT NULL,
    current_question_index INT DEFAULT 0 NOT NULL,
    difficulty_level VARCHAR(20) DEFAULT 'Medium' NOT NULL,
    category_roadmap JSONB, -- Planner Agent question distribution roadmap
    memory_json JSONB, -- Memory Agent state (Strong areas, weak areas)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 5. Answers Table
CREATE TABLE public.answers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    interview_id UUID REFERENCES public.interviews(id) ON DELETE CASCADE NOT NULL,
    category VARCHAR(50) NOT NULL, -- Technical, Scenario, Behavioral, Leadership
    question_text TEXT NOT NULL,
    answer_text TEXT NOT NULL,
    evaluation_json JSONB, -- Accuracy, Depth, Communication, Confidence
    confidence_metrics JSONB, -- wpm, fillerCount, latencySeconds
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 6. Reports Table
CREATE TABLE public.reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    interview_id UUID REFERENCES public.interviews(id) ON DELETE CASCADE UNIQUE NOT NULL,
    report_json JSONB NOT NULL, -- Overall Score, Category Score vectors, Heatmap
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- =========================================================================
-- AUTOMATIC TIMESTAMPS
-- =========================================================================

-- Trigger function to update updated_at timestamps
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = timezone('utc'::text, now());
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply triggers
CREATE TRIGGER set_users_updated_at
    BEFORE UPDATE ON public.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_updated_at();

CREATE TRIGGER set_interviews_updated_at
    BEFORE UPDATE ON public.interviews
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_updated_at();

-- Automatically sync supabase auth.users to public.users on sign-up (Safe Definer & search_path locked)
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.users (id, email)
    VALUES (NEW.id, NEW.email)
    ON CONFLICT (id) DO NOTHING;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

CREATE OR REPLACE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();
```

---

## 2. Row Level Security (RLS) Policies

Enable RLS on all tables and configure policies scoped specifically for `authenticated` users.

```sql
-- Enable Row Level Security on all tables
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.resumes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.jds ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.interviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.answers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reports ENABLE ROW LEVEL SECURITY;

-- 1. Users policies
CREATE POLICY "Users can view own profile" 
    ON public.users FOR SELECT TO authenticated USING (auth.uid() = id);

-- 2. Resumes policies
CREATE POLICY "Users can view own resumes" 
    ON public.resumes FOR SELECT TO authenticated USING (auth.uid() = user_id);
CREATE POLICY "Users can create own resumes" 
    ON public.resumes FOR INSERT TO authenticated WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can delete own resumes" 
    ON public.resumes FOR DELETE TO authenticated USING (auth.uid() = user_id);

-- 3. Job Descriptions (JDs) policies
CREATE POLICY "Users can view own JDs" 
    ON public.jds FOR SELECT TO authenticated USING (auth.uid() = user_id);
CREATE POLICY "Users can create own JDs" 
    ON public.jds FOR INSERT TO authenticated WITH CHECK (auth.uid() = user_id);

-- 4. Interviews policies
CREATE POLICY "Users can view own interviews" 
    ON public.interviews FOR SELECT TO authenticated USING (auth.uid() = user_id);
CREATE POLICY "Users can create own interviews" 
    ON public.interviews FOR INSERT TO authenticated WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own interviews" 
    ON public.interviews FOR UPDATE TO authenticated USING (auth.uid() = user_id);

-- 5. Answers policies (Linked via parent interview ownership verification)
CREATE POLICY "Users can view own answers" 
    ON public.answers FOR SELECT TO authenticated USING (
        EXISTS (
            SELECT 1 FROM public.interviews 
            WHERE interviews.id = answers.interview_id AND interviews.user_id = auth.uid()
        )
    );
CREATE POLICY "Users can submit own answers" 
    ON public.answers FOR INSERT TO authenticated WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.interviews 
            WHERE interviews.id = answers.interview_id AND interviews.user_id = auth.uid()
        )
    );

-- 6. Reports policies
CREATE POLICY "Users can view own reports" 
    ON public.reports FOR SELECT TO authenticated USING (
        EXISTS (
            SELECT 1 FROM public.interviews 
            WHERE interviews.id = reports.interview_id AND interviews.user_id = auth.uid()
        )
    );
CREATE POLICY "Users can create own reports" 
    ON public.reports FOR INSERT TO authenticated WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.interviews 
            WHERE interviews.id = reports.interview_id AND interviews.user_id = auth.uid()
        )
    );
```

---

## 3. Recommended Performance Indexes

Indices structured to speed up joins and query filtering.

```sql
-- Foreign key indexes to speed up table joins
CREATE INDEX IF NOT EXISTS idx_resumes_user_id ON public.resumes(user_id);
CREATE INDEX IF NOT EXISTS idx_jds_user_id ON public.jds(user_id);
CREATE INDEX IF NOT EXISTS idx_interviews_user_id ON public.interviews(user_id);
CREATE INDEX IF NOT EXISTS idx_interviews_resume_id ON public.interviews(resume_id);
CREATE INDEX IF NOT EXISTS idx_interviews_jd_id ON public.interviews(jd_id);
CREATE INDEX IF NOT EXISTS idx_answers_interview_id ON public.answers(interview_id);
CREATE INDEX IF NOT EXISTS idx_reports_interview_id ON public.reports(interview_id);

-- Index on interview status (common query filter for active practice lists)
CREATE INDEX IF NOT EXISTS idx_interviews_status ON public.interviews(status);

-- JSONB GIN indexes (Indexes the entire JSONB object for containment @> and existence ? queries)
CREATE INDEX IF NOT EXISTS idx_resumes_parsed_json ON public.resumes USING gin (parsed_json);
CREATE INDEX IF NOT EXISTS idx_jds_parsed_json ON public.jds USING gin (parsed_json);
```

---

## 4. Scalability Suggestions (Optional Extension Tables)

If you decide to scale this MVP into a team/recruiting platform (B2B SaaS model), consider adding these tables:

### A. Organizations (Multi-Tenancy)
Enables multiple users (recruiters, managers) to share resumes, JDs, and reports under one company bucket.
```sql
CREATE TABLE public.organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Link public.users to organizations
ALTER TABLE public.users ADD COLUMN organization_id UUID REFERENCES public.organizations(id) ON DELETE SET NULL;
```

### B. Normalized Skills Registry
Instead of storing text lists inside JSON fields, a normalized skills table allows candidate matching and filtering to use simple, lightning-fast index joins rather than parsing heavy text strings.
```sql
CREATE TABLE public.skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    category VARCHAR(50) -- Frontend, Backend, Devops, Soft
);

-- Many-to-many relationship map between resumes and skills
CREATE TABLE public.resume_skills (
    resume_id UUID REFERENCES public.resumes(id) ON DELETE CASCADE,
    skill_id UUID REFERENCES public.skills(id) ON DELETE CASCADE,
    PRIMARY KEY (resume_id, skill_id)
);

-- Many-to-many relationship map between JDs and skills
CREATE TABLE public.jd_skills (
    jd_id UUID REFERENCES public.jds(id) ON DELETE CASCADE,
    skill_id UUID REFERENCES public.skills(id) ON DELETE CASCADE,
    PRIMARY KEY (jd_id, skill_id)
);
```
