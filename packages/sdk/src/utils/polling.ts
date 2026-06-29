// ─────────────────────────────────────────────────────────────────────────────
// @hireintel/sdk — Polling Utility
// ─────────────────────────────────────────────────────────────────────────────

import type { HireIntel } from '../client.js';
import type { AnswerResult, InterviewStartResult, ReportJSON } from '../types.js';

/**
 * Drives a complete interview session to completion.
 *
 * Repeatedly calls `submitAnswer` with user-provided answers until
 * `finished === true`, then fetches and returns the final report.
 *
 * @param client  - HireIntel SDK client instance
 * @param session - The interview session from `client.interview.start()`
 * @param getAnswer - Async callback that receives the current question
 *                    context and returns the candidate's answer text
 *                    and confidence signals.
 * @param options - Polling configuration
 *
 * @example
 * ```ts
 * import { HireIntel, driveInterview } from '@hireintel/sdk';
 *
 * const client = new HireIntel({ baseUrl: 'http://localhost:8000' });
 * const session = await client.interview.start({ resume_id, jd_id });
 *
 * const report = await driveInterview(client, session, async (ctx) => {
 *   // Your logic to generate/collect an answer
 *   return {
 *     answer_text: await askCandidate(ctx.question),
 *     signals: {
 *       responseTime: 30000,
 *       latencySeconds: 2.0,
 *       wordCount: 100,
 *       wordsPerMinute: 130,
 *       fillerCount: 2,
 *     },
 *   };
 * });
 *
 * console.log(report.overallScore);
 * ```
 */
export async function driveInterview(
  client: HireIntel,
  session: InterviewStartResult,
  getAnswer: (context: {
    question: string;
    category: string;
    questionIndex: number;
  }) => Promise<{
    answer_text: string;
    signals: {
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
    };
  }>,
  options?: {
    /** Max questions before force-stopping. Default: 30 */
    maxQuestions?: number;
    /** Delay between answer submissions in ms. Default: 0 */
    delayMs?: number;
  },
): Promise<ReportJSON> {
  const maxQuestions = options?.maxQuestions ?? 30;
  const delayMs = options?.delayMs ?? 0;

  let currentQuestion = session.question;
  let currentCategory = session.category;
  let finished = session.finished;
  let questionIndex = 0;

  while (!finished && questionIndex < maxQuestions) {
    const answerData = await getAnswer({
      question: currentQuestion,
      category: currentCategory,
      questionIndex,
    });

    if (delayMs > 0) {
      await new Promise((resolve) => setTimeout(resolve, delayMs));
    }

    const result: AnswerResult = await client.interview.submitAnswer({
      interview_id: session.interview_id,
      question_text: currentQuestion,
      category: currentCategory,
      answer_text: answerData.answer_text,
      signals: answerData.signals,
    });

    finished = result.finished;
    currentQuestion = result.question;
    currentCategory = result.category;
    questionIndex++;
  }

  return client.interview.getReport(session.interview_id);
}
