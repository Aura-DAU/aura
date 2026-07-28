"use client"

import { useCallback, useEffect, useRef, useState } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { WifiOff } from "lucide-react"
import { useAuraChat } from "@/hooks/use-aura-chat"
import { usePWAInstall } from "@/hooks/use-pwa-install"
import { DocumentViewerProvider } from "@/hooks/use-document-viewer"
import { Sidebar } from "./Sidebar"
import { Header } from "./Header"
import { MessageList } from "./MessageList"
import { Composer } from "./Composer"
import { EmptyState } from "./EmptyState"
import { ProfileModal } from "./ProfileModal"
import { DocumentViewerSheet } from "./DocumentViewerSheet"
import { InstallPromptBanner } from "./InstallPromptBanner"
import { AuroraBackground } from "@/components/ui/aurora-background"

export function ChatShell() {
  const chat = useAuraChat()
  const { canInstall, promptInstall } = usePWAInstall()
  const router = useRouter()
  const searchParams = useSearchParams()
  const promptHandled = useRef(false)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  // Desktop sidebar visibility. Default open for SSR/first paint; hydrate the
  // persisted preference after mount to avoid a hydration mismatch.
  const [desktopSidebarOpen, setDesktopSidebarOpen] = useState(true)
  const [profileOpen, setProfileOpen] = useState(false)
  // Always false for SSR + first client paint; only show after mount to avoid hydration mismatch.
  const [isOffline, setIsOffline] = useState(false)
  const [offlineReady, setOfflineReady] = useState(false)

  useEffect(() => {
    const goOnline = () => setIsOffline(false)
    const goOffline = () => setIsOffline(true)
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setOfflineReady(true)
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setIsOffline(!navigator.onLine)
    window.addEventListener("online", goOnline)
    window.addEventListener("offline", goOffline)
    return () => {
      window.removeEventListener("online", goOnline)
      window.removeEventListener("offline", goOffline)
    }
  }, [])

  // Consume ?prompt= from dashboard quick actions once, then clear the URL.
  useEffect(() => {
    if (promptHandled.current) return
    const prompt = searchParams.get("prompt")?.trim()
    if (!prompt) return
    promptHandled.current = true
    // Defer navigation until the router is ready (avoids "Router action before initialization").
    queueMicrotask(() => {
      router.replace("/", { scroll: false })
    })
    void chat.handleSendMessage(prompt)
    // eslint-disable-next-line react-hooks/exhaustive-deps -- one-shot handoff
  }, [searchParams, router])

  useEffect(() => {
    const stored = localStorage.getItem("aura-sidebar-open")
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (stored !== null) setDesktopSidebarOpen(stored === "1")
  }, [])

  const toggleDesktopSidebar = useCallback(() => {
    setDesktopSidebarOpen((prev) => {
      const next = !prev
      try {
        localStorage.setItem("aura-sidebar-open", next ? "1" : "0")
      } catch {
        /* storage unavailable */
      }
      return next
    })
  }, [])

  const handleRegenerate = useCallback(() => {
    const lastUser = chat.messages.findLast((m) => m.role === "user")
    if (lastUser) void chat.handleSendMessage(lastUser.content)
    // eslint-disable-next-line react-hooks/exhaustive-deps -- avoid depending on whole chat object
  }, [chat.messages, chat.handleSendMessage])

  const hasMessages = chat.messages.length > 0

  const composer = (
    <Composer
      inputText={chat.inputText}
      setInputText={chat.setInputText}
      loading={chat.loading}
      isRecording={chat.isRecording}
      isTranscribing={chat.isTranscribing}
      recordingVolume={chat.recordingVolume}
      onSend={chat.handleSendMessage}
      onMicClick={chat.handleMicClick}
      onStop={chat.stopGeneration}
      remainingQuota={chat.remainingQuota}
      variant={hasMessages ? "docked" : "centered"}
    />
  )

  return (
    <DocumentViewerProvider>
      <div className="flex h-[100dvh] overflow-hidden bg-theme-black text-neutral-100">
        <Sidebar
          threads={chat.threads}
          activeThreadId={chat.activeThreadId}
          onSelectThread={chat.setActiveThreadId}
          onNewChat={chat.startNewChat}
          onDeleteThread={chat.deleteThread}
          onOpenProfile={() => setProfileOpen(true)}
          studentProfile={chat.studentProfile}
          mobileOpen={sidebarOpen}
          onCloseMobile={() => setSidebarOpen(false)}
          collapsed={!desktopSidebarOpen}
          onCollapse={toggleDesktopSidebar}
        />

        <main className="relative flex min-w-0 flex-1 flex-col">
          <div className="pointer-events-none absolute inset-0 overflow-hidden">
            <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,rgba(244,80,59,0.06),transparent_55%),radial-gradient(ellipse_at_bottom_right,rgba(255,190,63,0.05),transparent_50%)]" />
          </div>

          <div className="relative z-10 flex h-full flex-col">
            <Header
              onToggleSidebar={() => setSidebarOpen(true)}
              onToggleDesktopSidebar={toggleDesktopSidebar}
              desktopSidebarOpen={desktopSidebarOpen}
              onClearChat={chat.handleClearChat}
              canInstall={canInstall}
              onInstall={() => {
                void promptInstall()
              }}
            />

            {offlineReady && isOffline ? (
              <div className="flex items-center justify-center gap-2 border-b border-theme-yellow/20 bg-theme-yellow/10 px-4 py-2 text-xs text-theme-yellow">
                <span className="size-2 animate-pulse rounded-full bg-theme-yellow" />
                <WifiOff className="size-3.5" />
                You&apos;re offline. Messages will fail until you reconnect.
              </div>
            ) : null}

            {chat.errorMessage ? (
              <div className="flex items-center justify-center border-b border-theme-red/20 bg-theme-red/10 px-4 py-2 text-xs text-theme-red">
                {chat.errorMessage}
              </div>
            ) : null}

            {hasMessages ? (
              <>
                <div className="flex-1 overflow-y-auto chat-v2-scroll">
                  <MessageList
                    messages={chat.messages}
                    loading={chat.loading}
                    thinkingStep={chat.thinkingStep}
                    activeCitations={chat.activeCitations}
                    onRegenerate={handleRegenerate}
                  />
                </div>
                {composer}
              </>
            ) : (
              <div className="flex-1 overflow-y-auto chat-v2-scroll">
                <AuroraBackground className="flex min-h-full items-center justify-center">
                  <EmptyState
                    onSelectPrompt={chat.handleSendMessage}
                    userName={chat.studentProfile.name}
                  >
                    {composer}
                  </EmptyState>
                </AuroraBackground>
              </div>
            )}
          </div>
        </main>

        <ProfileModal
          open={profileOpen}
          onClose={() => setProfileOpen(false)}
          profile={chat.studentProfile}
          onSave={chat.saveProfile}
        />

        <DocumentViewerSheet />
        <InstallPromptBanner />
      </div>
    </DocumentViewerProvider>
  )
}
