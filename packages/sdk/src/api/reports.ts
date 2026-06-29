// ─────────────────────────────────────────────────────────────────────────────
// @hireintel/sdk — Reports API
// ─────────────────────────────────────────────────────────────────────────────

import type { HttpClient } from '../http.js';
import type { ReportListItem, RawReportParams, ReportJSON } from '../types.js';

export class ReportsAPI {
  constructor(private readonly http: HttpClient) {}

  /**
   * List all interview reports, optionally filtered by JD.
   *
   * Returns candidate name, score, recommendation, and status
   * for each interview session.
   *
   * @example
   * ```ts
   * // All reports
   * const all = await client.reports.list();
   *
   * // Filtered by job description
   * const forRole = await client.reports.list({ jdId: 'abc-123' });
   * forRole.forEach(r => console.log(r.candidate_name, r.score));
   * ```
   */
  async list(options?: { jdId?: string }): Promise<ReportListItem[]> {
    const query: Record<string, string> = {};
    if (options?.jdId) query['jd_id'] = options.jdId;
    return this.http.get<ReportListItem[]>('/api/interview/reports', query);
  }

  /**
   * Generate a report from raw Q&A data (no database).
   *
   * Useful for playground testing and external integrations
   * where the interview was conducted outside the platform.
   *
   * @example
   * ```ts
   * const report = await client.reports.generateRaw({
   *   all_qa: [
   *     { question: '...', answer: '...', evaluation: {...}, category: 'Technical' }
   *   ],
   *   memory: { demonstrated_skills: ['Python'], weak_skills: [] },
   * });
   * ```
   */
  async generateRaw(params: RawReportParams): Promise<ReportJSON> {
    return this.http.post<ReportJSON>('/api/interview/report/raw', params);
  }
}
