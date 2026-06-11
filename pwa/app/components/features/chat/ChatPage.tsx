"use client";

import React, { useState, useRef, useEffect } from "react";
import { useAuraChat } from "@/hooks/use-aura-chat";
import ChatSidebar from "@/app/components/features/chat/ChatSidebar";
import MessageStream from "@/app/components/features/chat/MessageStream";
import ProfileModal from "@/app/components/features/chat/ProfileModal";

export default function ChatPage() {
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
    recentThreads,
    studentProfile,
    saveProfile,
    handleMicClick,
    handleSendMessage,
    handleClearChat,
  } = useAuraChat();

  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [showProfileSettings, setShowProfileSettings] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
  }, [inputText]);

  const submit = () => {
    if (!inputText.trim() || loading || isRecording) return;
    void handleSendMessage(inputText);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    submit();
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  return (
    <div className="flex h-[100dvh] w-screen overflow-hidden bg-slate-900 text-slate-100 font-sans">
      <ChatSidebar
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        recentQueries={recentThreads}
        onSelectQuery={(q) => {
          setInputText(q);
          setSidebarOpen(false);
        }}
        studentProfile={studentProfile}
        onOpenProfile={() => setShowProfileSettings(true)}
        onClearChat={handleClearChat}
      />

      {sidebarOpen && (
        <div
          onClick={() => setSidebarOpen(false)}
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
        />
      )}

      <main className="flex flex-1 flex-col h-full bg-slate-900 relative">
        <header className="flex h-16 items-center justify-between px-6 border-b border-slate-800/60 bg-slate-900/90 backdrop-blur shrink-0">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(true)}
              className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-white lg:hidden"
              type="button"
            >
              <svg
                className="w-5 h-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2.5}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M4 6h16M4 12h16M4 18h16"
                />
              </svg>
            </button>
            <div className="flex items-center gap-2 text-xs text-slate-500">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
              Registry connected
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleClearChat}
              className="rounded-lg p-2 text-slate-400 hover:bg-slate-800 hover:text-red-400 transition-colors"
              title="Clear Thread"
              type="button"
            >
              <svg
                className="w-4 h-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2.5}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                />
              </svg>
            </button>
          </div>
        </header>

        {errorMessage && (
          <div className="bg-red-500/10 border-b border-red-500/25 px-6 py-3 flex items-center justify-between gap-3 text-red-300 text-xs font-bold shrink-0">
            <div className="flex items-center gap-2.5">
              <span className="w-5 h-5 rounded-full bg-red-500/20 text-red-400 flex items-center justify-center shrink-0">
                !
              </span>
              <span>{errorMessage}</span>
            </div>
            <button
              onClick={() => setErrorMessage(null)}
              className="text-red-400 hover:text-white transition-colors uppercase tracking-wider text-[9px] font-black"
              type="button"
            >
              Dismiss
            </button>
          </div>
        )}

        <MessageStream
          messages={messages}
          studentProfile={studentProfile}
          loading={loading}
          thinkingStep={thinkingStep}
          activeCitations={activeCitations}
          onSelectStarter={(text) => void handleSendMessage(text)}
          messagesEndRef={messagesEndRef}
        />

        <footer className="border-t border-slate-800/60 bg-slate-900/60 backdrop-blur p-4 shrink-0">
          <div className="mx-auto max-w-3xl">
            <form
              onSubmit={handleSubmit}
              className="relative flex flex-col gap-2 bg-slate-950 border border-slate-800 focus-within:border-orange-500/50 focus-within:ring-1 focus-within:ring-orange-500/20 rounded-2xl px-4 py-3 transition-all duration-200"
            >
              <textarea
                ref={textareaRef}
                rows={1}
                maxLength={2000}
                placeholder="Ask AURA about exams, curfews, clubs, maps, leave policies..."
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={loading || isRecording}
                className="w-full resize-none bg-transparent text-sm text-slate-200 placeholder-slate-500 focus:outline-none disabled:opacity-50 leading-relaxed max-h-[200px]"
              />
              <div className="flex items-center justify-between">
                <button
                  type="button"
                  onClick={handleMicClick}
                  disabled={loading || isTranscribing}
                  className={`p-2 rounded-lg transition-all duration-150 shrink-0 ${
                    isRecording
                      ? "bg-red-500 text-white animate-pulse"
                      : "text-slate-500 hover:bg-slate-900 hover:text-slate-200"
                  }`}
                  title={isRecording ? "Stop recording" : "Record voice input"}
                >
                {isTranscribing ? (
                  <svg
                    className="w-4 h-4 text-orange-500 animate-spin"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                ) : isRecording ? (
                  <svg
                    className="w-4 h-4 animate-pulse"
                    fill="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <rect x="6" y="6" width="12" height="12" rx="1.5" />
                  </svg>
                ) : (
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2.5}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M12 18.75a6 6 0 0 0 6-6v-1.5m-6 7.5a6 6 0 0 1-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 0 1-3-3V4.5a3 3 0 1 1 6 0v8.25a3 3 0 0 1-3 3Z"
                    />
                  </svg>
                )}
              </button>
                <button
                  type="submit"
                  disabled={!inputText.trim() || loading || isRecording}
                  className="bg-orange-500 text-white p-2 rounded-lg hover:bg-orange-600 disabled:opacity-30 disabled:cursor-not-allowed transition-colors shrink-0"
                  title="Send message"
                >
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2.5}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M5 12l14-7-7 14-2-5-5-2z"
                    />
                  </svg>
                </button>
              </div>
            </form>
            <p className="text-[11px] text-slate-500 text-center mt-2.5">
              AURA may make mistakes. Verify policies with the registry.
            </p>
          </div>
        </footer>
      </main>

      <ProfileModal
        show={showProfileSettings}
        profile={studentProfile}
        onClose={() => setShowProfileSettings(false)}
        onSave={(updatedProfile) => {
          saveProfile(updatedProfile);
          setShowProfileSettings(false);
        }}
      />
    </div>
  );
}
