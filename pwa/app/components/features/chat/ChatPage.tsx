"use client";

import React, { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { useAuraChat } from "@/hooks/use-aura-chat";
import ChatSidebar from "@/app/components/features/chat/ChatSidebar";
import MessageStream from "@/app/components/features/chat/MessageStream";
import ProfileModal from "@/app/components/features/chat/ProfileModal";
import { ThemeToggle } from "@/app/components/ThemeToggle";

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
    userSession,
    logout,
  } = useAuraChat();

  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [desktopSidebarCollapsed, setDesktopSidebarCollapsed] = useState(false);
  const [showProfileSettings, setShowProfileSettings] = useState(false);
  const [micSupported, setMicSupported] = useState(true);
  const [confirmClear, setConfirmClear] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const confirmTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
  }, [inputText]);

  useEffect(() => {
    const hasGetUserMedia = !!(
      typeof navigator !== "undefined" &&
      navigator.mediaDevices &&
      navigator.mediaDevices.getUserMedia
    );
    const hasMediaRecorder =
      typeof window !== "undefined" && "MediaRecorder" in window;
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setMicSupported(hasGetUserMedia && hasMediaRecorder);
  }, []);

  useEffect(() => {
    return () => {
      if (confirmTimeoutRef.current) clearTimeout(confirmTimeoutRef.current);
    };
  }, []);

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

  const handleClearClick = () => {
    if (confirmClear) {
      if (confirmTimeoutRef.current) clearTimeout(confirmTimeoutRef.current);
      setConfirmClear(false);
      handleClearChat();
    } else {
      setConfirmClear(true);
      confirmTimeoutRef.current = setTimeout(() => setConfirmClear(false), 3000);
    }
  };

  return (
    <div className="flex h-[100dvh] w-screen overflow-hidden bg-white dark:bg-slate-950 text-slate-900 dark:text-slate-100 font-sans">
      <ChatSidebar
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        collapsed={desktopSidebarCollapsed}
        recentQueries={recentThreads}
        onSelectQuery={(q) => {
          setInputText(q);
          setSidebarOpen(false);
        }}
        studentProfile={studentProfile}
        onOpenProfile={() => setShowProfileSettings(true)}
        onClearChat={handleClearChat}
        userSession={userSession}
      />

      {sidebarOpen && (
        <div
          onClick={() => setSidebarOpen(false)}
          className="fixed inset-0 z-40 bg-black/30 lg:hidden"
        />
      )}

      <main className="flex flex-1 flex-col h-full bg-white dark:bg-slate-950 relative">
        <header className="flex h-16 items-center justify-between px-6 border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 shrink-0">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setSidebarOpen(true)}
              className="rounded-md p-1.5 text-slate-500 hover:bg-slate-100 hover:text-slate-900 lg:hidden"
              type="button"
            >
              <svg
                className="w-5 h-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M4 6h16M4 12h16M4 18h16"
                />
              </svg>
            </button>
            <button
              onClick={() => setDesktopSidebarCollapsed((v) => !v)}
              className="hidden lg:inline-flex rounded-md p-1.5 text-slate-500 hover:bg-slate-100 hover:text-slate-900"
              type="button"
              title={desktopSidebarCollapsed ? "Show sidebar" : "Hide sidebar"}
            >
              <svg
                className="w-5 h-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                {desktopSidebarCollapsed ? (
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M13.5 4.5 21 12l-7.5 7.5M3 12h17.25"
                  />
                ) : (
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M10.5 19.5 3 12l7.5-7.5M21 12H3.75"
                  />
                )}
              </svg>
            </button>
            <span className="text-sm font-medium text-slate-700 ml-1 hidden sm:inline">
              AURA — Academic & University Resource Assistant
            </span>
          </div>

          <div className="flex items-center gap-3">
            <ThemeToggle />
            {userSession ? (
              <div className="flex items-center gap-3">
                <div className="hidden sm:flex flex-col text-right leading-tight">
                  <span className="text-xs font-semibold text-slate-800 dark:text-slate-200">
                    {userSession.name}
                  </span>
                  <span className="text-[10px] text-slate-500 capitalize">
                    {userSession.role}
                  </span>
                </div>
                <button
                  onClick={logout}
                  className="rounded-md px-3.5 py-1.5 text-xs font-semibold border border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors hover:cursor-pointer"
                >
                  Logout
                </button>
              </div>
            ) : (
              <Link
                href="/login"
                className="rounded-md px-4 py-1.5 text-sm font-medium transition-colors bg-brand-600 text-white hover:bg-brand-700"
              >
                Login
              </Link>
            )}
            <button
              onClick={handleClearClick}
              className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors flex items-center gap-1.5 ${
                confirmClear
                  ? "bg-red-50 text-red-600 border border-red-200"
                  : "text-slate-500 hover:bg-slate-100 hover:text-slate-700 border border-transparent"
              }`}
              title="Clear conversation"
              type="button"
            >
              <svg
                className="w-4 h-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                />
              </svg>
              {confirmClear ? "Confirm clear?" : "Clear chat"}
            </button>
          </div>
        </header>

        {errorMessage && (
          <div className="bg-amber-50 border-b border-amber-200 px-6 py-2.5 flex items-center justify-between gap-3 text-amber-800 text-[13px] shrink-0">
            <div className="flex items-center gap-2.5">
              <span className="w-5 h-5 rounded-full bg-amber-100 text-amber-700 flex items-center justify-center shrink-0 text-xs">
                !
              </span>
              <span>{errorMessage}</span>
            </div>
            <button
              onClick={() => setErrorMessage(null)}
              className="text-amber-700 hover:text-amber-900 transition-colors text-[13px] font-medium"
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
          userSession={userSession}
        />

        <footer className="border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 p-4 shrink-0">
          <div className="mx-auto max-w-3xl">
            <form
              onSubmit={handleSubmit}
              className="relative flex flex-col gap-2 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 focus-within:border-brand-500 focus-within:ring-1 focus-within:ring-brand-100 dark:focus-within:ring-brand-900 rounded-lg px-4 py-3 transition-colors duration-150"
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
                className="w-full resize-none bg-transparent text-sm text-slate-800 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none disabled:opacity-50 leading-relaxed max-h-[200px]"
              />
              <div className="flex items-center justify-between">
                {micSupported ? (
                  <button
                    type="button"
                    onClick={handleMicClick}
                    disabled={loading || isTranscribing}
                    className={`p-2 rounded-md transition-colors duration-150 shrink-0 ${
                      isRecording
                        ? "bg-red-500 text-white"
                        : "text-slate-500 hover:bg-slate-100 hover:text-slate-700"
                    }`}
                    title={isRecording ? "Stop recording" : "Record voice input"}
                  >
                    {isTranscribing ? (
                      <svg
                        className="w-4 h-4 text-brand-600 animate-spin"
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
                      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                        <rect x="6" y="6" width="12" height="12" rx="1.5" />
                      </svg>
                    ) : (
                      <svg
                        className="w-4 h-4"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                        strokeWidth={2}
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M12 18.75a6 6 0 0 0 6-6v-1.5m-6 7.5a6 6 0 0 1-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 0 1-3-3V4.5a3 3 0 1 1 6 0v8.25a3 3 0 0 1-3 3Z"
                        />
                      </svg>
                    )}
                  </button>
                ) : (
                  <span
                    className="p-2 rounded-md text-slate-300 cursor-not-allowed shrink-0"
                    title="Voice input is not available in this browser."
                  >
                    <svg
                      className="w-4 h-4"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      strokeWidth={2}
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M12 18.75a6 6 0 0 0 6-6v-1.5m-6 7.5a6 6 0 0 1-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 0 1-3-3V4.5a3 3 0 1 1 6 0v8.25a3 3 0 0 1-3 3Z"
                      />
                    </svg>
                  </span>
                )}
                <button
                  type="submit"
                  disabled={!inputText.trim() || loading || isRecording}
                  className="bg-brand-600 text-white p-2 rounded-md hover:bg-brand-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors shrink-0"
                  title="Send message"
                >
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2}
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
            <p className="text-[12px] text-slate-400 text-center mt-2.5">
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
        userSession={userSession}
      />
    </div>
  );
}
