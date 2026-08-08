/** Module-level cache for citation source markdown. Shared by the viewer
 *  sheet and hover prefetch so reopening / hovering the same path is free. */
const documentCache = new Map<string, string>()

const inflight = new Map<string, Promise<string>>()

export function getCachedDocument(path: string): string | undefined {
  return documentCache.get(path)
}

export function setCachedDocument(path: string, content: string): void {
  documentCache.set(path, content)
}

/** Fetch a document into the cache without touching UI state. Dedupes
 *  concurrent requests for the same path. */
export function prefetchDocumentContent(path: string): Promise<string> {
  const cached = documentCache.get(path)
  if (cached !== undefined) return Promise.resolve(cached)

  const existing = inflight.get(path)
  if (existing) return existing

  const request = fetch(`/api/documents?path=${encodeURIComponent(path)}`)
    .then(async (res) => {
      if (!res.ok) {
        const body = (await res.json().catch(() => null)) as { error?: string } | null
        throw new Error(body?.error ?? "Failed to load document")
      }
      return res.json() as Promise<{ content: string }>
    })
    .then((data) => {
      documentCache.set(path, data.content)
      return data.content
    })
    .finally(() => {
      inflight.delete(path)
    })

  inflight.set(path, request)
  return request
}
