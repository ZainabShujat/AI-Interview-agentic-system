// ─────────────────────────────────────────────────────────────────────────────
// @hireintel/sdk — Match API
// ─────────────────────────────────────────────────────────────────────────────

import type { HttpClient } from '../http.js';
import type { MatchResult } from '../types.js';

export class MatchAPI {
  constructor(private readonly http: HttpClient) {}

  /**
   * Evaluate match between a stored resume and JD using their IDs.
   *
   * Returns a deterministic match score with justifications explaining
   * every matched skill, gap, and the resulting assessment blueprint.
   *
   * @example
   * ```ts
   * const match = await client.match.evaluate(resumeId, jdId);
   * console.log(match.matchScore);        // 82
   * console.log(match.justifications);     // [{ type: 'success', text: '...' }, ...]
   * console.log(match.assessmentBlueprint);
   * ```
   */
  async evaluate(resumeId: string, jdId: string): Promise<MatchResult> {
    return this.http.post<MatchResult>('/api/match', {
      resume_id: resumeId,
      jd_id: jdId,
    });
  }

  /**
   * Evaluate match from raw JSON (no database lookup).
   *
   * Used for playground / sandbox testing where parsed JSON
   * is available directly without prior upload.
   *
   * @example
   * ```ts
   * const match = await client.match.evaluateRaw(parsedResume, parsedJD);
   * ```
   */
  async evaluateRaw(
    resumeJson: Record<string, unknown>,
    jdJson: Record<string, unknown>,
  ): Promise<MatchResult> {
    return this.http.post<MatchResult>('/api/match/raw', {
      resume_json: resumeJson,
      jd_json: jdJson,
    });
  }
}
