"use client";

import React, { useState, useRef } from "react";
import { useAuraChat } from "@/hooks/useAuraChat";
import ChatSidebar from "@/components/ui/ChatSidebar";
import MessageStream from "@/components/ui/MessageStream";
import ProfileModal from "@/components/ui/ProfileModal";

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

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSendMessage(inputText);
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-900 text-slate-100 font-sans">
      {/* 1. Left Sidebar */}
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

      {/* Backdrop for mobile sidebar */}
      {sidebarOpen && (
        <div
          onClick={() => setSidebarOpen(false)}
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
        />
      )}

      {/* 2. Main Chat Panel */}
      <main className="flex flex-1 flex-col h-full bg-slate-900 relative">
        {/* Top Header Bar */}
        <header className="flex h-16 items-center justify-between px-6 border-b border-slate-800/60 bg-slate-900/90 backdrop-blur shrink-0">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(true)}
              className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-white lg:hidden"
              type="button"
            >
              <svg className="w-5.5 h-5.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-[10px] font-black uppercase tracking-wider text-slate-400">
                L-RAG Registry Database Connected
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleClearChat}
              className="rounded-lg p-2 text-slate-400 hover:bg-slate-800 hover:text-red-400 transition-colors"
              title="Clear Thread"
              type="button"
            >
              <svg className="w-4.5 h-4.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        </header>

        {/* Inline Error State Banner replacing alert() */}
        {errorMessage && (
          <div className="bg-red-500/10 border-b border-red-500/25 px-6 py-3 flex items-center justify-between gap-3 text-red-250 text-xs font-bold animate-fade-in shrink-0">
            <div className="flex items-center gap-2.5">
              <span className="w-5 h-5 rounded-full bg-red-500/20 text-red-400 flex items-center justify-center shrink-0">!</span>
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

        {/* Messaging Stream Center Area */}
        <MessageStream
          messages={messages}
          studentProfile={studentProfile}
          loading={loading}
          thinkingStep={thinkingStep}
          activeCitations={activeCitations}
          onSelectStarter={handleSendMessage}
          messagesEndRef={messagesEndRef}
        />

        {/* Bottom Centered Fixed Input Bar */}
        <footer className="border-t border-slate-800/60 bg-slate-900/60 backdrop-blur p-4 shrink-0">
          <div className="mx-auto max-w-3xl">
            <form
              onSubmit={handleSubmit}
              className="relative flex items-center bg-slate-950 border border-slate-800 focus-within:border-primary-dau/50 rounded-2xl p-2.5 transition-all duration-200"
            >
              <input
                type="text"
                placeholder="Ask AURA about exams, curfews, clubs, maps, leave policies..."
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                disabled={loading || isRecording}
                className="flex-1 bg-transparent px-4 py-2 text-sm text-slate-200 placeholder-slate-500 focus:outline-none disabled:opacity-50"
              />
              <button
                type="button"
                onClick={handleMicClick}
                disabled={loading || isTranscribing}
                className={`p-2.5 rounded-xl border transition-all duration-150 shrink-0 mr-2 ${
                  isRecording 
                    ? "bg-red-500 border-red-500 text-white animate-pulse" 
                    : "bg-slate-900 border-slate-800 hover:bg-slate-850 text-slate-400 hover:text-slate-200"
                }`}
                title={isRecording ? "Stop recording" : "Record voice input"}
              >
                {isTranscribing ? (
                  <svg className="w-4.5 h-4.5 text-primary-dau animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                ) : isRecording ? (
                  <svg className="w-4.5 h-4.5 animate-pulse" fill="currentColor" viewBox="0 0 24 24">
                    <rect x="6" y="6" width="12" height="12" rx="1.5" />
                  </svg>
                ) : (
                  <svg className="w-4.5 h-4.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 18.75a6 6 0 0 0 6-6v-1.5m-6 7.5a6 6 0 0 1-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 0 1-3-3V4.5a3 3 0 1 1 6 0v8.25a3 3 0 0 1-3 3Z" />
                  </svg>
                )}
              </button>
              <button
                type="submit"
                disabled={!inputText.trim() || loading || isRecording}
                className="bg-primary-dau text-white p-2.5 rounded-xl hover:bg-[#D7380A] disabled:opacity-40 transition-colors shrink-0 shadow-lg shadow-primary-dau/10"
              >
                <svg className="w-4 h-4 transform rotate-90" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 19l9-7-9-7v14z" />
                </svg>
              </button>
            </form>
            <p className="text-[10px] text-slate-500 text-center mt-2.5">
              AURA assistant synthesizes grounded responses. Double-check official policies with the registry department.
            </p>
          </div>
        </footer>
      </main>

      {/* 3. Student Profile Personalization Settings Modal */}
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
