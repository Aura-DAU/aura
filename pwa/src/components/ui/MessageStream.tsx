import React from "react";
import { ChatMessage, Citation, StudentProfile } from "@/services/chat";
import MarkdownRenderer from "./MarkdownRenderer";

interface MessageStreamProps {
  messages: ChatMessage[];
  studentProfile: StudentProfile;
  loading: boolean;
  thinkingStep: string;
  activeCitations: Citation[];
  onSelectStarter: (text: string) => void;
  messagesEndRef: React.RefObject<HTMLDivElement | null>;
}

const STARTER_PROMPTS = [
  { text: "Lost ID card workflow", icon: "💳" },
  { text: "What is the curfew timing at hostellers HoR?", icon: "🌙" },
  { text: "How do I apply for a bonafide certificate?", icon: "📄" },
  { text: "Show technical clubs for AI or programming", icon: "💻" },
];

export default function MessageStream({
  messages,
  studentProfile,
  loading,
  thinkingStep,
  activeCitations,
  onSelectStarter,
  messagesEndRef,
}: MessageStreamProps) {
  return (
    <div className="flex-1 overflow-y-auto px-6 py-8 scrollbar-thin scrollbar-thumb-slate-800 scrollbar-track-transparent">
      <div className="mx-auto max-w-3xl space-y-6">
        {messages.length === 0 ? (
          <div className="flex flex-col items-start justify-center min-h-[40vh] pt-12 space-y-6 animate-fade-in select-none">
            <div>
              <h2 className="text-3xl sm:text-5xl font-black tracking-tight leading-tight">
                Hello, <span className="bg-gradient-to-r from-orange-400 via-primary-dau to-red-500 bg-clip-text text-transparent">{studentProfile.name.split(" ")[0]}</span>.
              </h2>
              <h3 className="text-2xl sm:text-4xl font-extrabold text-slate-500 tracking-tight mt-1.5">
                How can I help you navigate the portal today?
              </h3>
            </div>

            <p className="text-xs text-slate-400 max-w-xl font-medium leading-relaxed">
              I am **AURA**, the Academic and University Resource Assistant. I scan verified Dhirubhai Ambani University registry documents, handbooks, and schedules to provide accurate policies.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 w-full pt-4">
              {STARTER_PROMPTS.map((prompt, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => onSelectStarter(prompt.text)}
                  className="flex flex-col items-start gap-2.5 text-left p-4 rounded-2xl bg-slate-955/45 border border-slate-800/80 hover:border-primary-dau/30 hover:bg-slate-950 transition-all duration-150 group shadow-sm hover:shadow-lg"
                >
                  <span className="text-lg bg-slate-900 border border-slate-800 p-2 rounded-xl group-hover:scale-105 transition-transform">{prompt.icon}</span>
                  <span className="text-xs font-bold text-slate-300 group-hover:text-slate-100">{prompt.text}</span>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            {messages.map((msg, idx) => {
              const isAssistant = msg.role === "assistant";
              return (
                <div key={idx} className="flex gap-4 animate-fade-in">
                  <div className={`w-8 h-8 rounded-xl flex items-center justify-center font-black text-xs shrink-0 select-none shadow ${
                    isAssistant 
                      ? "bg-primary-dau/10 border border-primary-dau/25 text-primary-dau" 
                      : "bg-slate-800 border border-slate-700 text-slate-300"
                  }`}>
                    {isAssistant ? "AU" : "ME"}
                  </div>
                  
                  <div className="flex-1 space-y-1.5 min-w-0">
                    <span className="block text-[9px] font-black uppercase tracking-wider text-slate-505">
                      {isAssistant ? "AURA Assistant" : "You"}
                    </span>
                    <div className={`prose prose-invert max-w-none text-sm sm:text-base leading-relaxed ${
                      isAssistant ? "text-slate-200" : "text-slate-300 font-medium"
                    }`}>
                      <MarkdownRenderer content={msg.content} />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {loading && (
          <div className="flex gap-4 items-start animate-pulse">
            <div className="w-8 h-8 rounded-xl bg-primary-dau/10 border border-primary-dau/25 text-primary-dau font-black text-xs flex items-center justify-center shrink-0">
              AU
            </div>
            <div className="space-y-2 flex-1">
              <span className="block text-[9px] font-black uppercase tracking-wider text-slate-500">
                AURA Assistant
              </span>
              <div className="flex items-center gap-2.5 bg-slate-950/40 border border-slate-850 rounded-2xl p-3.5 max-w-sm">
                <svg className="w-3.5 h-3.5 text-primary-dau animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                <span className="text-[10px] text-slate-400 font-bold tracking-tight">
                  {thinkingStep}
                </span>
              </div>
            </div>
          </div>
        )}

        {activeCitations.length > 0 && !loading && (
          <div className="mt-8 border-t border-slate-800/80 pt-6 animate-fade-in">
            <span className="block text-[9px] font-black uppercase tracking-wider text-slate-500 mb-3">
              Scanned Registry References
            </span>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {activeCitations.map((cit, idx) => (
                <div key={idx} className="bg-slate-955/60 border border-slate-850 rounded-2xl p-4 shadow-sm hover:border-primary-dau/20 transition-all duration-150">
                  <h4 className="text-xs font-black text-slate-200 mb-1 leading-snug">{cit.title}</h4>
                  <span className="text-[9px] font-mono text-primary-dau font-black block truncate">
                    File: {cit.file}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>
    </div>
  );
}
