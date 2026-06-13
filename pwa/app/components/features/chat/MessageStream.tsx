import React from "react";
import {
  ChatMessage,
  Citation,
  StudentProfile,
} from "@/app/api/chat.service";
import MessageItem from "@/app/components/features/chat/MessageItem";
import { UserSession } from "@/hooks/use-aura-chat";

interface MessageStreamProps {
  messages: ChatMessage[];
  studentProfile: StudentProfile;
  loading: boolean;
  thinkingStep: string;
  activeCitations: Citation[];
  onSelectStarter: (text: string) => void;
  messagesEndRef: React.RefObject<HTMLDivElement | null>;
  userSession?: UserSession | null;
}

function IdCardIcon() {
  return (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.6}>
      <rect x="3" y="5" width="18" height="14" rx="2" />
      <circle cx="8.5" cy="11" r="1.75" />
      <path strokeLinecap="round" d="M5.5 16c0-1.4 1.3-2.5 3-2.5s3 1.1 3 2.5M13.5 9.5h5M13.5 13h5" />
    </svg>
  );
}

// Parent or student can query curfew
function ClockIcon() {
  return (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.6}>
      <circle cx="12" cy="12" r="9" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 7v5l3 2" />
    </svg>
  );
}

function DocumentIcon() {
  return (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.6}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M7 3h7l3 3v15H7z" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M14 3v3h3M9.5 11h5M9.5 14h5M9.5 17h3" />
    </svg>
  );
}

function TerminalIcon() {
  return (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.6}>
      <rect x="3" y="4" width="18" height="16" rx="2" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M7 9.5 10 12l-3 2.5M12.5 15h4" />
    </svg>
  );
}

const STARTER_PROMPTS = [
  { text: "Lost ID card workflow", icon: IdCardIcon },
  { text: "What is the curfew timing at hostellers HoR?", icon: ClockIcon },
  { text: "How do I apply for a bonafide certificate?", icon: DocumentIcon },
  { text: "Show technical clubs for AI or programming", icon: TerminalIcon },
];

export default function MessageStream({
  messages,
  studentProfile,
  loading,
  thinkingStep,
  activeCitations,
  onSelectStarter,
  messagesEndRef,
  userSession
}: MessageStreamProps) {
  const getGreeting = () => {
    if (!userSession) {
      return "Good day. How can I help you navigate the portal today?";
    }
    if (userSession.role === "parent") {
      const parentFirstName = userSession.name.split(" ")[0];
      const studentFirstName = studentProfile.name ? studentProfile.name.split(" ")[0] : "your child";
      return `Hello Mr./Ms. ${parentFirstName}. I can help you check academic information, fee structures, or hostel guidelines for ${studentFirstName}.`;
    } else {
      const studentFirstName = userSession.name.split(" ")[0];
      return `Good morning, ${studentFirstName}. How can I help you navigate the academic portal today?`;
    }
  };

  const getUserInitial = () => {
    if (userSession) return userSession.name[0] || "U";
    return studentProfile.name[0] || "M";
  };

  return (
    <div className="flex-1 overflow-y-auto px-6 py-8">
      <div className="mx-auto max-w-3xl space-y-6">
        {messages.length === 0 ? (
          <div className="flex flex-col items-start justify-center min-h-[30vh] pt-8 space-y-5 select-none">
            <div>
              <h2 className="text-2xl sm:text-3xl font-semibold tracking-tight text-slate-900 dark:text-slate-100 leading-snug">
                AURA — Academic & University Resource Assistant
              </h2>
              <h3 className="text-sm sm:text-base text-slate-500 dark:text-slate-400 mt-1.5 leading-relaxed">
                {getGreeting()}
              </h3>
            </div>

            <p className="text-sm text-slate-500 dark:text-slate-400 max-w-xl leading-relaxed">
              AURA scans verified Dhirubhai Ambani University registry documents,
              handbooks, and schedules to provide accurate policies.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 w-full pt-2">
              {STARTER_PROMPTS.map((prompt, idx) => {
                const Icon = prompt.icon;
                return (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => onSelectStarter(prompt.text)}
                    className="flex items-center gap-3 text-left p-4 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-brand-300 dark:hover:border-brand-700 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors duration-150 hover:cursor-pointer"
                  >
                    <span className="shrink-0 text-brand-600 dark:text-brand-400">
                      <Icon />
                    </span>
                    <span className="text-sm text-slate-600 dark:text-slate-300 leading-snug">
                      {prompt.text}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            {messages.map((msg, idx) => (
              <MessageItem
                key={idx}
                msg={msg}
                userInitial={getUserInitial()}
              />
            ))}
          </div>
        )}

        {loading && (
          <div className="flex gap-4 items-start">
            <div className="w-8 h-8 rounded-md bg-brand-600 text-white font-semibold text-xs flex items-center justify-center shrink-0">
              A
            </div>
            <div className="space-y-1 flex-1">
              <span className="block text-xs font-medium text-slate-400 dark:text-slate-500">AURA</span>
              <div className="flex items-center gap-2.5 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg px-3.5 py-3 max-w-sm">
                <svg className="w-4 h-4 text-brand-600 dark:text-brand-400 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
                <span className="text-xs text-slate-500 dark:text-slate-400">{thinkingStep}</span>
              </div>
            </div>
          </div>
        )}

        {activeCitations.length > 0 && !loading && (
          <div className="mt-8 border-t border-slate-200 dark:border-slate-800 pt-6">
            <span className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-3">
              Sources
            </span>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {activeCitations.map((cit, idx) => (
                <div
                  key={idx}
                  className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 border-l-2 border-l-brand-300 dark:border-l-brand-600 rounded-md p-3.5 hover:border-l-brand-500 dark:hover:border-l-brand-400 transition-colors duration-150"
                >
                  <h4 className="text-sm font-medium text-slate-700 dark:text-slate-200 mb-1 leading-snug">
                    {cit.title}
                  </h4>
                  {cit.file && (
                    <span className="text-[12px] font-mono text-slate-400 dark:text-slate-500 block truncate">
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
