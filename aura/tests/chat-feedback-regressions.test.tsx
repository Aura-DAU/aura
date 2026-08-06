import { act, render, renderHook, screen, waitFor } from "@testing-library/react"
import { beforeEach, describe, expect, it, vi } from "vitest"
import { useSession } from "next-auth/react"

import { Composer } from "../components/features/chat-ui/Composer"
import { ChatShell } from "../components/features/chat-ui/ChatShell"
import { FacultyDashboard } from "../components/features/chat-ui/FacultyDashboard"
import { ProfileModal } from "../components/features/chat-ui/ProfileModal"
import { Sidebar } from "../components/features/chat-ui/Sidebar"
import { useAuraChat } from "../hooks/use-aura-chat"

vi.mock("next-auth/react", () => ({
  useSession: vi.fn(),
}))

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn(), refresh: vi.fn() }),
  useSearchParams: () => new URLSearchParams(),
}))

const NAME_PROMPT =
  "Welcome to DAU! I noticed you haven't set your preferred name yet. What would you like me to call you?"

function mockSession(role: "student" | "faculty" | null) {
  vi.mocked(useSession).mockReturnValue(
    role
      ? {
          data: {
            user: {
              email: `${role}@dau.ac.in`,
              role,
              erpId: role === "faculty" ? "FAC001" : "202300001",
              department: "ICT",
            },
            expires: "9999-12-31T23:59:59.999Z",
          },
          status: "authenticated",
          update: vi.fn(),
        }
      : {
          data: null,
          status: "unauthenticated",
          update: vi.fn(),
        },
  )
}

function sse(events: string[]): Response {
  return new Response(`${events.map((event) => `data: ${event}\n\n`).join("")}data: [DONE]\n\n`, {
    status: 200,
    headers: { "Content-Type": "text/event-stream" },
  })
}

describe("chat feedback regressions", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    global.fetch = vi.fn()
    Object.defineProperty(window, "matchMedia", {
      configurable: true,
      value: vi.fn().mockImplementation(() => ({
        matches: false,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
      })),
    })
    Object.defineProperty(Element.prototype, "scrollIntoView", {
      configurable: true,
      value: vi.fn(),
    })
  })

  it("shows the missing-name prompt immediately even when chat history exists", async () => {
    mockSession("student")
    localStorage.setItem(
      "aura-threads-v2",
      JSON.stringify([
        {
          id: "existing-chat",
          title: "Existing chat",
          updatedAt: 200,
          messages: [{ role: "user", content: "Earlier question", timestamp: 200 }],
        },
      ]),
    )

    render(<ChatShell />)

    expect(await screen.findByText(NAME_PROMPT)).toBeInTheDocument()
  })

  it("restores the selected conversation after hydration", async () => {
    mockSession(null)
    localStorage.setItem(
      "aura-threads-v2",
      JSON.stringify([
        {
          id: "newer",
          title: "Newer chat",
          updatedAt: 200,
          messages: [{ role: "user", content: "newer", timestamp: 200 }],
        },
        {
          id: "selected",
          title: "Selected chat",
          updatedAt: 100,
          messages: [{ role: "user", content: "keep me open", timestamp: 100 }],
        },
      ]),
    )
    localStorage.setItem("aura-active-thread-v2", "selected")

    const { result } = renderHook(() => useAuraChat())

    await waitFor(() => expect(result.current.hasHydrated).toBe(true))
    expect(result.current.activeThreadId).toBe("selected")
    expect(result.current.messages[0]?.content).toBe("keep me open")
  })

  it("reuses the existing name prompt instead of creating another thread", async () => {
    mockSession(null)
    localStorage.setItem(
      "aura-threads-v2",
      JSON.stringify([
        {
          id: "current",
          title: "Current chat",
          updatedAt: 200,
          messages: [{ role: "user", content: "current", timestamp: 200 }],
        },
        {
          id: "welcome",
          title: "Welcome to AURA",
          updatedAt: 100,
          messages: [{ role: "assistant", content: NAME_PROMPT, timestamp: 100 }],
        },
      ]),
    )

    const { result } = renderHook(() => useAuraChat())
    await waitFor(() => expect(result.current.hasHydrated).toBe(true))

    act(() => result.current.insertGreeting(NAME_PROMPT))

    expect(result.current.threads).toHaveLength(2)
    expect(result.current.activeThreadId).toBe("welcome")
  })

  it("clears citations when the next answer has no source", async () => {
    mockSession(null)
    vi.mocked(global.fetch)
      .mockResolvedValueOnce(
        sse([
          JSON.stringify({ type: "text-delta", delta: "Grounded answer" }),
          JSON.stringify({
            type: "citations",
            citations: [{ file: "https://dau.ac.in/policy", title: "Policy" }],
          }),
          JSON.stringify({ type: "quota", remaining: 9 }),
        ]),
      )
      .mockResolvedValueOnce(
        sse([
          JSON.stringify({ type: "text-delta", delta: "Answer without a source" }),
          JSON.stringify({ type: "quota", remaining: 8 }),
        ]),
      )

    const { result } = renderHook(() => useAuraChat())

    await act(async () => {
      await result.current.handleSendMessage("First question")
    })
    expect(result.current.activeCitations).toHaveLength(1)

    await act(async () => {
      await result.current.handleSendMessage("Second question")
    })
    expect(result.current.activeCitations).toEqual([])
  })
})

describe("faculty chat presentation", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockSession("faculty")
  })

  it("uses the Ask AURA faculty prompt and a mobile-safe input size", () => {
    render(
      <Composer
        inputText=""
        setInputText={vi.fn()}
        loading={false}
        isRecording={false}
        isTranscribing={false}
        onSend={vi.fn()}
        onMicClick={vi.fn()}
      />,
    )

    const input = screen.getByLabelText("Message AURA")
    expect(input).toHaveAttribute("placeholder", "Ask AURA anything about DAU…")
    expect(input).toHaveAttribute("enterkeyhint", "send")
    expect(input).toHaveClass("text-base")
    expect(input).toHaveClass("caret-theme-yellow")
  })

  it("hides student-only and department fields from the faculty profile", () => {
    render(
      <ProfileModal
        open
        onClose={vi.fn()}
        profile={{ name: "", program: "", year: "", interests: "" }}
        onSave={vi.fn().mockResolvedValue(undefined)}
      />,
    )

    expect(screen.queryByText("Department")).not.toBeInTheDocument()
    expect(screen.queryByLabelText("Program")).not.toBeInTheDocument()
    expect(screen.queryByLabelText("Year")).not.toBeInTheDocument()
    expect(screen.getByLabelText("Name")).toBeInTheDocument()
    expect(screen.getByLabelText("Interests")).toBeInTheDocument()
  })

  it("does not show a department in the faculty sidebar account summary", () => {
    render(
      <Sidebar
        threads={[]}
        activeThreadId={null}
        onSelectThread={vi.fn()}
        onNewChat={vi.fn()}
        onDeleteThread={vi.fn()}
        onOpenProfile={vi.fn()}
        onOpenBugReport={vi.fn()}
        studentProfile={{ name: "Prof. User", program: "", year: "", interests: "" }}
        mobileOpen={false}
        onCloseMobile={vi.fn()}
        collapsed={false}
        onCollapse={vi.fn()}
      />,
    )

    expect(screen.queryByText("ICT")).not.toBeInTheDocument()
  })

  it("labels the faculty dashboard without a department", () => {
    global.fetch = vi.fn().mockResolvedValue(Response.json({}))

    render(<FacultyDashboard userName="User" onSelectPrompt={vi.fn()} />)

    expect(screen.getByText("Faculty")).toBeInTheDocument()
    expect(screen.queryByText("Information & Communication Technology")).not.toBeInTheDocument()
  })
})
