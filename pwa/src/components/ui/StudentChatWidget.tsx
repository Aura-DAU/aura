"use client";

import React, { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { useAuraChat } from "@/hooks/useAuraChat";
import MarkdownRenderer from "./MarkdownRenderer";

export default function StudentChatWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const {
    messages,
    inputText,
    setInputText,
    loading,
    isRecording,
    isTranscribing,
    handleMicClick,
    handleSendMessage,
  } = useAuraChat({ storageKey: "aura_widget_chat_history" });

  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSendMessage(inputText);
  };

  return (
    <div className="fixed bottom-24 md:bottom-8 right-6 z-50 flex flex-col items-end select-none">
      {/* Mini Chat Window */}
      {isOpen && (
        <div className="w-[320px] sm:w-[360px] h-[450px] bg-white border border-border-dau rounded-[28px] shadow-2xl flex flex-col overflow-hidden mb-4 animate-fade-in relative">
          {/* Header */}
          <div className="px-5 py-3.5 bg-slate-900 text-white flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-6 h-6 rounded-lg bg-primary-dau text-white font-black text-xs flex items-center justify-center">
                A
              </span>
              <div>
                <h3 className="text-xs font-black leading-tight">Ask AURA</h3>
                <span className="text-[8px] font-bold text-slate-400">PWA AI Companion</span>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Link
                href="/student/chat"
                onClick={() => setIsOpen(false)}
                className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
                title="Open full page chat"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
              </Link>
              <button
                onClick={() => setIsOpen(false)}
                className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
              >
                <svg className="w-4.5 h-4.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          {/* Messages list */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-slate-50/50 scrollbar-thin">
            {messages.map((msg, idx) => {
              const isAssistant = msg.role === "assistant";
              return (
                <div key={idx} className={`flex gap-2 max-w-[85%] ${isAssistant ? "mr-auto" : "ml-auto flex-row-reverse"}`}>
                  <div className={`rounded-xl p-3 border text-xs leading-relaxed ${
                    isAssistant ? "bg-white border-border-dau/60 text-slate-800" : "bg-primary-dau border-primary-dau text-white"
                  }`}>
                    <MarkdownRenderer content={msg.content} />
                  </div>
                </div>
              );
            })}
            {loading && (
              <div className="flex gap-2 mr-auto items-center">
                <div className="bg-white border border-border-dau/60 rounded-xl p-2.5 shadow-sm flex items-center gap-1.5">
                  <svg className="w-3.5 h-3.5 text-primary-dau animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  <span className="text-[9px] text-slate-400 font-bold">AURA is thinking...</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Mini form */}
          <form onSubmit={handleSubmit} className="p-3 border-t border-border-dau bg-white flex gap-2 items-center">
            <input
              type="text"
              placeholder="Type your question..."
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              disabled={loading || isRecording}
              className="flex-1 bg-slate-50 border border-border-dau rounded-xl px-3 py-2 text-xs font-medium text-slate-800 placeholder-slate-400 focus:outline-none focus:border-primary-dau"
            />
            <button
              type="button"
              onClick={handleMicClick}
              disabled={loading || isTranscribing}
              className={`p-2 rounded-xl border transition-all duration-150 shrink-0 ${
                isRecording 
                  ? "bg-red-500 border-red-500 text-white animate-pulse" 
                  : "bg-slate-50 border-border-dau hover:bg-slate-100 text-slate-500 hover:text-slate-700"
              }`}
              title={isRecording ? "Stop recording" : "Record voice input"}
            >
              {isTranscribing ? (
                <svg className="w-3.5 h-3.5 text-primary-dau animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
              ) : isRecording ? (
                <svg className="w-3.5 h-3.5 animate-pulse" fill="currentColor" viewBox="0 0 24 24">
                  <rect x="6" y="6" width="12" height="12" rx="1.5" />
                </svg>
              ) : (
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 18.75a6 6 0 0 0 6-6v-1.5m-6 7.5a6 6 0 0 1-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 0 1-3-3V4.5a3 3 0 1 1 6 0v8.25a3 3 0 0 1-3 3Z" />
                </svg>
              )}
            </button>
            <button
              type="submit"
              disabled={!inputText.trim() || loading || isRecording}
              className="bg-primary-dau text-white p-2 rounded-xl hover:bg-[#D7380A] disabled:opacity-40 transition-colors shrink-0"
            >
              <svg className="w-3.5 h-3.5 transform rotate-90" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 19l9-7-9-7v14z" />
              </svg>
            </button>
          </form>
        </div>
      )}

      {/* Floating Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-12 h-12 rounded-full bg-primary-dau hover:bg-[#D7380A] text-white flex items-center justify-center shadow-xl hover:scale-105 transition-all duration-150 relative border-2 border-white ring-4 ring-primary-dau/20 hover:rotate-12 cursor-pointer"
        title="Ask AURA Assistant"
      >
        {isOpen ? (
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        ) : (
          <svg className="w-5.5 h-5.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
        )}
      </button>
    </div>
  );
}
