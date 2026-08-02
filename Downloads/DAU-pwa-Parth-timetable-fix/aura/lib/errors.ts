/**
 * Production error abstraction for AURA.
 *
 * Rules:
 * - Never leak stack traces, backend payloads, or internal paths to the client.
 * - Always log the real cause server-side with a stable `code` + `scope`.
 * - Prefer `AppError` over ad-hoc `throw new Error("...")` at domain boundaries.
 */

export const ErrorCode = {
  UNAUTHORIZED: "UNAUTHORIZED",
  FORBIDDEN: "FORBIDDEN",
  VALIDATION: "VALIDATION",
  NOT_FOUND: "NOT_FOUND",
  CONFLICT: "CONFLICT",
  PAYLOAD_TOO_LARGE: "PAYLOAD_TOO_LARGE",
  RATE_LIMITED: "RATE_LIMITED",
  BACKEND_UNAVAILABLE: "BACKEND_UNAVAILABLE",
  BACKEND_ERROR: "BACKEND_ERROR",
  NETWORK: "NETWORK",
  ABORTED: "ABORTED",
  INTERNAL: "INTERNAL",
} as const

export type ErrorCode = (typeof ErrorCode)[keyof typeof ErrorCode]

const USER_MESSAGES: Record<ErrorCode, string> = {
  UNAUTHORIZED: "Your session expired. Please sign in again.",
  FORBIDDEN: "You don't have permission to do that.",
  VALIDATION: "Invalid request. Please check your input and try again.",
  NOT_FOUND: "We couldn't find what you were looking for.",
  CONFLICT: "That action conflicts with the current state. Please refresh and try again.",
  PAYLOAD_TOO_LARGE: "That file is too large. Please try a smaller one.",
  RATE_LIMITED: "Question limit reached. Please wait a bit, or sign in with a DAU account.",
  BACKEND_UNAVAILABLE: "AURA is temporarily unavailable. Please try again shortly.",
  BACKEND_ERROR: "Something went wrong while processing your request. Please try again.",
  NETWORK: "Network error. Check your connection and try again.",
  ABORTED: "Request cancelled.",
  INTERNAL: "Something went wrong. Please try again.",
}

/** Phrases that must never reach the user (infra / debug copy). */
const TECHNICAL_MESSAGE =
  /\b(backend|upstream|api server|unreachable|econnrefused|enotfound|stack|traceback|internal server|fastapi|uvicorn|postgres|redis|localhost|127\.0\.0\.1|exception|typeiderror)\b/i

/**
 * Returns a user-safe message, or `undefined` if the input looks technical
 * so callers can fall back to the code default.
 */
export function sanitizePublicMessage(message?: string | null): string | undefined {
  if (!message) return undefined
  const trimmed = message.trim()
  if (!trimmed) return undefined
  if (trimmed.length > 180) return undefined
  if (trimmed.includes("\n")) return undefined
  if (/at\s+\S+\s+\(/.test(trimmed)) return undefined
  if (TECHNICAL_MESSAGE.test(trimmed)) return undefined
  return trimmed
}

export interface AppErrorOptions {
  /** Stable machine-readable code */
  code: ErrorCode
  /** HTTP status for API responses */
  status?: number
  /** Safe message shown to users. Defaults from ErrorCode. */
  message?: string
  /** Internal detail for logs only — never sent to clients */
  detail?: string
  cause?: unknown
}

const STATUS_BY_CODE: Record<ErrorCode, number> = {
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  VALIDATION: 400,
  NOT_FOUND: 404,
  CONFLICT: 409,
  PAYLOAD_TOO_LARGE: 413,
  RATE_LIMITED: 429,
  BACKEND_UNAVAILABLE: 502,
  BACKEND_ERROR: 502,
  NETWORK: 503,
  ABORTED: 499,
  INTERNAL: 500,
}

export class AppError extends Error {
  readonly code: ErrorCode
  readonly status: number
  readonly detail?: string
  readonly expose = true as const

  constructor(options: AppErrorOptions) {
    const safe =
      sanitizePublicMessage(options.message) || USER_MESSAGES[options.code]
    super(safe)
    this.name = "AppError"
    this.code = options.code
    this.status = options.status ?? STATUS_BY_CODE[options.code]
    this.detail = options.detail
    if (options.cause !== undefined) {
      // Preserve native cause when supported
      ;(this as Error & { cause?: unknown }).cause = options.cause
    }
  }

  static unauthorized(message?: string, detail?: string): AppError {
    return new AppError({ code: ErrorCode.UNAUTHORIZED, message, detail })
  }

  static forbidden(message?: string, detail?: string): AppError {
    return new AppError({ code: ErrorCode.FORBIDDEN, message, detail })
  }

  static validation(message?: string, detail?: string): AppError {
    return new AppError({ code: ErrorCode.VALIDATION, message, detail })
  }

  static notFound(message?: string, detail?: string): AppError {
    return new AppError({ code: ErrorCode.NOT_FOUND, message, detail })
  }

  static rateLimited(message?: string, detail?: string): AppError {
    return new AppError({ code: ErrorCode.RATE_LIMITED, message, detail })
  }

  static payloadTooLarge(message?: string, detail?: string): AppError {
    return new AppError({ code: ErrorCode.PAYLOAD_TOO_LARGE, message, detail })
  }

  static backendUnavailable(detail?: string, cause?: unknown): AppError {
    return new AppError({
      code: ErrorCode.BACKEND_UNAVAILABLE,
      detail,
      cause,
    })
  }

  static backendError(detail?: string, cause?: unknown): AppError {
    return new AppError({
      code: ErrorCode.BACKEND_ERROR,
      detail,
      cause,
    })
  }

  static internal(detail?: string, cause?: unknown): AppError {
    return new AppError({
      code: ErrorCode.INTERNAL,
      detail,
      cause,
    })
  }

  static network(cause?: unknown): AppError {
    return new AppError({ code: ErrorCode.NETWORK, cause })
  }

  static aborted(): AppError {
    return new AppError({ code: ErrorCode.ABORTED })
  }

  /** Map an upstream/backend HTTP status into a safe AppError. */
  static fromUpstreamStatus(status: number, detail?: string): AppError {
    if (status === 401) return AppError.unauthorized(undefined, detail)
    if (status === 403) return AppError.forbidden(undefined, detail)
    if (status === 404) return AppError.notFound(undefined, detail)
    if (status === 409) {
      return new AppError({ code: ErrorCode.CONFLICT, detail })
    }
    if (status === 413) return AppError.payloadTooLarge(undefined, detail)
    if (status === 429) return AppError.rateLimited(undefined, detail)
    if (status >= 500) return AppError.backendError(detail)
    return AppError.backendError(detail ?? `Upstream status ${status}`)
  }

  /** Map a Next.js / BFF response status on the client. */
  static fromHttpStatus(status: number, fallbackMessage?: string): AppError {
    const safe = sanitizePublicMessage(fallbackMessage)
    if (status === 401) return AppError.unauthorized(safe)
    if (status === 403) return AppError.forbidden(safe)
    if (status === 404) return AppError.notFound(safe)
    if (status === 413) return AppError.payloadTooLarge(safe)
    if (status === 429) return AppError.rateLimited(safe)
    if (status === 502 || status === 503 || status === 504) {
      return AppError.backendUnavailable(fallbackMessage)
    }
    if (status >= 400 && status < 500) {
      return AppError.validation(safe)
    }
    return AppError.internal(fallbackMessage)
  }

  static fromUnknown(err: unknown, fallbackCode: ErrorCode = ErrorCode.INTERNAL): AppError {
    if (err instanceof AppError) return err
    if (err instanceof DOMException && err.name === "AbortError") {
      return AppError.aborted()
    }
    if (err instanceof TypeError && /fetch|network|failed/i.test(err.message)) {
      return AppError.network(err)
    }
    if (err instanceof Error && err.message.trim()) {
      const safe = sanitizePublicMessage(err.message)
      // If the thrown message is already user-safe, keep it; otherwise hide it.
      if (safe) {
        return new AppError({
          code: fallbackCode,
          message: safe,
          detail: err.message,
          cause: err,
        })
      }
      return new AppError({
        code: guessCodeFromTechnicalMessage(err.message) ?? fallbackCode,
        detail: err.message,
        cause: err,
      })
    }
    return new AppError({
      code: fallbackCode,
      detail: typeof err === "string" ? err : undefined,
      cause: err,
    })
  }

  toPublicJSON(): { error: string; code: ErrorCode } {
    return {
      error: this.message,
      code: this.code,
    }
  }
}

export function isAppError(err: unknown): err is AppError {
  return err instanceof AppError
}

export function isAbortError(err: unknown): boolean {
  return (
    (err instanceof AppError && err.code === ErrorCode.ABORTED) ||
    (err instanceof DOMException && err.name === "AbortError")
  )
}

/** Safe user-facing message from any thrown value. */
export function getUserMessage(err: unknown, fallback = USER_MESSAGES.INTERNAL): string {
  if (err instanceof AppError) return err.message

  if (err instanceof Error && err.message.trim()) {
    const safe = sanitizePublicMessage(err.message)
    if (safe) return safe
    const code = guessCodeFromTechnicalMessage(err.message)
    if (code) return USER_MESSAGES[code]
  }

  if (typeof err === "string") {
    const safe = sanitizePublicMessage(err)
    if (safe) return safe
    const code = guessCodeFromTechnicalMessage(err)
    if (code) return USER_MESSAGES[code]
  }

  return fallback
}

function guessCodeFromTechnicalMessage(message: string): ErrorCode | undefined {
  const m = message.toLowerCase()
  if (m.includes("unauthorized") || m.includes("session expired")) {
    return ErrorCode.UNAUTHORIZED
  }
  if (m.includes("forbidden") || m.includes("permission")) {
    return ErrorCode.FORBIDDEN
  }
  if (m.includes("rate") || m.includes("limit reached") || m.includes("429")) {
    return ErrorCode.RATE_LIMITED
  }
  if (
    m.includes("backend") ||
    m.includes("unreachable") ||
    m.includes("unavailable") ||
    m.includes("api server") ||
    m.includes("502") ||
    m.includes("503")
  ) {
    return ErrorCode.BACKEND_UNAVAILABLE
  }
  if (m.includes("network") || m.includes("fetch failed")) {
    return ErrorCode.NETWORK
  }
  return undefined
}

export interface ErrorLogMeta {
  [key: string]: unknown
}

/** Structured error log — safe for production (no secrets assumed in meta). */
export function logError(scope: string, err: unknown, meta?: ErrorLogMeta): void {
  const appErr = isAppError(err) ? err : AppError.fromUnknown(err)
  const payload = {
    scope,
    code: appErr.code,
    status: appErr.status,
    message: appErr.message,
    detail: appErr.detail,
    meta,
    cause:
      err instanceof Error
        ? { name: err.name, message: err.message }
        : err === undefined
          ? undefined
          : String(err),
  }

  if (process.env.NODE_ENV === "production") {
    console.error(JSON.stringify({ level: "error", ...payload }))
  } else {
    console.error(`[${scope}]`, payload)
  }
}

export function userMessageForCode(code: ErrorCode): string {
  return USER_MESSAGES[code]
}
