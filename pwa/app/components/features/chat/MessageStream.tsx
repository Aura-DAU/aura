import React from "react";
import {
  ChatMessage,
  Citation,
  StudentProfile,
} from "@/app/api/chat.service";
import MessageItem from "@/app/components/features/chat/MessageItem";

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
    <div className="flex-1 overflow-y-auto px-6 py-8">
      <div className="mx-auto max-w-3xl space-y-6">
        {messages.length === 0 ? (
          <div className="flex flex-col items-start justify-center min-h-[40vh] pt-12 space-y-6 select-none">
            <div>
              <h2 className="text-3xl sm:text-5xl font-semibold tracking-tight leading-tight">
                Hello,{" "}
                <span className="bg-gradient-to-r from-orange-400 via-orange-500 to-red-500 bg-clip-text text-transparent">
                  {studentProfile.name.split(" ")[0]}
                </span>
                .
              </h2>
              <h3 className="text-2xl sm:text-4xl font-semibold text-slate-500 tracking-tight mt-2">
                How can I help you navigate the portal today?
              </h3>
            </div>

            <p className="text-sm text-slate-400 max-w-xl leading-relaxed">
              I am AURA, the Academic and University Resource Assistant. I scan
              verified Dhirubhai Ambani University registry documents,
              handbooks, and schedules to provide accurate policies.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 w-full pt-4">
              {STARTER_PROMPTS.map((prompt, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => onSelectStarter(prompt.text)}
                  className="flex items-center gap-3 text-left p-4 rounded-xl bg-slate-950/45 border border-slate-800/80 hover:border-orange-500/40 hover:bg-slate-950 transition-all duration-150 group"
                >
                  <span className="text-lg shrink-0 group-hover:scale-110 transition-transform">
                    {prompt.icon}
                  </span>
                  <span className="text-sm text-slate-300 group-hover:text-slate-100 leading-snug">
                    {prompt.text}
                  </span>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            {messages.map((msg, idx) => (
              <MessageItem
                key={idx}
                msg={msg}
                userInitial={studentProfile.name[0] ?? "M"}
              />
            ))}
          </div>
        )}

        {loading && (
          <div className="flex gap-4 items-start">
            <div className="w-8 h-8 rounded-lg bg-orange-500 text-white font-semibold text-xs flex items-center justify-center shrink-0">
              A
            </div>
            <div className="space-y-1 flex-1">
              <span className="block text-xs font-medium text-slate-400">
                AURA
              </span>
              <div className="flex items-center gap-2.5 bg-slate-950/40 border border-slate-800 rounded-xl px-3.5 py-3 max-w-sm">
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
                <span className="text-xs text-slate-400">
                  {thinkingStep}
                </span>
              </div>
            </div>
          </div>
        )}

        {activeCitations.length > 0 && !loading && (
          <div className="mt-8 border-t border-slate-800/80 pt-6">
            <span className="block text-xs font-medium text-slate-400 mb-3">
              Sources
            </span>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {activeCitations.map((cit, idx) => (
                <div
                  key={idx}
                  className="bg-slate-950/60 border border-slate-800 rounded-xl p-3.5 hover:border-orange-500/30 transition-all duration-150"
                >
                  <h4 className="text-sm font-medium text-slate-200 mb-1 leading-snug">
                    {cit.title}
                  </h4>
                  {cit.file && (
                    <span className="text-[11px] font-mono text-orange-400 block truncate">
                      {cit.file}
                    </span>
                  )}
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
