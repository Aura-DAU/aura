import { toast } from "sonner"
import {
  AppError,
  ErrorCode,
  getUserMessage,
  isAbortError,
  isAppError,
  type ErrorCode as ErrorCodeType,
} from "@/lib/errors"

export { getUserMessage }

/** @deprecated Prefer getUserMessage — kept for existing call sites. */
export function getErrorMessage(err: unknown, fallback: string): string {
  return getUserMessage(err, fallback)
}

export function toastError(message: string): void {
  toast.error(message)
}

export function toastSuccess(message: string): void {
  toast.success(message)
}

/** Toast a safe message derived from any thrown value. Skips aborts. */
export function toastAppError(err: unknown, fallback?: string): void {
  if (isAbortError(err)) return
  toastError(getUserMessage(err, fallback))
}

export interface ApiErrorPayload {
  error?: string
  code?: ErrorCodeType
  message?: string
}

/**
 * Turn a failed `fetch` Response into an AppError.
 * Prefers `{ code, error }` from our BFF; falls back to status mapping.
 */
export async function appErrorFromResponse(res: Response): Promise<AppError> {
  let payload: ApiErrorPayload | null = null
  const contentType = res.headers.get("content-type") ?? ""

  try {
    if (contentType.includes("application/json")) {
      payload = (await res.json()) as ApiErrorPayload
    } else {
      const text = (await res.text()).trim()
      if (text) payload = { error: text }
    }
  } catch {
    payload = null
  }

  const headerCode = res.headers.get("X-Error-Code") as ErrorCodeType | null
  const code = payload?.code ?? headerCode ?? undefined
  const serverMessage = payload?.error ?? payload?.message

  if (code && code in ErrorCode) {
    return new AppError({
      code,
      status: res.status,
      message: serverMessage,
      detail: `HTTP ${res.status}`,
    })
  }

  return AppError.fromHttpStatus(res.status, serverMessage)
}

/**
 * If `res` is not ok, throw a mapped AppError. Returns res otherwise.
 */
export async function assertOk(res: Response): Promise<Response> {
  if (res.ok) return res
  throw await appErrorFromResponse(res)
}

export function toAppError(err: unknown): AppError {
  return isAppError(err) ? err : AppError.fromUnknown(err)
}
