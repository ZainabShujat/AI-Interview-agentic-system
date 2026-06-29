// ─────────────────────────────────────────────────────────────────────────────
// @hireintel/sdk — Judge API
// ─────────────────────────────────────────────────────────────────────────────

import type { HttpClient } from '../http.js';
import type { JudgeParams, JudgeEvaluation } from '../types.js';

export class JudgeAPI {
  constructor(private readonly http: HttpClient) {}

  /**
   * Evaluate a single question-answer pair with the Judge agent.
   *
   * Returns accuracy, depth, communication, and problem-solving scores.
   * Useful for standalone answer evaluation outside of a full interview.
   *
   * @example
   * ```ts
   * const evaluation = await client.judge.evaluate({
   *   question: 'Explain the CAP theorem.',
   *   answer: 'CAP theorem states that in a distributed system...',
   *   signals: {
   *     responseTime: 30000,
   *     latencySeconds: 1.5,
   *     wordCount: 85,
   *     wordsPerMinute: 140,
   *     fillerCount: 1,
   *   },
   * });
   * console.log(evaluation.accuracy);  // 85
   * ```
   */
  async evaluate(params: JudgeParams): Promise<JudgeEvaluation> {
    return this.http.post<JudgeEvaluation>('/api/interview/judge', params);
  }
}
