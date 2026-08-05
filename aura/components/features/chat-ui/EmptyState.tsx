"use client"

import { useEffect, useState } from "react"
import {
  ArrowUpRight,
  GraduationCap,
  Home,
  Award,
  ClipboardList,
  Landmark,
  FileText,
  CalendarClock,
} from "lucide-react"
import { useSession } from "next-auth/react"
import { cn } from "@/lib/utils"
import { AnimatedBrandMark } from "@/components/ui/animated-brand-mark"
import { TextGenerateEffect } from "@/components/ui/text-generate-effect"

interface EmptyStateProps {
  onSelectPrompt: (text: string) => void
  /** Preferred display name (from the student profile); falls back to the session name. */
  userName?: string
  /** Disable starter prompts (e.g. while a reply is already in flight). */
  disabled?: boolean
}

const STARTER_PROMPTS = [
  {
    prompt: "What programs does DAU offer?",
    icon: GraduationCap,
    iconWrap: "bg-theme-yellow/10 text-theme-yellow ring-theme-yellow/20",
  },
  {
    prompt: "How do I apply for the next intake?",
    icon: ClipboardList,
    iconWrap: "bg-aura-sky/10 text-aura-sky ring-aura-sky/20",
  },
  {
    prompt: "Tell me about campus hostel facilities.",
    icon: Home,
    iconWrap: "bg-aura-mint/10 text-aura-mint ring-aura-mint/20",
  },
  {
    prompt: "What scholarships are available?",
    icon: Award,
    iconWrap: "bg-brand-400/10 text-brand-400 ring-brand-400/20",
  },
] as const

const FACULTY_STARTER_PROMPTS = [
  {
    prompt: "What is the consultancy policy?",
    icon: Landmark,
    iconWrap: "bg-theme-yellow/10 text-theme-yellow ring-theme-yellow/20",
  },
  {
    prompt: "How do I apply for a seed grant?",
    icon: Award,
    iconWrap: "bg-aura-sky/10 text-aura-sky ring-aura-sky/20",
  },
  {
    prompt: "Where can I find the course file template?",
    icon: FileText,
    iconWrap: "bg-aura-mint/10 text-aura-mint ring-aura-mint/20",
  },
] as const

function timeGreeting(date: Date): string {
  const hour = date.getHours()
  if (hour < 12) return "Good morning"
  if (hour < 17) return "Good afternoon"
  return "Good evening"
}

export function EmptyState({ onSelectPrompt, userName, disabled = false }: EmptyStateProps) {
  const { data: session } = useSession()
  // Time- and name-based greeting resolves client-side; keep the server/first paint neutral
  // so hydration matches, then personalise once mounted and the session is known.
  const [mounted, setMounted] = useState(false)
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => setMounted(true), [])

  const firstName = (userName || session?.user?.name || "").trim().split(" ")[0]
  const heading =
    mounted && firstName ? `${timeGreeting(new Date())}, ${firstName}` : "How can I help you today?"

  const role = session?.user?.role as string | undefined
  const isFaculty =
    !!role && (role.startsWith("faculty") || role.startsWith("dean") || role === "registrar")
  const starterPrompts = isFaculty ? FACULTY_STARTER_PROMPTS : STARTER_PROMPTS

  return (
    <div className="w-full max-w-3xl 2xl:max-w-5xl px-4 py-10">
      <div className="mb-6 flex flex-col items-center gap-4 text-center animate-in fade-in slide-in-from-bottom-2 duration-500">
        <AnimatedBrandMark className="size-14 shadow-[0_0_44px_-12px_rgba(244,80,59,0.5)]" />
        <h1 className="text-balance text-[1.7rem] font-semibold tracking-tight md:text-[2.25rem]">
          <TextGenerateEffect key={heading} words={heading} className="text-gradient-aura" />
        </h1>
        <p className="max-w-md text-sm text-neutral-500">
          Your campus AI for programs, admissions, timetables, and everything DAU.
        </p>
      </div>

      <div className="mx-auto mt-4 grid w-full grid-cols-1 gap-2 sm:grid-cols-2">
        {starterPrompts.map(({ prompt, icon: Icon, iconWrap }, index) => (
          <button
            key={prompt}
            type="button"
            disabled={disabled}
            onClick={() => onSelectPrompt(prompt)}
            style={{ animationDelay: `${120 + index * 55}ms` }}
            className={cn(
              "group flex items-center gap-3 rounded-2xl border border-theme-gray-light/70 bg-theme-gray/30 px-3.5 py-3 text-left transition-all duration-200",
              "hover:-translate-y-0.5 hover:border-theme-gray-lighter hover:bg-theme-gray/70 hover:shadow-[0_12px_30px_-18px_rgba(0,0,0,0.9)]",
              "active:translate-y-0 active:scale-[0.985]",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-theme-yellow/35",
              "animate-in fade-in slide-in-from-bottom-2 fill-mode-both duration-500",
              disabled && "pointer-events-none opacity-50",
            )}
          >
            <span
              className={cn(
                "inline-flex size-8 shrink-0 items-center justify-center rounded-xl ring-1 transition-transform duration-200 group-hover:scale-110",
                iconWrap,
              )}
            >
              <Icon className="size-4" />
            </span>
            <span className="min-w-0 flex-1 text-sm leading-snug text-neutral-300 transition-colors group-hover:text-neutral-100">
              {prompt}
            </span>
            <ArrowUpRight className="size-3.5 shrink-0 text-neutral-700 opacity-0 transition-all duration-200 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 group-hover:text-neutral-400 group-hover:opacity-100" />
          </button>
        ))}
      </div>
    </div>
  )
}
