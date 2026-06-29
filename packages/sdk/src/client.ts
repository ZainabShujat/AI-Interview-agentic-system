// ─────────────────────────────────────────────────────────────────────────────
// @hireintel/sdk — Main Client
// ─────────────────────────────────────────────────────────────────────────────

import { HttpClient } from './http.js';
import { ResumesAPI } from './api/resumes.js';
import { JDsAPI } from './api/jds.js';
import { MatchAPI } from './api/match.js';
import { InterviewAPI } from './api/interview.js';
import { ReportsAPI } from './api/reports.js';
import { JudgeAPI } from './api/judge.js';
import { RoadmapAPI } from './api/roadmap.js';
import type { HireIntelConfig, HealthCheckResponse, Interceptor } from './types.js';

/**
 * HireIntel SDK client.
 *
 * Entry point for all platform operations — resume parsing, JD analysis,
 * match scoring, adaptive interviews, reports, and career roadmaps.
 *
 * @example
 * ```ts
 * import { HireIntel } from '@hireintel/sdk';
 *
 * const client = new HireIntel({
 *   apiKey: process.env.HIREINTEL_API_KEY,
 *   baseUrl: 'http://localhost:8000',
 * });
 *
 * const resume = await client.resumes.parse(pdfBuffer, { filename: 'cv.pdf' });
 * const jd = await client.jds.create({ text: 'Senior Python Engineer...' });
 * const match = await client.match.evaluate(resume.id, jd.id);
 * console.log(match.matchScore);
 * ```
 */
export class HireIntel {
  private readonly http: HttpClient;

  /** Resume parsing and management. */
  readonly resumes: ResumesAPI;
  /** Job description parsing and management. */
  readonly jds: JDsAPI;
  /** Resume-JD match scoring with explainability. */
  readonly match: MatchAPI;
  /** Adaptive interview sessions. */
  readonly interview: InterviewAPI;
  /** Interview report listings and raw generation. */
  readonly reports: ReportsAPI;
  /** Standalone answer evaluation. */
  readonly judge: JudgeAPI;
  /** Career roadmap generation. */
  readonly roadmap: RoadmapAPI;

  constructor(config: HireIntelConfig = {}) {
    this.http = new HttpClient(config);

    this.resumes = new ResumesAPI(this.http);
    this.jds = new JDsAPI(this.http);
    this.match = new MatchAPI(this.http);
    this.interview = new InterviewAPI(this.http);
    this.reports = new ReportsAPI(this.http);
    this.judge = new JudgeAPI(this.http);
    this.roadmap = new RoadmapAPI(this.http);
  }

  /**
   * Register a request/response interceptor (middleware).
   *
   * Interceptors execute in registration order. Each interceptor
   * receives the request and a `next` function to call the next
   * interceptor (or the actual HTTP call).
   *
   * @example
   * ```ts
   * client.use(async (req, next) => {
   *   console.log(`→ ${req.method} ${req.url}`);
   *   const res = await next(req);
   *   console.log(`← ${res.status}`);
   *   return res;
   * });
   * ```
   */
  use(interceptor: Interceptor): this {
    this.http.use(interceptor);
    return this;
  }

  /**
   * Check API server health.
   *
   * @example
   * ```ts
   * const health = await client.healthCheck();
   * console.log(health.status);  // 'online'
   * console.log(health.version); // '0.1.0'
   * ```
   */
  async healthCheck(): Promise<HealthCheckResponse> {
    return this.http.get<HealthCheckResponse>('/');
  }
}
