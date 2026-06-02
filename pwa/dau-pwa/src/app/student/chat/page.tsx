"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { askAura, ChatMessage, StudentProfile } from "@/lib/api/chat.action";
import MarkdownRenderer from "@/components/features/student/MarkdownRenderer";

const STARTER_PROMPTS = [
  { text: "Lost ID card workflow", icon: "💳" },
  { text: "What is the curfew timing at hostellers HoR?", icon: "🌙" },
  { text: "How do I apply for a bonafide certificate?", icon: "📄" },
  { text: "Show technical clubs for AI or programming", icon: "💻" },
];

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState("");
  const [loading, setLoading] = useState(false);
  const [thinkingStep, setThinkingStep] = useState("");
  
  // UI Panels states
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [showProfileSettings, setShowProfileSettings] = useState(false);
  const [activeCitations, setActiveCitations] = useState<{ title: string; file: string }[]>([]);

  // Student Profile Context State
  const [studentProfile, setStudentProfile] = useState<StudentProfile>({
    name: "Rahul Sharma",
    branch: "B.Tech (ICT)",
    year: "3rd Year",
    semester: "Semester V",
    interests: "Artificial Intelligence, competitive coding",
  });

  // Recent ChatGPT-like sidebar threads
  const [recentThreads, setRecentThreads] = useState<string[]>([
    "Hostel Curfew Rules",
    "Bonafide Application Guide",
    "Lost ID Replacement Steps",
    "Technical Clubs & E-Cell",
  ]);

  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  // Load chat history and profile from localStorage on mount
  useEffect(() => {
    const savedHistory = localStorage.getItem("aura_chat_history");
    if (savedHistory) {
      try {
        // eslint-disable-next-line react-hooks/set-state-in-effect
        setMessages(JSON.parse(savedHistory));
      } catch {
        console.error("Error loading chat history");
      }
    } else {
      // Welcome message (starts fresh and empty for Gemini style welcome unless messages present)
      setMessages([]);
    }

    const savedProfile = localStorage.getItem("aura_student_profile");
    if (savedProfile) {
      try {
        setStudentProfile(JSON.parse(savedProfile));
      } catch {
        console.error("Error loading student profile");
      }
    }
  }, []);

  // Save chat history when messages change
  const saveHistory = (newMessages: ChatMessage[]) => {
    setMessages(newMessages);
    localStorage.setItem("aura_chat_history", JSON.stringify(newMessages));
  };

  // Scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSendMessage = async (textToSend: string) => {
    if (!textToSend.trim() || loading) return;

    // Add to recent threads in sidebar if it's a new or first query
    if (messages.length === 0) {
      const threadTitle = textToSend.length > 25 ? textToSend.substring(0, 25) + "..." : textToSend;
      setRecentThreads((prev) => [threadTitle, ...prev.filter((t) => t !== threadTitle)]);
    }

    const userMsg: ChatMessage = { role: "user", content: textToSend };
    const updatedMessages = [...messages, userMsg];
    saveHistory(updatedMessages);
    setInputText("");
    setLoading(true);
    setActiveCitations([]);

    // Multi-step reasoning steps for premium ChatGPT feel
    setThinkingStep("Accessing university registry database...");
    await new Promise((r) => setTimeout(r, 500));
    setThinkingStep("Scanning academics policies & student service handbooks...");
    await new Promise((r) => setTimeout(r, 600));
    setThinkingStep("Formulating RAG grounded response...");
    await new Promise((r) => setTimeout(r, 450));

    try {
      const result = await askAura({
        message: textToSend,
        history: messages,
        studentProfile,
      });

      if (result.success && result.content) {
        saveHistory([...updatedMessages, { role: "assistant", content: result.content }]);
        if (result.citations) {
          setActiveCitations(result.citations);
        }
      } else {
        saveHistory([
          ...updatedMessages,
          {
            role: "assistant",
            content: "Sorry, I had trouble processing your query. Please check your network or try again.",
          },
        ]);
      }
    } catch {
      saveHistory([
        ...updatedMessages,
        {
          role: "assistant",
          content: "Error: I encountered a problem communicating with the university registry servers.",
        },
      ]);
    } finally {
      setLoading(false);
      setThinkingStep("");
    }
  };

  const handleClearChat = () => {
    saveHistory([]);
    setActiveCitations([]);
  };

  const handleSaveProfile = (e: React.FormEvent) => {
    e.preventDefault();
    localStorage.setItem("aura_student_profile", JSON.stringify(studentProfile));
    setShowProfileSettings(false);
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-900 text-slate-100 font-sans">
      
      {/* 1. Left Sidebar (ChatGPT/Gemini Style) */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 flex w-72 flex-col bg-slate-950 border-r border-slate-800/80 transition-transform duration-300 lg:static lg:translate-x-0 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {/* Brand header */}
        <div className="flex h-16 items-center justify-between px-6 border-b border-slate-900">
          <div className="flex items-center gap-3">
            <span className="w-8 h-8 rounded-xl bg-[#E8400C] text-white font-black text-sm flex items-center justify-center shadow-lg shadow-[#E8400C]/25">
              A
            </span>
            <div>
              <h1 className="text-sm font-black tracking-tight text-white">AURA Assistant</h1>
              <span className="text-[9px] font-black uppercase tracking-wider text-[#E8400C]">
                DAU PWA Registry
              </span>
            </div>
          </div>
          {/* Close button on mobile */}
          <button
            onClick={() => setSidebarOpen(false)}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-900 hover:text-white lg:hidden"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* New Chat Button */}
        <div className="px-4 py-4">
          <button
            onClick={() => {
              handleClearChat();
              setSidebarOpen(false);
            }}
            className="flex w-full items-center gap-2.5 rounded-xl border border-slate-800 bg-slate-900 hover:bg-slate-850 px-4 py-3 text-xs font-black uppercase tracking-wider text-slate-200 transition-all duration-150 hover:border-[#E8400C]/30 hover:text-white"
          >
            <svg className="w-4 h-4 text-[#E8400C]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
            </svg>
            New Chat
          </button>
        </div>

        {/* Recent Threads / History */}
        <div className="flex-1 overflow-y-auto px-3 py-2 space-y-1.5 scrollbar-thin scrollbar-thumb-slate-850">
          <span className="block px-3 text-[9px] font-black uppercase tracking-wider text-slate-500 mb-2">
            Recent Queries
          </span>
          {recentThreads.map((thread, idx) => (
            <button
              key={idx}
              onClick={() => {
                setInputText(thread);
                setSidebarOpen(false);
              }}
              className="flex w-full items-center gap-2.5 rounded-xl px-3 py-2.5 text-left text-xs font-medium text-slate-400 hover:bg-slate-900 hover:text-slate-200 transition-all duration-150 group"
            >
              <svg className="w-4.5 h-4.5 text-slate-600 group-hover:text-slate-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
              <span className="truncate">{thread}</span>
            </button>
          ))}
        </div>

        {/* Profile Settings (Clickable Card) */}
        <div className="p-4 border-t border-slate-900">
          <button
            onClick={() => setShowProfileSettings(true)}
            className="flex w-full items-center gap-3 rounded-xl bg-slate-900/60 hover:bg-slate-900 border border-slate-900 hover:border-slate-800 p-3 text-left transition-all duration-150"
          >
            <div className="w-8 h-8 rounded-lg bg-orange-500/10 text-orange-400 flex items-center justify-center font-bold text-xs border border-orange-500/20 shrink-0">
              {studentProfile.name.split(" ").map((n) => n[0]).join("")}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-black text-slate-200 truncate">{studentProfile.name}</p>
              <p className="text-[9px] text-slate-500 font-bold truncate uppercase">{studentProfile.branch}</p>
            </div>
            <svg className="w-4 h-4 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </button>

          {/* Quick Exit back to Main Portal */}
          <Link
            href="/student/academics"
            className="flex w-full items-center justify-center gap-2 mt-3 rounded-xl bg-slate-950 border border-slate-800 hover:border-slate-700 py-2.5 text-[10px] font-black uppercase tracking-wider text-slate-400 hover:text-white transition-colors"
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M11 15l-3-3m0 0l3-3m-3 3h8M3 12a9 9 0 1118 0 9 9 0 01-18 0z" />
            </svg>
            Exit to Student Portal
          </Link>
        </div>
      </aside>

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
            >
              <svg className="w-4.5 h-4.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        </header>

        {/* Messaging Stream / Center Area */}
        <div className="flex-1 overflow-y-auto px-6 py-8 scrollbar-thin scrollbar-thumb-slate-800 scrollbar-track-transparent">
          <div className="mx-auto max-w-3xl space-y-6">
            
            {messages.length === 0 ? (
              /* Gemini/ChatGPT Welcome Screen */
              <div className="flex flex-col items-start justify-center min-h-[40vh] pt-12 space-y-6 animate-fade-in select-none">
                <div>
                  <h2 className="text-3xl sm:text-5xl font-black tracking-tight leading-tight">
                    Hello, <span className="bg-gradient-to-r from-orange-400 via-[#E8400C] to-red-500 bg-clip-text text-transparent">{studentProfile.name.split(" ")[0]}</span>.
                  </h2>
                  <h3 className="text-2xl sm:text-4xl font-extrabold text-slate-500 tracking-tight mt-1.5">
                    How can I help you navigate the portal today?
                  </h3>
                </div>

                <p className="text-xs text-slate-400 max-w-xl font-medium leading-relaxed">
                  I am **AURA**, the Academic and University Resource Assistant. I scan verified Dhirubhai Ambani University registry documents, handbooks, and schedules to provide accurate policies.
                </p>

                {/* Starter Prompt Cards */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 w-full pt-4">
                  {STARTER_PROMPTS.map((prompt, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleSendMessage(prompt.text)}
                      className="flex flex-col items-start gap-2.5 text-left p-4 rounded-2xl bg-slate-950/45 border border-slate-800/80 hover:border-[#E8400C]/30 hover:bg-slate-950 transition-all duration-150 group shadow-sm hover:shadow-lg"
                    >
                      <span className="text-lg bg-slate-900 border border-slate-800 p-2 rounded-xl group-hover:scale-105 transition-transform">{prompt.icon}</span>
                      <span className="text-xs font-bold text-slate-300 group-hover:text-slate-100">{prompt.text}</span>
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              /* Message Thread List */
              <div className="space-y-6">
                {messages.map((msg, idx) => {
                  const isAssistant = msg.role === "assistant";
                  return (
                    <div key={idx} className="flex gap-4 animate-fade-in">
                      {/* Avatar */}
                      <div className={`w-8 h-8 rounded-xl flex items-center justify-center font-black text-xs shrink-0 select-none shadow ${
                        isAssistant 
                          ? "bg-[#E8400C]/10 border border-[#E8400C]/25 text-[#E8400C]" 
                          : "bg-slate-800 border border-slate-700 text-slate-300"
                      }`}>
                        {isAssistant ? "AU" : "ME"}
                      </div>
                      
                      {/* Bubble content */}
                      <div className="flex-1 space-y-1.5 min-w-0">
                        <span className="block text-[9px] font-black uppercase tracking-wider text-slate-500">
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

            {/* AURA Processing Reasoning Step */}
            {loading && (
              <div className="flex gap-4 items-start animate-pulse">
                <div className="w-8 h-8 rounded-xl bg-[#E8400C]/10 border border-[#E8400C]/25 text-[#E8400C] font-black text-xs flex items-center justify-center shrink-0">
                  AU
                </div>
                <div className="space-y-2 flex-1">
                  <span className="block text-[9px] font-black uppercase tracking-wider text-slate-500">
                    AURA Assistant
                  </span>
                  <div className="flex items-center gap-2.5 bg-slate-950/40 border border-slate-850 rounded-2xl p-3.5 max-w-sm">
                    <svg className="w-3.5 h-3.5 text-[#E8400C] animate-spin" fill="none" viewBox="0 0 24 24">
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

            {/* Citations Panel underneath response (if active) */}
            {activeCitations.length > 0 && !loading && (
              <div className="mt-8 border-t border-slate-800/80 pt-6 animate-fade-in">
                <span className="block text-[9px] font-black uppercase tracking-wider text-slate-500 mb-3">
                  Scanned Registry References
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {activeCitations.map((cit, idx) => (
                    <div key={idx} className="bg-slate-950/60 border border-slate-850 rounded-2xl p-4 shadow-sm hover:border-[#E8400C]/20 transition-all duration-150">
                      <h4 className="text-xs font-black text-slate-200 mb-1 leading-snug">{cit.title}</h4>
                      <span className="text-[9px] font-mono text-[#E8400C] font-black block truncate">
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

        {/* Bottom Centered Fixed Input Bar */}
        <footer className="border-t border-slate-800/60 bg-slate-900/60 backdrop-blur p-4 shrink-0">
          <div className="mx-auto max-w-3xl">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSendMessage(inputText);
              }}
              className="relative flex items-center bg-slate-950 border border-slate-800 focus-within:border-[#E8400C]/50 rounded-2xl p-2.5 transition-all duration-200"
            >
              <input
                type="text"
                placeholder="Ask AURA about exams, curfews, clubs, maps, leave policies..."
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                disabled={loading}
                className="flex-1 bg-transparent px-4 py-2 text-sm text-slate-200 placeholder-slate-500 focus:outline-none disabled:opacity-50"
              />
              <button
                type="submit"
                disabled={!inputText.trim() || loading}
                className="bg-[#E8400C] text-white p-2.5 rounded-xl hover:bg-[#D7380A] disabled:opacity-40 transition-colors shrink-0 shadow-lg shadow-[#E8400C]/10"
              >
                <svg className="w-4 h-4 transform rotate-90" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 19l9-7-9-7v14z" />
                </svg>
              </button>
            </form>
            <p className="text-[10px] text-slate-500 font-medium text-center mt-2.5">
              AURA assistant synthesizes grounded responses. Double-check official policies with the registry department.
            </p>
          </div>
        </footer>
      </main>

      {/* 3. Student Profile Personalization Settings Modal */}
      {showProfileSettings && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in">
          <div className="bg-slate-905 border border-slate-800 rounded-3xl max-w-md w-full overflow-hidden shadow-2xl flex flex-col">
            <div className="p-6 border-b border-slate-800/80 flex justify-between items-center">
              <div>
                <h2 className="text-sm font-black text-white leading-tight">Student Profile Settings</h2>
                <p className="text-[9px] text-slate-500 font-bold uppercase tracking-wide mt-0.5">Configure AURA Context</p>
              </div>
              <button
                onClick={() => setShowProfileSettings(false)}
                className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <form onSubmit={handleSaveProfile} className="p-6 space-y-4 text-xs">
              <div>
                <label className="block text-[10px] font-black text-slate-450 uppercase mb-1">Student Name</label>
                <input
                  type="text"
                  value={studentProfile.name}
                  onChange={(e) => setStudentProfile({ ...studentProfile, name: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 hover:border-slate-700 rounded-xl px-3.5 py-2.5 text-slate-200 font-medium focus:outline-none focus:border-[#E8400C]"
                />
              </div>
              <div className="grid grid-cols-2 gap-3.5">
                <div>
                  <label className="block text-[10px] font-black text-slate-450 uppercase mb-1">Academic Branch</label>
                  <input
                    type="text"
                    value={studentProfile.branch}
                    onChange={(e) => setStudentProfile({ ...studentProfile, branch: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 hover:border-slate-700 rounded-xl px-3.5 py-2.5 text-slate-200 font-medium focus:outline-none focus:border-[#E8400C]"
                  />
                </div>
                <div>
                  <label className="block text-[10px] font-black text-slate-450 uppercase mb-1">Semester</label>
                  <input
                    type="text"
                    value={studentProfile.semester}
                    onChange={(e) => setStudentProfile({ ...studentProfile, semester: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 hover:border-slate-700 rounded-xl px-3.5 py-2.5 text-slate-200 font-medium focus:outline-none focus:border-[#E8400C]"
                  />
                </div>
              </div>
              <div>
                <label className="block text-[10px] font-black text-slate-450 uppercase mb-1">Special Interests / Tech</label>
                <input
                  type="text"
                  value={studentProfile.interests}
                  onChange={(e) => setStudentProfile({ ...studentProfile, interests: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 hover:border-slate-700 rounded-xl px-3.5 py-2.5 text-slate-200 font-medium focus:outline-none focus:border-[#E8400C]"
                />
              </div>
              <div className="flex gap-3 pt-3">
                <button
                  type="button"
                  onClick={() => setShowProfileSettings(false)}
                  className="flex-1 bg-slate-900 hover:bg-slate-850 text-slate-300 text-[10px] font-black uppercase py-3 rounded-xl border border-slate-800 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 bg-[#E8400C] hover:bg-[#D7380A] text-white text-[10px] font-black uppercase py-3 rounded-xl shadow transition-colors"
                >
                  Save Context
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
}
