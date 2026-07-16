"use client"

import { useState } from "react"
import { Check, Copy } from "lucide-react"
import { cn } from "@/lib/utils"

interface CodeBlockProps {
  code: string
  language?: string
}

export function CodeBlock({ code, language }: CodeBlockProps) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      /* clipboard unavailable */
    }
  }

  return (
    <div className="group/code relative my-3 overflow-hidden rounded-xl border border-theme-gray-light bg-theme-black">
      <div className="flex items-center justify-between border-b border-theme-gray-light bg-theme-gray px-3 py-1.5">
        <span className="font-mono text-xs text-neutral-400">
          {language || "code"}
        </span>
        <button
          type="button"
          onClick={handleCopy}
          aria-label={copied ? "Copied" : "Copy code"}
          className={cn(
            "inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-xs font-medium transition-colors",
            "text-neutral-400 hover:bg-theme-gray-light hover:text-neutral-100",
          )}
        >
          {copied ? (
            <>
              <Check className="size-3.5 text-theme-yellow" />
              Copied
            </>
          ) : (
            <>
              <Copy className="size-3.5" />
              Copy
            </>
          )}
        </button>
      </div>
      <pre className="overflow-x-auto p-4 text-sm leading-relaxed">
        <code className="font-mono text-neutral-100">{code}</code>
      </pre>
    </div>
  )
}
