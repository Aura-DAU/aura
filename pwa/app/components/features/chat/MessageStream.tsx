import React from "react";
import {
  ChatMessage,
  Citation,
  StudentProfile,
} from "@/app/api/chat.service";

interface MessageStreamProps {
  messages: ChatMessage[];
  studentProfile: StudentProfile;
  loading: boolean;
  thinkingStep: string;
  activeCitations: Citation[];
  onSelectStarter: (text: string) => void;
  messagesEndRef: React.RefObject<HTMLDivElement | null>;
}

function parseInline(text: string): React.ReactNode[] {
  const cleaned = text.replace(/\[at\]/gi, "@").replace(/\[dot\]/gi, ".");
  const regex = /(\*\*.*?\*\*|\[Source:\s*[^\]]+\]|\[[^\]]+\]\([^)]+\)|https?:\/\/[^\s,)]+|[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/g;
  
  const parts = cleaned.split(regex);
  return parts.map((part, index) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={index} className="font-semibold text-orange-400">
          {part.slice(2, -2)}
        </strong>
      );
    }
    if (part.startsWith("[Source:") && part.endsWith("]")) {
      const sourceName = part.slice(9, -1);
      return (
        <span
          key={index}
          className="inline-flex items-center px-1.5 py-0.5 rounded-md text-[10px] font-medium bg-slate-900/80 text-slate-400 ml-1.5 border border-slate-700/60"
        >
          Source: {sourceName}
        </span>
      );
    }
    if (part.startsWith("[") && part.includes("](")) {
      const match = part.match(/\[([^\]]+)\]\(([^)]+)\)/);
      if (match) {
        return (
          <a
            key={index}
            href={match[2]}
            target="_blank"
            rel="noopener noreferrer"
            className="text-orange-400 hover:text-orange-300 underline font-medium break-all"
          >
            {match[1]}
          </a>
        );
      }
    }
    if (part.startsWith("http://") || part.startsWith("https://")) {
      return (
        <a
          key={index}
          href={part}
          target="_blank"
          rel="noopener noreferrer"
          className="text-orange-400 hover:text-orange-300 underline font-medium break-all"
        >
          {part}
        </a>
      );
    }
    if (part.includes("@") && !part.includes(" ")) {
      return (
        <a
          key={index}
          href={`mailto:${part}`}
          className="text-orange-400 hover:text-orange-300 underline"
        >
          {part}
        </a>
      );
    }
    return part;
  });
}

function parseMarkdown(text: string): React.ReactNode[] {
  const lines = text.split("\n");
  const elements: React.ReactNode[] = [];
  
  let currentList: React.ReactNode[] = [];
  let listKey = 0;
  
  const flushList = () => {
    if (currentList.length > 0) {
      elements.push(
        <ul key={`list-${listKey++}`} className="list-disc pl-5 mb-4 space-y-1">
          {currentList}
        </ul>
      );
      currentList = [];
    }
  };
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();
    
    if (trimmed === "") {
      flushList();
      continue;
    }
    
    const headingMatch = line.match(/^(#{1,6})\s+(.*)$/);
    if (headingMatch) {
      flushList();
      const level = headingMatch[1].length;
      const content = headingMatch[2];
      const parsedContent = parseInline(content);
      
      switch (level) {
        case 1:
          elements.push(
            <h1 key={`h1-${i}`} className="text-xl font-bold mt-6 mb-3 text-white">
              {parsedContent}
            </h1>
          );
          break;
        case 2:
          elements.push(
            <h2 key={`h2-${i}`} className="text-lg font-bold mt-5 mb-2.5 text-white">
              {parsedContent}
            </h2>
          );
          break;
        case 3:
          elements.push(
            <h3 key={`h3-${i}`} className="text-base font-semibold mt-4 mb-2 text-white">
              {parsedContent}
            </h3>
          );
          break;
        default:
          elements.push(
            <h4 key={`h4-${i}`} className="text-sm font-semibold mt-3 mb-1.5 text-white">
              {parsedContent}
            </h4>
          );
      }
      continue;
    }
    
    const listMatch = line.match(/^(\s*)[-*+]\s+(.*)$/);
    if (listMatch) {
      const content = listMatch[2];
      currentList.push(
        <li key={`li-${i}`} className="text-slate-300 text-sm sm:text-base">
          {parseInline(content)}
        </li>
      );
      continue;
    }
    
    flushList();
    elements.push(
      <p key={`p-${i}`} className="mb-3 text-slate-300 text-sm sm:text-base leading-relaxed">
        {parseInline(line)}
      </p>
    );
  }
  
  flushList();
  return elements;
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
            {messages.map((msg, idx) => {
              const isAssistant = msg.role === "assistant";
              return (
                <div key={idx} className="flex gap-4">
                  <div
                    className={`w-8 h-8 rounded-lg flex items-center justify-center font-semibold text-xs shrink-0 select-none ${
                      isAssistant
                        ? "bg-orange-500 text-white"
                        : "bg-slate-800 text-slate-300"
                    }`}
                  >
                    {isAssistant ? "A" : studentProfile.name[0] ?? "M"}
                  </div>

                  <div className="flex-1 space-y-1 min-w-0">
                    <span className="block text-xs font-medium text-slate-400">
                      {isAssistant ? "AURA" : "You"}
                    </span>
                    <div
                      className={`max-w-none leading-relaxed ${
                        isAssistant
                          ? "text-slate-200 space-y-3"
                          : "text-slate-300 font-medium text-sm sm:text-base whitespace-pre-wrap"
                      }`}
                    >
                      {isAssistant ? parseMarkdown(msg.content) : msg.content}
                    </div>
                  </div>
                </div>
              );
            })}
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
