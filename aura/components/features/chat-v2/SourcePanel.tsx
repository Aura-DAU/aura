"use client"

import { useEffect, useMemo, useRef } from "react"
import { FileText, X, ExternalLink, Calendar } from "lucide-react"
import { cn } from "@/lib/utils"
import type { Citation } from "@/lib/chat-types"

interface SourcePanelProps {
  citation: Citation | null
  onClose: () => void
}

/**
 * FE-3: Source Provenance Side-Panel UI
 *
 * Slides in from the right when a citation badge is hovered/focused in
 * Message.tsx. Shows the cited document's text with the exact line range
 * (start_line–end_line) highlighted, once the backend starts returning
 * that metadata (see BE-1). Until then it falls back to showing whatever
 * metadata is available (title, file, visibility, year) plus a link to
 * open the source document directly.
 */
export function SourcePanel({ citation, onClose }: SourcePanelProps) {
  const panelRef = useRef<HTMLDivElement>(null)
  const open = citation !== null

  // Close on Escape for keyboard/accessibility parity with mouse-hover close.
  useEffect(() => {
    if (!open) return
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose()
    }
    window.addEventListener("keydown", handleKey)
    return () => window.removeEventListener("keydown", handleKey)
  }, [open, onClose])

  const snippet = citation?.snippet
  const lines = useMemo(() => (snippet ? snippet.split("\n") : null), [snippet])

  const hasLineRange =
    typeof citation?.start_line === "number" && typeof citation?.end_line === "number"

  const isUrl = citation?.file.startsWith("http://") || citation?.file.startsWith("https://")

  return (
    <>
      {/* Scrim — only intercepts clicks on mobile/split layouts, hover never triggers it */}
      <div
        aria-hidden
        onClick={onClose}
        className={cn(
          "fixed inset-0 z-40 bg-black/40 backdrop-blur-[1px] transition-opacity duration-200 md:hidden",
          open ? "pointer-events-auto opacity-100" : "pointer-events-none opacity-0",
        )}
      />

      <div
        ref={panelRef}
        role="complementary"
        aria-label="Source document preview"
        aria-hidden={!open}
        className={cn(
          "fixed inset-y-0 right-0 z-50 flex w-full max-w-sm flex-col border-l border-theme-gray-light bg-theme-black shadow-2xl transition-transform duration-200 ease-out",
          open ? "translate-x-0" : "translate-x-full",
        )}
      >
        <div className="flex items-center justify-between gap-3 border-b border-theme-gray-light px-4 py-3">
          <div className="flex min-w-0 items-center gap-2">
            <FileText className="size-4 shrink-0 text-theme-yellow" />
            <span className="truncate text-sm font-medium text-neutral-100">
              {citation?.title ?? citation?.file ?? "Source"}
            </span>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close source preview"
            className="rounded-lg p-1.5 text-neutral-400 transition-colors hover:bg-theme-gray-light hover:text-neutral-100"
          >
            <X className="size-4" />
          </button>
        </div>

        <div className="flex flex-wrap items-center gap-2 border-b border-theme-gray-light px-4 py-2.5">
          {citation?.document_year ? (
            <span className="inline-flex items-center gap-1 rounded-full border border-theme-gray-light bg-theme-gray px-2 py-0.5 text-[10px] text-neutral-400">
              <Calendar className="size-3" />
              {citation.document_year}
            </span>
          ) : null}
          {hasLineRange ? (
            <span className="inline-flex items-center gap-1 rounded-full border border-theme-yellow/20 bg-theme-yellow/10 px-2 py-0.5 text-[10px] font-medium text-theme-yellow">
              Lines {citation?.start_line}–{citation?.end_line}
            </span>
          ) : null}
          {citation?.visibility ? (
            <span className="rounded-full border border-theme-gray-light bg-theme-gray px-2 py-0.5 text-[10px] text-neutral-400">
              {citation.visibility}
            </span>
          ) : null}
        </div>

        <div className="flex-1 overflow-y-auto px-4 py-4">
          {lines ? (
            <pre className="whitespace-pre-wrap break-words rounded-lg border border-theme-gray-light bg-theme-gray/60 p-3 font-mono text-xs leading-relaxed text-neutral-300">
              {lines.map((line, i) => {
                const lineNumber = (citation?.start_line ?? 1) + i
                const isCited =
                  hasLineRange &&
                  lineNumber >= (citation!.start_line as number) &&
                  lineNumber <= (citation!.end_line as number)
                return (
                  <div
                    key={i}
                    className={cn(
                      "flex gap-3 rounded px-1",
                      isCited && "bg-theme-yellow/15 text-theme-yellow",
                    )}
                  >
                    <span className="w-8 shrink-0 select-none text-right text-neutral-600">
                      {lineNumber}
                    </span>
                    <span className="min-w-0 flex-1">{line || " "}</span>
                  </div>
                )
              })}
            </pre>
          ) : (
            <div className="flex flex-col items-center gap-2 rounded-lg border border-dashed border-theme-gray-light px-4 py-8 text-center">
              <FileText className="size-6 text-neutral-600" />
              <p className="text-xs text-neutral-500">
                Line-level preview isn&apos;t available for this source yet.
                {hasLineRange
                  ? ` It was cited from lines ${citation?.start_line}–${citation?.end_line}.`
                  : ""}
              </p>
            </div>
          )}
        </div>

        {isUrl ? (
          <div className="border-t border-theme-gray-light px-4 py-3">
            <a
              href={citation?.file}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-xs text-theme-yellow transition-colors hover:underline"
            >
              Open full document
              <ExternalLink className="size-3" />
            </a>
          </div>
        ) : null}
      </div>
    </>
  )
}
