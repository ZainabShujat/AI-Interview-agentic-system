// ─────────────────────────────────────────────────────────────────────────────
// @hireintel/sdk — Job Descriptions API
// ─────────────────────────────────────────────────────────────────────────────

import type { HttpClient } from '../http.js';
import type {
  JDCreateParams,
  JDCreateResult,
  JDUploadResult,
  JDListItem,
  BlueprintUpdateResult,
} from '../types.js';

export class JDsAPI {
  constructor(private readonly http: HttpClient) {}

  /**
   * List all job descriptions, most recent first (limit 50).
   *
   * @example
   * ```ts
   * const jds = await client.jds.list();
   * jds.forEach(jd => console.log(jd.title, jd.seniority));
   * ```
   */
  async list(): Promise<JDListItem[]> {
    return this.http.get<JDListItem[]>('/api/jd');
  }

  /**
   * Create a job description from raw text.
   *
   * The text is parsed by the JD Intelligence agent into a structured
   * hiring blueprint with role, skills, responsibilities, etc.
   *
   * @example
   * ```ts
   * const jd = await client.jds.create({
   *   text: 'Senior Python Engineer with 5+ years experience...'
   * });
   * console.log(jd.id, jd.parsed);
   * ```
   */
  async create(params: JDCreateParams): Promise<JDCreateResult> {
    return this.http.post<JDCreateResult>('/api/jd', params);
  }

  /**
   * Upload a JD file (PDF or text) for parsing.
   *
   * @example
   * ```ts
   * const jd = await client.jds.upload(pdfFile, { filename: 'senior_eng.pdf' });
   * console.log(jd.parsed);
   * ```
   */
  async upload(
    file: File | Blob | Buffer,
    options?: { filename?: string },
  ): Promise<JDUploadResult> {
    return this.http.upload<JDUploadResult>(
      '/api/jd/upload',
      file,
      'file',
      options?.filename,
    );
  }

  /**
   * Update the parsed hiring blueprint for a JD.
   *
   * Useful when recruiters manually refine the auto-parsed blueprint.
   *
   * @example
   * ```ts
   * const updated = await client.jds.updateBlueprint(jdId, {
   *   ...existingBlueprint,
   *   seniority: 'Staff',
   * });
   * ```
   */
  async updateBlueprint(
    jdId: string,
    blueprint: Record<string, unknown>,
  ): Promise<BlueprintUpdateResult> {
    return this.http.put<BlueprintUpdateResult>(
      `/api/jd/${jdId}/blueprint`,
      { blueprint },
    );
  }
}
