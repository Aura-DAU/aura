import { renderHook, act } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useSession } from 'next-auth/react'
import {
  useAuraChat,
  readShedSignal,
  parseRetryAfterSeconds,
  shedErrorFor,
} from '../hooks/use-aura-chat'

vi.mock('next-auth/react', () => ({
  useSession: vi.fn(),
}))

function shedResponse(
  status: number,
  body: Record<string, unknown>,
  headers: Record<string, string>,
): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json', ...headers },
  })
}

describe('readShedSignal — capacity shed vs question quota', () => {
  it('recognises an edge 429 overload', async () => {
    const signal = await readShedSignal(
      shedResponse(
        429,
        { detail: 'busy', code: 'EDGE_OVERLOADED', shedBy: 'edge', retryAfter: 5 },
        { 'Retry-After': '5', 'X-Aura-Shed-By': 'edge' },
      ),
    )
    expect(signal).toEqual({ shedBy: 'edge', retryAfterSeconds: 5 })
  })

  it('recognises a backend admission 503', async () => {
    const signal = await readShedSignal(
      shedResponse(
        503,
        { code: 'ADMISSION_OVERLOADED', shedBy: 'backend', retryAfter: 5 },
        { 'Retry-After': '7', 'X-Aura-Shed-By': 'backend' },
      ),
    )
    // Header wins over the body value.
    expect(signal).toEqual({ shedBy: 'backend', retryAfterSeconds: 7 })
  })

  it('returns null for a real quota 429 so the quota branch still runs', async () => {
    const signal = await readShedSignal(
      new Response('Question limit reached', { status: 429 }),
    )
    expect(signal).toBeNull()
  })

  it('returns null for a BFF quota 429 carrying RATE_LIMITED', async () => {
    const signal = await readShedSignal(
      shedResponse(429, { error: 'Question limit reached', code: 'RATE_LIMITED' }, {}),
    )
    expect(signal).toBeNull()
  })

  it('falls back to the header alone when the body is not JSON', async () => {
    const signal = await readShedSignal(
      new Response('<html>429</html>', {
        status: 429,
        headers: { 'Retry-After': '5', 'X-Aura-Shed-By': 'edge' },
      }),
    )
    expect(signal).toEqual({ shedBy: 'edge', retryAfterSeconds: 5 })
  })

  it('ignores statuses that are not a shed', async () => {
    expect(await readShedSignal(new Response('', { status: 500 }))).toBeNull()
  })
})

describe('parseRetryAfterSeconds', () => {
  it('reads delta-seconds', () => {
    expect(parseRetryAfterSeconds('5')).toBe(5)
  })

  it('reads an HTTP-date', () => {
    const when = new Date(Date.now() + 12_000).toUTCString()
    expect(parseRetryAfterSeconds(when)).toBeGreaterThan(0)
  })

  it('falls back when missing or nonsense', () => {
    expect(parseRetryAfterSeconds(null)).toBe(5)
    expect(parseRetryAfterSeconds('soon')).toBe(5)
    expect(parseRetryAfterSeconds('-3')).toBe(5)
    expect(parseRetryAfterSeconds(null, 9)).toBe(9)
  })
})

describe('shedErrorFor', () => {
  it('produces a retryable, user-safe message', () => {
    expect(shedErrorFor({ shedBy: 'edge', retryAfterSeconds: 5 }).message).toBe(
      'AURA is busy right now — please retry in 5 seconds.',
    )
    expect(shedErrorFor({ shedBy: 'backend', retryAfterSeconds: 1 }).message).toBe(
      'AURA is busy right now — please retry in 1 second.',
    )
  })
})

describe('useAuraChat overload handling', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    global.fetch = vi.fn()
    vi.mocked(useSession).mockReturnValue({
      data: null,
      status: 'unauthenticated',
      update: vi.fn(),
    })
  })

  it('does not burn a guest\'s quota on an edge 429 overload', async () => {
    vi.mocked(global.fetch).mockImplementation(async (input: RequestInfo | URL) => {
      if (String(input) === '/api/chat') {
        return shedResponse(
          429,
          { error: 'busy', code: 'EDGE_OVERLOADED', shedBy: 'edge', retryAfter: 5 },
          { 'Retry-After': '5', 'X-Aura-Shed-By': 'edge' },
        )
      }
      return Response.json({ token: 'mock-token' })
    })

    const { result } = renderHook(() => useAuraChat())
    expect(result.current.remainingQuota).toBe(10)

    await act(async () => {
      await result.current.handleSendMessage('Hello AURA!')
    })

    // Capacity shed — the guest still has all 10 questions, and the message
    // says it is retryable rather than "limit reached".
    expect(result.current.remainingQuota).toBe(10)
    expect(result.current.errorMessage).toContain('busy')
    expect(result.current.errorMessage).toContain('5 seconds')
  })

  it('does not burn a guest\'s quota on a backend admission 503', async () => {
    vi.mocked(global.fetch).mockImplementation(async (input: RequestInfo | URL) => {
      if (String(input) === '/api/chat') {
        return shedResponse(
          503,
          { error: 'peak load', code: 'ADMISSION_OVERLOADED', shedBy: 'backend', retryAfter: 5 },
          { 'Retry-After': '5', 'X-Aura-Shed-By': 'backend' },
        )
      }
      return Response.json({ token: 'mock-token' })
    })

    const { result } = renderHook(() => useAuraChat())

    await act(async () => {
      await result.current.handleSendMessage('Hello AURA!')
    })

    expect(result.current.remainingQuota).toBe(10)
    expect(result.current.errorMessage).toContain('busy')
  })

  it('still pins a guest to 0 on a genuine quota 429', async () => {
    vi.mocked(global.fetch).mockImplementation(async (input: RequestInfo | URL) => {
      if (String(input) === '/api/chat') {
        return Response.json(
          { error: 'Question limit reached', code: 'RATE_LIMITED' },
          { status: 429 },
        )
      }
      return Response.json({ token: 'mock-token' })
    })

    const { result } = renderHook(() => useAuraChat())

    await act(async () => {
      await result.current.handleSendMessage('Hello AURA!')
    })

    expect(result.current.remainingQuota).toBe(0)
    expect(result.current.errorMessage).toContain('Question limit reached')
  })
})
