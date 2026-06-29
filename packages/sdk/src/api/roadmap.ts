// ─────────────────────────────────────────────────────────────────────────────
// @hireintel/sdk — Roadmap API
// ─────────────────────────────────────────────────────────────────────────────

import type { HttpClient } from '../http.js';
import type { RoadmapParams, CareerRoadmap } from '../types.js';

export class RoadmapAPI {
  constructor(private readonly http: HttpClient) {}

  /**
   * Generate a personalized career roadmap.
   *
   * Analyzes the candidate's resume against a target role/company/JD
   * and produces a structured plan of skills to acquire, certifications
   * to pursue, and experience gaps to close.
   *
   * @example
   * ```ts
   * const roadmap = await client.roadmap.generate({
   *   resume: parsedResumeJson,
   *   target_role: 'Staff Engineer',
   *   target_company: 'Google',
   * });
   * ```
   */
  async generate(params: RoadmapParams): Promise<CareerRoadmap> {
    return this.http.post<CareerRoadmap>('/api/roadmap', params);
  }
}
