// ─────────────────────────────────────────────────────────────────────────────
// @hireintel/sdk — Interview API
// ─────────────────────────────────────────────────────────────────────────────

import type { HttpClient } from '../http.js';
import type {
  InterviewStartParams,
  InterviewStartResult,
  AnswerSubmitParams,
  AnswerResult,
  ReportJSON,
} from '../types.js';

export class InterviewAPI {
  constructor(private readonly http: HttpClient) {}

  /**
   * Start a new adaptive interview session.
   *
   * Creates the interview record, plans the category roadmap
   * (Technical → Scenario → Behavioral → Leadership), and
   * returns the first question.
   *
   * @example
   * ```ts
   * const session = await client.interview.start({
   *   resume_id: resumeId,
   *   jd_id: jdId,
   * });
   * console.log(session.interview_id);
   * console.log(session.question);    // First question text
   * console.log(session.category);    // 'Technical'
   * ```
   */
  async start(params: InterviewStartParams): Promise<InterviewStartResult> {
    return this.http.post<InterviewStartResult>('/api/interview/start', params);
  }

  /**
   * Submit a candidate's answer to the current question.
   *
   * The answer is evaluated by the Judge agent, memory is updated,
   * difficulty adapts, and the next question is generated.
   *
   * When `finished === true`, the interview is complete and the
   * report can be fetched.
   *
   * @example
   * ```ts
   * const result = await client.interview.submitAnswer({
   *   interview_id: session.interview_id,
   *   question_text: session.question,
   *   category: session.category,
   *   answer_text: 'I would implement a microservices architecture...',
   *   signals: {
   *     responseTime: 45000,
   *     latencySeconds: 2.1,
   *     wordCount: 120,
   *     wordsPerMinute: 145,
   *     fillerCount: 3,
   *   },
   * });
   *
   * if (result.finished) {
   *   const report = await client.interview.getReport(session.interview_id);
   * } else {
   *   console.log(result.question);  // Next question
   * }
   * ```
   */
  async submitAnswer(params: AnswerSubmitParams): Promise<AnswerResult> {
    return this.http.post<AnswerResult>('/api/interview/answer', params);
  }

  /**
   * Get the final interview report.
   *
   * If the report hasn't been generated yet, the server generates it
   * on the fly from all recorded answers.
   *
   * @example
   * ```ts
   * const report = await client.interview.getReport(interviewId);
   * console.log(report.overallScore);
   * console.log(report.recommendation);
   * ```
   */
  async getReport(interviewId: string): Promise<ReportJSON> {
    return this.http.get<ReportJSON>('/api/interview/report', {
      interview_id: interviewId,
    });
  }

  /**
   * Download the interview report as a PDF binary.
   *
   * Returns raw bytes that can be saved to disk or streamed to the browser.
   *
   * @example
   * ```ts
   * const pdfBytes = await client.interview.getReportPdf(interviewId);
   * fs.writeFileSync('report.pdf', Buffer.from(pdfBytes));
   * ```
   */
  async getReportPdf(interviewId: string): Promise<ArrayBuffer> {
    return this.http.getBuffer('/api/interview/report/pdf', {
      interview_id: interviewId,
    });
  }
}
