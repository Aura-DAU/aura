import { Suspense } from "react"
import { ChatShell } from "@/components/features/chat-ui/ChatShell"

function ChatFallback() {
  return (
    <div className="flex h-[100dvh] items-center justify-center bg-theme-black text-neutral-400">
      <span className="text-sm">Loading AURA…</span>
    </div>
  )
}

export default function Page() {
  return (
    <Suspense fallback={<ChatFallback />}>
      <ChatShell />
    </Suspense>
  )
}
