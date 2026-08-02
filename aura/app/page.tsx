import { Suspense } from "react"
import { ChatShell } from "@/components/features/chat-ui/ChatShell"
import { BrandMark } from "@/components/ui/brand-mark"

function ChatFallback() {
  return (
    <div className="flex h-[100dvh] flex-col items-center justify-center gap-3 bg-theme-black text-neutral-400">
      <BrandMark className="size-12 animate-pulse shadow-[0_0_32px_-6px_rgba(244,80,59,0.55)]" />
      <span className="text-sm tracking-wide">Loading AURA…</span>
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
