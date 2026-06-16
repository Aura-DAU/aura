"use client";
/* eslint-disable react-hooks/set-state-in-effect */

import { useEffect, useState } from "react";
import { Toaster, toast } from "sonner";
import { useAuraChat } from "@/hooks/use-aura-chat";
import ProfileModal from "./ProfileModal";
import Header from "./Header";
import Sidebar from "./Sidebar";
import MessageList from "./MessageList";
import Composer from "./Composer";
import EmptyState from "./EmptyState";

export default function ChatShell() {
  const {
    messages,
    inputText,
    setInputText,
    loading,
    thinkingStep,
    isRecording,
    isTranscribing,
    errorMessage,
    setErrorMessage,
    activeCitations,
    threads,
    activeThreadId,
    setActiveThreadId,
    startNewChat,
    deleteThread,
    studentProfile,
    saveProfile,
    handleMicClick,
    handleSendMessage,
    handleClearChat,
    userSession,
    logout,
  } = useAuraChat();

  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [showProfile, setShowProfile] = useState(false);
  const [micSupported, setMicSupported] = useState(true);
  const [isOffline, setIsOffline] = useState(false);

  useEffect(() => {
    const hasGetUserMedia = !!(
      typeof navigator !== "undefined" &&
      navigator.mediaDevices &&
      navigator.mediaDevices.getUserMedia
    );
    const hasMediaRecorder =
      typeof window !== "undefined" && "MediaRecorder" in window;
    setMicSupported(hasGetUserMedia && hasMediaRecorder);
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    setIsOffline(!window.navigator.onLine);
    const handleOnline = () => setIsOffline(false);
    const handleOffline = () => setIsOffline(true);
    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);
    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, []);

  useEffect(() => {
    if (errorMessage) {
      toast.error(errorMessage, {
        action: { label: "Dismiss", onClick: () => setErrorMessage(null) },
      });
    }
  }, [errorMessage, setErrorMessage]);

  const submit = () => {
    const text = inputText.trim();
    if (!text || loading || isRecording) return;
    void handleSendMessage(text);
  };

  const handleRegenerate = () => {
    const lastUser = [...messages].reverse().find((m) => m.role === "user");
    if (lastUser && !loading) {
      void handleSendMessage(lastUser.content);
    }
  };

  const hasMessages = messages.length > 0;

  return (
    <div className="flex h-[100dvh] w-full overflow-hidden bg-theme-black text-foreground">
      <Sidebar
        threads={threads}
        activeThreadId={activeThreadId}
        onSelectThread={(id) => {
          setActiveThreadId(id);
          setMobileSidebarOpen(false);
        }}
        onDeleteThread={deleteThread}
        onNewChat={() => {
          startNewChat();
          setMobileSidebarOpen(false);
        }}
        userSession={userSession}
        onOpenProfile={() => setShowProfile(true)}
        mobileOpen={mobileSidebarOpen}
        onCloseMobile={() => setMobileSidebarOpen(false)}
      />

      <main className="relative flex h-full min-w-0 flex-1 flex-col">
        {/* ambient backdrop: grid + blurred color blobs */}
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px]"
        />
        <div
          aria-hidden
          className="pointer-events-none absolute -left-20 -top-20 h-[310px] w-[310px] rounded-full bg-theme-red opacity-20 blur-[100px]"
        />
        <div
          aria-hidden
          className="pointer-events-none absolute -right-20 bottom-1/3 h-[310px] w-[310px] rounded-full bg-theme-yellow opacity-15 blur-[100px]"
        />

        <div className="relative z-10 flex h-full flex-col">
          <Header
            onOpenMobileSidebar={() => setMobileSidebarOpen(true)}
            userSession={userSession}
            onLogout={() => void logout()}
            onClearChat={handleClearChat}
            canClearChat={hasMessages}
          />

          {isOffline && (
            <div className="flex items-center gap-2 border-b border-theme-yellow/30 bg-theme-yellow/10 px-4 py-2 text-xs font-medium text-theme-yellow">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-theme-yellow" />
              <span>You&apos;re offline — old chats still load.</span>
            </div>
          )}

          <div className="chat-v2-scroll flex-1 overflow-y-auto">
            {hasMessages ? (
              <MessageList
                messages={messages}
                loading={loading}
                thinkingStep={thinkingStep}
                citations={activeCitations}
                onRegenerate={handleRegenerate}
              />
            ) : (
              <EmptyState
                onSelectStarter={(text) => void handleSendMessage(text)}
              />
            )}
          </div>

          <div className="shrink-0 border-t border-theme-gray-light/60 bg-theme-black/60 backdrop-blur">
            <Composer
              value={inputText}
              onChange={setInputText}
              onSubmit={submit}
              disabled={loading || isOffline}
              isRecording={isRecording}
              isTranscribing={isTranscribing}
              micSupported={micSupported}
              onMicClick={handleMicClick}
              placeholder={isOffline ? "You're offline — reconnect to chat." : undefined}
            />
          </div>
        </div>
      </main>

      <ProfileModal
        show={showProfile}
        profile={studentProfile}
        onClose={() => setShowProfile(false)}
        onSave={(updated) => {
          void saveProfile(updated);
          setShowProfile(false);
        }}
        userSession={userSession}
      />

      <Toaster
        theme="dark"
        position="bottom-right"
        toastOptions={{
          style: {
            background: "#1A1A1A",
            border: "1px solid #2A2A2A",
            color: "hsl(0 0% 98%)",
          },
        }}
      />
    </div>
  );
}
