"use client"

import { type ReactNode, useEffect, useState } from "react"
import {
  ArrowUpRight,
  GraduationCap,
  Home,
  Award,
  ClipboardList,
} from "lucide-react"
import { useSession } from "next-auth/react"
import { cn } from "@/lib/utils"
import { AnimatedBrandMark } from "@/components/ui/animated-brand-mark"

interface EmptyStateProps {
  onSelectPrompt: (text: string) => void
  /** Preferred display name (from the student profile); falls back to the session name. */
  userName?: string
  /** The composer, rendered between the greeting and the starter prompts. */
  children?: ReactNode
}

const STARTER_PROMPTS = [
  {
    prompt: "What programs does DAU offer?",
    icon: GraduationCap,
  },
  {
    prompt: "How do I apply for the next intake?",
    icon: ClipboardList,
  },
  {
    prompt: "Tell me about campus hostel facilities.",
    icon: Home,
  },
  {
    prompt: "What scholarships are available?",
    icon: Award,
  },
] as const

function timeGreeting(date: Date): string {
  const hour = date.getHours()
  if (hour < 12) return "Good morning"
  if (hour < 17) return "Good afternoon"
  return "Good evening"
}

export function EmptyState({ onSelectPrompt, userName, children }: EmptyStateProps) {
  const { data: session } = useSession()
  // Time- and name-based greeting resolves client-side; keep the server/first paint neutral
  // so hydration matches, then personalise once mounted and the session is known.
  const [mounted, setMounted] = useState(false)
  useEffect(() => setMounted(true), [])

  const firstName = (userName || session?.user?.name || "").trim().split(" ")[0]
  const heading =
    mounted && firstName ? `${timeGreeting(new Date())}, ${firstName}` : "How can I help you today?"

  return (
    <div className="w-full max-w-3xl px-4 py-10">
      <div className="mb-6 flex flex-col items-center gap-4 text-center animate-in fade-in slide-in-from-bottom-2 duration-500">
        <AnimatedBrandMark className="size-14 shadow-[0_0_44px_-12px_rgba(244,80,59,0.5)]" />
        <h1 className="text-balance text-[1.7rem] font-semibold tracking-tight text-neutral-100 md:text-[2.25rem]">
          {heading}
        </h1>
      </div>

      {children ? <div className="w-full">{children}</div> : null}

      <div className="mx-auto mt-4 grid w-full grid-cols-1 gap-2 sm:grid-cols-2">
        {STARTER_PROMPTS.map(({ prompt, icon: Icon }, index) => (
          <button
            key={prompt}
            type="button"
            onClick={() => onSelectPrompt(prompt)}
            style={{ animationDelay: `${120 + index * 55}ms` }}
            className={cn(
              "group flex items-center gap-2.5 rounded-2xl border border-theme-gray-light/70 bg-theme-gray/30 px-3.5 py-3 text-left transition-all duration-200",
              "hover:border-theme-gray-lighter hover:bg-theme-gray/70",
              "active:scale-[0.985]",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-theme-yellow/35",
              "animate-in fade-in slide-in-from-bottom-2 fill-mode-both duration-500",
            )}
          >
            <span className="inline-flex size-7 shrink-0 items-center justify-center rounded-lg text-neutral-500 transition-colors group-hover:text-theme-yellow">
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
