// ─────────────────────────────────────────────────────────────────────────────
// @hireintel/sdk — Type Definitions
// Hand-mapped from backend/schemas.py + router response shapes
// ─────────────────────────────────────────────────────────────────────────────

// ── SDK Configuration ────────────────────────────────────────────────────────

export interface HireIntelConfig {
  /** API key sent as X-API-Key header. */
  apiKey?: string;
  /** Base URL of the HireIntel API server. Default: http://localhost:8000 */
  baseUrl?: string;
  /** Request timeout in milliseconds. Default: 30000 */
  timeout?: number;
  /** Max retry attempts on 429 / 5xx responses. Default: 3 */
  retryMaxAttempts?: number;
  /** Initial retry delay in milliseconds (doubled each attempt). Default: 1000 */
  retryDelayMs?: number;
  /** Enable debug logging to console. Default: false */
  debug?: boolean;
  /** Hook called before every request. */
  onRequest?: (info: RequestInfo) => void;
  /** Hook called after every response. */
  onResponse?: (info: ResponseInfo) => void;
}

export interface RequestInfo {
  method: string;
  url: string;
  headers: Record<string, string>;
  body?: unknown;
}

export interface ResponseInfo {
  status: number;
  url: string;
  durationMs: number;
  body?: unknown;
}

// ── Middleware / Interceptor ─────────────────────────────────────────────────

export type NextFn = (req: InterceptedRequest) => Promise<InterceptedResponse>;

export type Interceptor = (req: InterceptedRequest, next: NextFn) => Promise<InterceptedResponse>;

export interface InterceptedRequest {
  method: string;
  url: string;
  headers: Record<string, string>;
  body?: unknown;
}

export interface InterceptedResponse {
  status: number;
  headers: Record<string, string>;
  body: unknown;
}

// ── Resume Types ─────────────────────────────────────────────────────────────

export interface ProjectSchema {
  title?: string;
  description?: string;
  technologies: string[];
  github?: string;
  demo?: string;
  contributions: string[];
}

export interface ExperienceSchema {
  title?: string;
  company?: string;
  employment_type?: string;
  duration?: string;
  responsibilities: string[];
  achievements: string[];
  technologies: string[];
}

export interface EducationSchema {
  degree?: string;
  branch?: string;
  institution?: string;
  year?: string;
  cgpa?: string;
}

export interface InternshipSchema {
  company?: string;
  role?: string;
  duration?: string;
  summary?: string;
}

export interface LinkSchema {
  url?: string;
  type?: string;
  verified?: boolean;
  summary?: string;
  skills_found: string[];
  projects_found: string[];
}

export interface ParsedResume {
  candidate_name?: string;
  headline?: string;
  email?: string;
  phone?: string;
  location?: string;

  linkedin?: string;
  github?: string;
  portfolio?: string;
  website?: string;

  summary?: string;

  career_level?: string;
  estimated_experience_years?: number;
  primary_domain?: string;

  skills: string[];
  technical_skills: string[];
  soft_skills: string[];
  programming_languages: string[];
  frameworks: string[];
  databases: string[];
  cloud_platforms: string[];
  tools: string[];

  projects: ProjectSchema[];
  experience: ExperienceSchema[];
  education: EducationSchema[];
  certifications: string[];
  internships: InternshipSchema[];
  achievements: string[];
  languages: string[];
  domain_experience: string[];
  top_strengths: string[];
  potential_concerns: string[];
  links: LinkSchema[];
}

export interface ResumeTelemetry {
  cached: boolean;
  model: string;
  cost: number;
  mode: string;
  fallback: boolean;
}

export interface ResumeParseResult {
  id: string;
  filename: string;
  parsed: ParsedResume | null;
  raw_resume_text: string | null;
  telemetry: ResumeTelemetry | null;
}

// ── Job Description Types ────────────────────────────────────────────────────

export interface JDCreateParams {
  text: string;
}

export interface JDCreateResult {
  id: string;
  parsed: Record<string, unknown>;
}

export interface JDUploadResult {
  id: string;
  filename: string;
  parsed: Record<string, unknown>;
}

export interface JDListItem {
  id: string;
  title: string;
  industry?: string;
  seniority?: string;
  department?: string;
  created_at?: string;
  parsed: Record<string, unknown>;
}

export interface BlueprintUpdateParams {
  blueprint: Record<string, unknown>;
}

export interface BlueprintUpdateResult {
  id: string;
  parsed: Record<string, unknown>;
}

// ── Match Types ──────────────────────────────────────────────────────────────

export interface MatchEvaluateParams {
  resume_id: string;
  jd_id: string;
}

export interface MatchRawParams {
  resume_json: Record<string, unknown>;
  jd_json: Record<string, unknown>;
}

export interface MatchJustification {
  type: 'success' | 'warning' | 'gap';
  text: string;
}

export interface MatchResult {
  matchScore: number;
  justifications: MatchJustification[];
  assessmentBlueprint: Record<string, unknown>;
  [key: string]: unknown;
}

// ── Interview Types ──────────────────────────────────────────────────────────

export interface InterviewStartParams {
  resume_id: string;
  jd_id: string;
}

export interface InterviewStartResult {
  interview_id: string;
  question: string;
  category: string;
  finished: boolean;
}

export interface ConfidenceSignals {
  responseTime: number;
  latencySeconds: number;
  wordCount: number;
  wordsPerMinute: number;
  fillerCount: number;
  speakingRate?: number;
  energy?: number;
  intensity?: number;
  pitchVariance?: number;
  jitter?: number;
  shimmer?: number;
}

export interface AnswerSubmitParams {
  interview_id: string;
  question_text: string;
  category: string;
  answer_text: string;
  signals: ConfidenceSignals;
}

export interface JudgeEvaluation {
  accuracy: number;
  depth: number;
  communication: number;
  problemSolving: number;
  [key: string]: unknown;
}

export interface AnswerResult {
  question: string;
  category: string;
  finished: boolean;
  evaluation: JudgeEvaluation;
}

// ── Report Types ─────────────────────────────────────────────────────────────

export interface ReportJSON {
  overallScore: number;
  recommendation: string;
  [key: string]: unknown;
}

export interface ReportListItem {
  interview_id: string;
  candidate_name: string;
  candidate_email: string;
  job_title: string;
  jd_id: string;
  score: number;
  recommendation: string;
  status: string;
  date: string | null;
}

export interface RawReportParams {
  all_qa: Array<Record<string, unknown>>;
  memory: Record<string, unknown>;
}

// ── Judge Types ──────────────────────────────────────────────────────────────

export interface JudgeParams {
  question: string;
  answer: string;
  signals: ConfidenceSignals;
}

// ── Roadmap Types ────────────────────────────────────────────────────────────

export interface RoadmapParams {
  resume: Record<string, unknown>;
  target_role?: string;
  target_company?: string;
  target_jd?: Record<string, unknown>;
}

export interface CareerRoadmap {
  [key: string]: unknown;
}

// ── Health Check ─────────────────────────────────────────────────────────────

export interface HealthCheckResponse {
  status: string;
  service: string;
  version: string;
}
