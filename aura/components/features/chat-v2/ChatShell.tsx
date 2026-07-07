"use client"

import { useCallback, useEffect, useState } from "react"
import { WifiOff } from "lucide-react"
import { useAuraChat } from "@/hooks/use-aura-chat"
import { Sidebar } from "./Sidebar"
import { Header } from "./Header"
import { MessageList } from "./MessageList"
import { Composer } from "./Composer"
import { EmptyState } from "./EmptyState"
import { ProfileModal } from "./ProfileModal"

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>
}

export function ChatShell() {
  const chat = useAuraChat()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [profileOpen, setProfileOpen] = useState(false)
  const [isOffline, setIsOffline] = useState(false)
  const [installPrompt, setInstallPrompt] = useState<BeforeInstallPromptEvent | null>(null)

  useEffect(() => {
    setIsOffline(!navigator.onLine)
    const goOnline = () => setIsOffline(false)
    const goOffline = () => setIsOffline(true)
    window.addEventListener("online", goOnline)
    window.addEventListener("offline", goOffline)
    return () => {
      window.removeEventListener("online", goOnline)
      window.removeEventListener("offline", goOffline)
    }
  }, [])

  useEffect(() => {
    const handler = (e: Event) => {
      e.preventDefault()
      setInstallPrompt(e as BeforeInstallPromptEvent)
    }
    window.addEventListener("beforeinstallprompt", handler)
    return () => window.removeEventListener("beforeinstallprompt", handler)
  }, [])

  const handleInstall = useCallback(async () => {
    if (!installPrompt) return
    await installPrompt.prompt()
    setInstallPrompt(null)
  }, [installPrompt])

  const handleRegenerate = useCallback(() => {
    const lastUser = chat.messages.findLast((m) => m.role === "user")
    if (lastUser) void chat.handleSendMessage(lastUser.content)
  }, [chat])

  const hasMessages = chat.messages.length > 0

  return (
    <div className="flex h-[100dvh] overflow-hidden bg-theme-black text-neutral-100">
      <Sidebar
        threads={chat.threads}
        activeThreadId={chat.activeThreadId}
        onSelectThread={chat.setActiveThreadId}
        onNewChat={chat.startNewChat}
        onDeleteThread={chat.deleteThread}
        onOpenProfile={() => setProfileOpen(true)}
        studentProfile={chat.studentProfile}
        userSession={chat.userSession}
        mobileOpen={sidebarOpen}
        onCloseMobile={() => setSidebarOpen(false)}
      />

      <main className="relative flex min-w-0 flex-1 flex-col">
        <div className="pointer-events-none absolute inset-0 overflow-hidden">
          <div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(255,255,255,0.025)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.025)_1px,transparent_1px)] bg-[size:24px_24px]" />
          <div className="absolute -left-24 -top-24 size-72 rounded-full bg-theme-red/20 blur-3xl" />
          <div className="absolute -bottom-24 -right-24 size-72 rounded-full bg-theme-yellow/20 blur-3xl" />
        </div>

        <div className="relative z-10 flex h-full flex-col">
          <Header
            onToggleSidebar={() => setSidebarOpen(true)}
            onClearChat={chat.handleClearChat}
            canInstall={Boolean(installPrompt)}
            onInstall={handleInstall}
            userSession={chat.userSession}
            onLogout={chat.logout}
          />

          {isOffline ? (
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

          <div className="flex-1 overflow-y-auto">
            {hasMessages ? (
              <MessageList
                messages={chat.messages}
                loading={chat.loading}
                thinkingStep={chat.thinkingStep}
                activeCitations={chat.activeCitations}
                onRegenerate={handleRegenerate}
              />
            ) : (
              <EmptyState onSelectPrompt={chat.handleSendMessage} />
            )}
          </div>

          <Composer
            inputText={chat.inputText}
            setInputText={chat.setInputText}
            loading={chat.loading}
            isRecording={chat.isRecording}
            isTranscribing={chat.isTranscribing}
            recordingVolume={chat.recordingVolume}
            onSend={chat.handleSendMessage}
            onMicClick={chat.handleMicClick}
          />
        </div>
      </main>

      <ProfileModal
        open={profileOpen}
        onClose={() => setProfileOpen(false)}
        profile={chat.studentProfile}
        onSave={chat.saveProfile}
      />
    </div>
  )
}
