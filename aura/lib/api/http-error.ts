import { NextResponse } from "next/server"
import { AppError, ErrorCode, isAppError, logError } from "@/lib/errors"

export type ErrorBody = {
  error: string
  code: ErrorCode
}

/** JSON error response with stable `{ error, code }` shape. */
export function jsonError(err: AppError, init?: ResponseInit): NextResponse<ErrorBody> {
  return NextResponse.json(err.toPublicJSON(), {
    status: err.status,
    ...init,
  })
}

/** Plain-text error response (SSE / streaming routes). */
export function textError(err: AppError): Response {
  return new Response(err.message, {
    status: err.status,
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
      "X-Error-Code": err.code,
    },
  })
}

/**
 * Convert any thrown value into a logged, client-safe JSON response.
 * Use at the outer edge of route handlers.
 */
export function handleRouteError(scope: string, err: unknown): NextResponse<ErrorBody> {
  const appErr = isAppError(err) ? err : AppError.fromUnknown(err)
  logError(scope, appErr)
  return jsonError(appErr)
}

export function handleRouteTextError(scope: string, err: unknown): Response {
  const appErr = isAppError(err) ? err : AppError.fromUnknown(err)
  logError(scope, appErr)
  return textError(appErr)
}

/** Parse JSON body or throw a validation AppError. */
export async function readJsonBody(req: Request): Promise<unknown> {
  try {
    return await req.json()
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  } catch (cause) {
    throw AppError.validation("Invalid JSON", "Request body is not valid JSON")
  }
}
