import { render, screen, renderHook, act } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { Account, User } from 'next-auth'
import { Composer } from '../components/features/chat-ui/Composer'
import { useAuraChat } from '../hooks/use-aura-chat'
import { authOptions } from '../lib/auth/options'
import { useSession } from 'next-auth/react'

vi.mock('next-auth/react', () => ({
  useSession: vi.fn(),
}))

describe('Domain restriction (only @dau.ac.in may sign in)', () => {
  it('rejects non-DAU emails instead of signing them in as guest', async () => {
    const user = { email: 'test@gmail.com' } as User & { role?: string }
    const account = { provider: 'google' } as Account
    const signIn = authOptions.callbacks?.signIn
    expect(signIn).toBeDefined()

    const result = await signIn!({
      user,
      account,
      profile: undefined,
      email: undefined,
      credentials: undefined,
    })

    // Non-@dau.ac.in Google accounts (including @daiict.ac.in and personal
    // Gmail) are redirected to the login page instead of being let in as
    // guest — guest access is now anonymous/no-login only.
    expect(result).toBe('/login?error=DomainNotAllowed')
    expect(user.role).toBeUndefined()
  })
})

describe('Unauthenticated (guest) Composer rendering', () => {
  it('lets a guest with quota remaining type and send normally', () => {
    vi.mocked(useSession).mockReturnValue({
      data: null,
      status: 'unauthenticated',
      update: vi.fn(),
    })

    render(
      <Composer
        inputText=""
        setInputText={vi.fn()}
        loading={false}
        isRecording={false}
        isTranscribing={false}
        onSend={vi.fn()}
        onMicClick={vi.fn()}
        remainingQuota={10}
      />
    )

    // Guests get a normal composer, not a sign-in wall — quota is enforced
    // separately (see server/rag/pipeline/rate_limiter.py), not by blocking
    // input outright.
    expect(screen.getByLabelText('Message AURA')).toBeInTheDocument()
    expect(screen.getByText('10 messages left')).toBeInTheDocument()
  })

  it('prompts a guest to sign in once their daily quota is exhausted', () => {
    vi.mocked(useSession).mockReturnValue({
      data: null,
      status: 'unauthenticated',
      update: vi.fn(),
    })

    render(
      <Composer
        inputText=""
        setInputText={vi.fn()}
        loading={false}
        isRecording={false}
        isTranscribing={false}
        onSend={vi.fn()}
        onMicClick={vi.fn()}
        remainingQuota={0}
      />
    )

    expect(screen.getByText("You've used all your free questions for today.")).toBeInTheDocument()
    expect(screen.getByText('Sign in with @dau.ac.in for unlimited access')).toBeInTheDocument()
  })
})

describe('useAuraChat 429 handling', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    global.fetch = vi.fn()
  })

  it('handles 429 error and updates remainingQuota for a guest', async () => {
    // No session at all — anonymous guest, tracked via the local
    // "aura-quota-guest" mirror of the server-enforced 10/day cookie quota.
    vi.mocked(useSession).mockReturnValue({
      data: null,
      status: 'unauthenticated',
      update: vi.fn(),
    })

    const mockFetch = vi.mocked(global.fetch)
    mockFetch.mockImplementation(async (input: RequestInfo | URL) => {
      const url = String(input)
      if (url === '/api/chat') {
        return new Response(null, { status: 429 })
      }
      return Response.json({ token: 'mock-token' })
    })

    const { result } = renderHook(() => useAuraChat())

    // Initial quota for an anonymous guest should be 10
    expect(result.current.remainingQuota).toBe(10)

    // Send a message to trigger fetch
    await act(async () => {
      await result.current.handleSendMessage("Hello AURA!")
    })

    // After 429, quota should be 0 and errorMessage should be set
    expect(result.current.remainingQuota).toBe(0)
    expect(result.current.errorMessage).toContain("Question limit reached")
  })

  it('shows no quota limit for a signed-in @dau.ac.in account', async () => {
    vi.mocked(useSession).mockReturnValue({
      data: {
        user: { email: 'student@dau.ac.in', role: 'student', erpId: '123' },
        expires: '9999-12-31T23:59:59.999Z',
      },
      status: 'authenticated',
      update: vi.fn(),
    })

    const { result } = renderHook(() => useAuraChat())

    // Verified DAU accounts are unlimited — no counter shown.
    expect(result.current.remainingQuota).toBeNull()
  })
})
