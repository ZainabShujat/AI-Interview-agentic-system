// ─────────────────────────────────────────────────────────────────────────────
// @hireintel/sdk — HTTP Client
// Zero-dependency fetch wrapper with retries, interceptors, auth, and debug.
// ─────────────────────────────────────────────────────────────────────────────

import { createErrorFromStatus, NetworkError } from './errors.js';
import type {
  HireIntelConfig,
  RequestInfo as ReqInfo,
  ResponseInfo as ResInfo,
  Interceptor,
  InterceptedRequest,
  InterceptedResponse,
  NextFn,
} from './types.js';

/** Resolved config with defaults applied. */
interface ResolvedConfig {
  baseUrl: string;
  apiKey: string | undefined;
  timeout: number;
  retryMaxAttempts: number;
  retryDelayMs: number;
  debug: boolean;
  onRequest: ((info: ReqInfo) => void) | undefined;
  onResponse: ((info: ResInfo) => void) | undefined;
}

function resolveConfig(cfg: HireIntelConfig): ResolvedConfig {
  return {
    baseUrl: (cfg.baseUrl ?? 'http://localhost:8000').replace(/\/+$/, ''),
    apiKey: cfg.apiKey,
    timeout: cfg.timeout ?? 30_000,
    retryMaxAttempts: cfg.retryMaxAttempts ?? 3,
    retryDelayMs: cfg.retryDelayMs ?? 1_000,
    debug: cfg.debug ?? false,
    onRequest: cfg.onRequest,
    onResponse: cfg.onResponse,
  };
}

// ── Internal sleep helper ────────────────────────────────────────────────────

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// ── HttpClient ───────────────────────────────────────────────────────────────

export class HttpClient {
  private readonly cfg: ResolvedConfig;
  private readonly interceptors: Interceptor[] = [];

  constructor(config: HireIntelConfig) {
    this.cfg = resolveConfig(config);
  }

  /** Register an interceptor (middleware). Interceptors execute in FIFO order. */
  use(interceptor: Interceptor): void {
    this.interceptors.push(interceptor);
  }

  // ── Public request methods ─────────────────────────────────────────────────

  async get<T>(path: string, query?: Record<string, string>): Promise<T> {
    let url = `${this.cfg.baseUrl}${path}`;
    if (query) {
      const params = new URLSearchParams(
        Object.entries(query).filter(([, v]) => v !== undefined),
      );
      if (params.toString()) url += `?${params.toString()}`;
    }
    return this.request<T>('GET', url);
  }

  async post<T>(path: string, body?: unknown): Promise<T> {
    return this.request<T>('POST', `${this.cfg.baseUrl}${path}`, body);
  }

  async put<T>(path: string, body?: unknown): Promise<T> {
    return this.request<T>('PUT', `${this.cfg.baseUrl}${path}`, body);
  }

  async delete<T>(path: string): Promise<T> {
    return this.request<T>('DELETE', `${this.cfg.baseUrl}${path}`);
  }

  /**
   * POST with multipart/form-data — used for file uploads.
   * Accepts File | Blob | Buffer. Buffer is converted to Blob internally.
   */
  async upload<T>(
    path: string,
    file: File | Blob | Buffer,
    fieldName: string = 'file',
    filename?: string,
  ): Promise<T> {
    let blob: Blob;
    let name: string;

    if (typeof Buffer !== 'undefined' && Buffer.isBuffer(file)) {
      blob = new Blob([file]);
      name = filename ?? 'upload';
    } else if (file instanceof File) {
      blob = file;
      name = filename ?? file.name;
    } else {
      blob = file;
      name = filename ?? 'upload';
    }

    const form = new FormData();
    form.append(fieldName, blob, name);

    return this.requestRaw<T>('POST', `${this.cfg.baseUrl}${path}`, form);
  }

  /**
   * GET that returns raw ArrayBuffer (used for PDF downloads).
   */
  async getBuffer(path: string, query?: Record<string, string>): Promise<ArrayBuffer> {
    let url = `${this.cfg.baseUrl}${path}`;
    if (query) {
      const params = new URLSearchParams(
        Object.entries(query).filter(([, v]) => v !== undefined),
      );
      if (params.toString()) url += `?${params.toString()}`;
    }
    return this.requestBuffer('GET', url);
  }

  // ── Core request engine ────────────────────────────────────────────────────

  private async request<T>(method: string, url: string, body?: unknown): Promise<T> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (this.cfg.apiKey) headers['X-API-Key'] = this.cfg.apiKey;

    const interceptedReq: InterceptedRequest = {
      method,
      url,
      headers,
      body,
    };

    // Run through interceptor chain
    const finalFn = this.buildInterceptorChain(async (req) => {
      return this.executeWithRetry(req, false);
    });

    const res = await finalFn(interceptedReq);
    return res.body as T;
  }

  private async requestRaw<T>(method: string, url: string, form: FormData): Promise<T> {
    // For FormData, let fetch set the Content-Type (includes boundary)
    const headers: Record<string, string> = {};
    if (this.cfg.apiKey) headers['X-API-Key'] = this.cfg.apiKey;

    const interceptedReq: InterceptedRequest = {
      method,
      url,
      headers,
      body: form,
    };

    const finalFn = this.buildInterceptorChain(async (req) => {
      return this.executeWithRetry(req, true);
    });

    const res = await finalFn(interceptedReq);
    return res.body as T;
  }

  private async requestBuffer(method: string, url: string): Promise<ArrayBuffer> {
    const headers: Record<string, string> = {};
    if (this.cfg.apiKey) headers['X-API-Key'] = this.cfg.apiKey;

    const start = Date.now();

    this.debugLog(`→ ${method} ${url}`);
    this.cfg.onRequest?.({ method, url, headers });

    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.cfg.timeout);

    try {
      const response = await fetch(url, {
        method,
        headers,
        signal: controller.signal,
      });

      clearTimeout(timer);
      const durationMs = Date.now() - start;

      if (!response.ok) {
        const text = await response.text().catch(() => '');
        let detail: string | undefined;
        try {
          const parsed = JSON.parse(text);
          detail = parsed.detail ?? text;
        } catch {
          detail = text;
        }
        throw createErrorFromStatus(response.status, url, detail);
      }

      const buffer = await response.arrayBuffer();
      this.cfg.onResponse?.({ status: response.status, url, durationMs, body: `<${buffer.byteLength} bytes>` });
      this.debugLog(`← ${response.status} (${durationMs}ms) ${buffer.byteLength} bytes`);
      return buffer;
    } catch (err) {
      clearTimeout(timer);
      if (err instanceof Error && err.name === 'AbortError') {
        throw new NetworkError(url, `Request timed out after ${this.cfg.timeout}ms`);
      }
      throw err;
    }
  }

  // ── Interceptor chain builder ──────────────────────────────────────────────

  private buildInterceptorChain(
    terminal: (req: InterceptedRequest) => Promise<InterceptedResponse>,
  ): NextFn {
    let chain: NextFn = terminal;

    // Wrap from last to first so the first registered interceptor runs first
    for (let i = this.interceptors.length - 1; i >= 0; i--) {
      const interceptor = this.interceptors[i]!;
      const next = chain;
      chain = (req) => interceptor(req, next);
    }

    return chain;
  }

  // ── Retry engine ───────────────────────────────────────────────────────────

  private async executeWithRetry(
    req: InterceptedRequest,
    isFormData: boolean,
  ): Promise<InterceptedResponse> {
    let lastError: Error | undefined;

    for (let attempt = 0; attempt < this.cfg.retryMaxAttempts; attempt++) {
      if (attempt > 0) {
        const delay = this.cfg.retryDelayMs * Math.pow(2, attempt - 1);
        this.debugLog(`⟳ Retry ${attempt}/${this.cfg.retryMaxAttempts} in ${delay}ms`);
        await sleep(delay);
      }

      const start = Date.now();
      this.debugLog(`→ ${req.method} ${req.url}`);
      this.cfg.onRequest?.({ method: req.method, url: req.url, headers: req.headers, body: req.body });

      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), this.cfg.timeout);

      try {
        const fetchInit: globalThis.RequestInit = {
          method: req.method,
          headers: req.headers,
          signal: controller.signal,
        };

        if (req.body !== undefined) {
          if (isFormData) {
            fetchInit.body = req.body as FormData;
          } else {
            fetchInit.body = JSON.stringify(req.body);
          }
        }

        const response = await fetch(req.url, fetchInit);
        clearTimeout(timer);

        const durationMs = Date.now() - start;

        // Retryable status codes
        if ((response.status === 429 || response.status >= 500) && attempt < this.cfg.retryMaxAttempts - 1) {
          const text = await response.text().catch(() => '');
          this.debugLog(`← ${response.status} (retryable) — ${text.slice(0, 120)}`);
          lastError = createErrorFromStatus(response.status, req.url, text);
          continue;
        }

        // Non-retryable error
        if (!response.ok) {
          const text = await response.text().catch(() => '');
          let detail: string | undefined;
          try {
            const parsed = JSON.parse(text);
            detail = parsed.detail ?? text;
          } catch {
            detail = text;
          }
          throw createErrorFromStatus(
            response.status,
            req.url,
            detail,
            response.status === 429
              ? parseInt(response.headers.get('Retry-After') ?? '0', 10) || undefined
              : undefined,
          );
        }

        // Success
        const body = await response.json().catch(() => ({}));
        this.cfg.onResponse?.({ status: response.status, url: req.url, durationMs, body });
        this.debugLog(`← ${response.status} (${durationMs}ms)`);

        const resHeaders: Record<string, string> = {};
        response.headers.forEach((v, k) => {
          resHeaders[k] = v;
        });

        return { status: response.status, headers: resHeaders, body };
      } catch (err) {
        clearTimeout(timer);

        if (err instanceof Error && err.name === 'AbortError') {
          lastError = new NetworkError(req.url, `Request timed out after ${this.cfg.timeout}ms`);
          // Timeout is retryable
          continue;
        }

        // HireIntelError subclasses should not be retried (except those already handled above)
        throw err;
      }
    }

    // All retries exhausted
    throw lastError ?? new NetworkError(req.url, 'All retry attempts exhausted');
  }

  // ── Debug logger ───────────────────────────────────────────────────────────

  private debugLog(message: string): void {
    if (this.cfg.debug) {
      console.log(`[hireintel] ${message}`);
    }
  }
}
