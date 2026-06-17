"use client"

import { Sparkles } from "lucide-react"
import { cn } from "@/lib/utils"

interface EmptyStateProps {
  onSelectPrompt: (text: string) => void
}

const STARTER_PROMPTS = [
  "What programs does DAU offer?",
  "How do I apply for the next intake?",
  "Tell me about campus hostel facilities.",
  "What scholarships are available?",
]

export function EmptyState({ onSelectPrompt }: EmptyStateProps) {
  return (
    <div className="mx-auto flex min-h-full max-w-3xl flex-col items-center justify-center px-4 py-16 text-center">
      <span className="mb-6 inline-flex items-center gap-2 rounded-full border border-theme-gray-light bg-theme-gray px-3 py-1 text-xs text-neutral-400">
        <Sparkles className="size-3.5 text-theme-yellow" />
        AURA · DAU Assistant
      </span>
      <h1 className="bg-gradient-to-r from-theme-red to-theme-yellow bg-clip-text text-3xl font-semibold text-balance text-transparent md:text-4xl">
        How can I help you today?
      </h1>
      <p className="mt-3 max-w-md text-pretty text-sm text-neutral-400">
        Ask about programs, admissions, campus life, or anything else about
        Dhirubhai Ambani University.
      </p>
      <div className="mt-8 grid w-full grid-cols-1 gap-3 sm:grid-cols-2">
        {STARTER_PROMPTS.map((prompt) => (
          <button
            key={prompt}
            type="button"
            onClick={() => onSelectPrompt(prompt)}
            className={cn(
              "rounded-2xl border border-theme-gray-light bg-theme-gray px-4 py-3 text-left text-sm text-neutral-200 transition-colors",
              "hover:border-theme-gray-lighter hover:bg-theme-gray-light",
            )}
          >
            {prompt}
          </button>
        ))}
      </div>
    </div>
  )
}
