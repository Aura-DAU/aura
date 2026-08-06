/** Extract a user-facing error message from a failed fetch Response. */
export async function apiErrorMessage(
  res: Response,
  fallback = "Request failed",
): Promise<string> {
  try {
    const body: unknown = await res.json()
    if (body && typeof body === "object") {
      const record = body as Record<string, unknown>
      if (typeof record.error === "string" && record.error.trim()) return record.error
      if (typeof record.detail === "string" && record.detail.trim()) return record.detail
      if (typeof record.message === "string" && record.message.trim()) return record.message
    }
  } catch {
    /* non-JSON body */
  }
  return fallback
}
