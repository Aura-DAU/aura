import { render, screen, renderHook, act } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { Account, User } from 'next-auth'
import { Composer } from '../components/ui/composer'
import { useAuraChat } from '../hooks/use-aura-chat'
import { authOptions } from '../lib/auth/options'
import { useSession } from 'next-auth/react'

vi.mock('next-auth/react', () => ({
  useSession: vi.fn(),
}))

describe('Domain detection (guest vs DAU)', () => {
  it('assigns guest role to non-DAU emails', async () => {
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

    expect(result).toBe(true)
    expect(user.role).toBe('guest')
  })
})

describe('Unauthenticated Composer rendering', () => {
  it('renders "Sign in to ask questions" when unauthenticated', () => {
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
      />
    )

    expect(screen.getByText('Sign in to ask questions')).toBeInTheDocument()
    expect(screen.getByText('Sign In')).toBeInTheDocument()
  })
})

describe('useAuraChat 429 handling', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    global.fetch = vi.fn()
  })

  it('handles 429 error and updates remainingQuota', async () => {
    vi.mocked(useSession).mockReturnValue({
      data: {
        user: { email: 'student@dau.ac.in', role: 'student', erpId: '123' },
        expires: '9999-12-31T23:59:59.999Z',
      },
      status: 'authenticated',
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

    // Initial quota for student should be 5
    expect(result.current.remainingQuota).toBe(5)

    // Send a message to trigger fetch
    await act(async () => {
      await result.current.handleSendMessage("Hello AURA!")
    })

    // After 429, quota should be 0 and errorMessage should be set
    expect(result.current.remainingQuota).toBe(0)
    expect(result.current.errorMessage).toContain("Question limit reached")
  })
})
