// ─────────────────────────────────────────────────────────────────────────────
// @hireintel/sdk — Error Hierarchy
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Base error class for all HireIntel SDK errors.
 * Every error carries the HTTP status, the endpoint that failed,
 * and the raw response body from the server.
 */
export class HireIntelError extends Error {
  /** HTTP status code (0 for network / timeout errors). */
  readonly status: number;
  /** The API endpoint that returned the error. */
  readonly endpoint: string;
  /** Raw detail string from the server, if available. */
  readonly detail: string | undefined;

  constructor(message: string, status: number, endpoint: string, detail?: string) {
    super(message);
    this.name = 'HireIntelError';
    this.status = status;
    this.endpoint = endpoint;
    this.detail = detail;

    // Maintain proper prototype chain for instanceof checks
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

/** 400 — Request validation failed (missing fields, bad format). */
export class ValidationError extends HireIntelError {
  constructor(endpoint: string, detail?: string) {
    super(detail ?? 'Request validation failed', 400, endpoint, detail);
    this.name = 'ValidationError';
  }
}

/** 401 — Invalid or missing API key. */
export class AuthenticationError extends HireIntelError {
  constructor(endpoint: string, detail?: string) {
    super(detail ?? 'Authentication failed — check your API key', 401, endpoint, detail);
    this.name = 'AuthenticationError';
  }
}

/** 404 — Resource not found (resume, JD, interview, etc.). */
export class NotFoundError extends HireIntelError {
  constructor(endpoint: string, detail?: string) {
    super(detail ?? 'Resource not found', 404, endpoint, detail);
    this.name = 'NotFoundError';
  }
}

/** 422 — Unprocessable content (e.g. empty PDF, bad file format). */
export class UnprocessableError extends HireIntelError {
  constructor(endpoint: string, detail?: string) {
    super(detail ?? 'Unprocessable content', 422, endpoint, detail);
    this.name = 'UnprocessableError';
  }
}

/** 429 — Rate limit exceeded. */
export class RateLimitError extends HireIntelError {
  /** Seconds to wait before retrying, from Retry-After header. */
  readonly retryAfterSeconds: number | undefined;

  constructor(endpoint: string, detail?: string, retryAfter?: number) {
    super(detail ?? 'Rate limit exceeded — retry later', 429, endpoint, detail);
    this.name = 'RateLimitError';
    this.retryAfterSeconds = retryAfter;
  }
}

/** 500+ — Server-side failure. */
export class ServerError extends HireIntelError {
  constructor(endpoint: string, detail?: string) {
    super(detail ?? 'Internal server error', 500, endpoint, detail);
    this.name = 'ServerError';
  }
}

/** Network or timeout failure (status = 0). */
export class NetworkError extends HireIntelError {
  constructor(endpoint: string, detail?: string) {
    super(detail ?? 'Network request failed — check connectivity', 0, endpoint, detail);
    this.name = 'NetworkError';
  }
}

// ── Factory ──────────────────────────────────────────────────────────────────

/**
 * Maps an HTTP status code to the corresponding typed error.
 */
export function createErrorFromStatus(
  status: number,
  endpoint: string,
  detail?: string,
  retryAfter?: number,
): HireIntelError {
  switch (status) {
    case 400:
      return new ValidationError(endpoint, detail);
    case 401:
      return new AuthenticationError(endpoint, detail);
    case 404:
      return new NotFoundError(endpoint, detail);
    case 422:
      return new UnprocessableError(endpoint, detail);
    case 429:
      return new RateLimitError(endpoint, detail, retryAfter);
    default:
      if (status >= 500) return new ServerError(endpoint, detail);
      return new HireIntelError(detail ?? `HTTP ${status}`, status, endpoint, detail);
  }
}
