// ─────────────────────────────────────────────────────────────────────────────
// @hireintel/sdk — Public API
// ─────────────────────────────────────────────────────────────────────────────

// Client
export { HireIntel } from './client.js';

// Types — re-export everything for consumer convenience
export type {
  HireIntelConfig,
  RequestInfo,
  ResponseInfo,
  Interceptor,
  InterceptedRequest,
  InterceptedResponse,
  NextFn,

  // Resume
  ParsedResume,
  ResumeTelemetry,
  ResumeParseResult,
  ProjectSchema,
  ExperienceSchema,
  EducationSchema,
  InternshipSchema,
  LinkSchema,

  // JD
  JDCreateParams,
  JDCreateResult,
  JDUploadResult,
  JDListItem,
  BlueprintUpdateParams,
  BlueprintUpdateResult,

  // Match
  MatchEvaluateParams,
  MatchRawParams,
  MatchJustification,
  MatchResult,

  // Interview
  InterviewStartParams,
  InterviewStartResult,
  ConfidenceSignals,
  AnswerSubmitParams,
  AnswerResult,

  // Judge
  JudgeParams,
  JudgeEvaluation,

  // Report
  ReportJSON,
  ReportListItem,
  RawReportParams,

  // Roadmap
  RoadmapParams,
  CareerRoadmap,

  // Health
  HealthCheckResponse,
} from './types.js';

// Errors
export {
  HireIntelError,
  ValidationError,
  AuthenticationError,
  NotFoundError,
  UnprocessableError,
  RateLimitError,
  ServerError,
  NetworkError,
} from './errors.js';

// Utilities
export { driveInterview } from './utils/polling.js';
