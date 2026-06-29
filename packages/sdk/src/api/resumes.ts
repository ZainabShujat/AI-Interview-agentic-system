// ─────────────────────────────────────────────────────────────────────────────
// @hireintel/sdk — Resumes API
// ─────────────────────────────────────────────────────────────────────────────

import type { HttpClient } from '../http.js';
import type { ResumeParseResult } from '../types.js';

export class ResumesAPI {
  constructor(private readonly http: HttpClient) {}

  /**
   * Upload and parse a resume file.
   *
   * Accepts PDF, DOCX, or TXT files as File, Blob, or Buffer.
   *
   * @example
   * ```ts
   * const result = await client.resumes.parse(pdfBuffer, { filename: 'john_doe.pdf' });
   * console.log(result.parsed?.candidate_name);
   * ```
   */
  async parse(
    file: File | Blob | Buffer,
    options?: { filename?: string },
  ): Promise<ResumeParseResult> {
    return this.http.upload<ResumeParseResult>(
      '/api/resume',
      file,
      'file',
      options?.filename,
    );
  }

  /**
   * Parse multiple resumes in parallel.
   *
   * Fires N concurrent requests. Results are returned in the same order as input.
   * Failed parses return an error object instead of throwing.
   *
   * @example
   * ```ts
   * const results = await client.resumes.batchParse([
   *   { file: pdf1, filename: 'alice.pdf' },
   *   { file: pdf2, filename: 'bob.pdf' },
   * ]);
   * ```
   */
  async batchParse(
    items: Array<{ file: File | Blob | Buffer; filename?: string }>,
    options?: { concurrency?: number },
  ): Promise<Array<ResumeParseResult | { error: string; filename?: string }>> {
    const concurrency = options?.concurrency ?? 5;
    const results: Array<ResumeParseResult | { error: string; filename?: string }> = new Array(items.length);

    // Simple semaphore for concurrency control
    let running = 0;
    let idx = 0;

    await new Promise<void>((resolve) => {
      const next = () => {
        while (running < concurrency && idx < items.length) {
          const currentIdx = idx++;
          const item = items[currentIdx]!;
          running++;

          this.parse(item.file, { filename: item.filename })
            .then((res) => {
              results[currentIdx] = res;
            })
            .catch((err: Error) => {
              results[currentIdx] = { error: err.message, filename: item.filename };
            })
            .finally(() => {
              running--;
              if (idx >= items.length && running === 0) {
                resolve();
              } else {
                next();
              }
            });
        }

        // Handle edge case: empty input
        if (items.length === 0) resolve();
      };

      next();
    });

    return results;
  }
}
