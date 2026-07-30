"use client"

import { useEffect, useMemo, useRef, useState } from "react"
import { AnimatePresence, motion } from "framer-motion"
import { FileText, Loader2, X } from "lucide-react"
import { useDocumentViewer } from "@/hooks/use-document-viewer"

// Module-level cache so hovering multiple citation cards for the same file
// (or reopening a document already viewed) doesn't refetch every time.
const documentCache = new Map<string, string>()

interface FetchState {
  status: "idle" | "loading" | "loaded" | "error"
  content?: string
  error?: string
}

export function DocumentViewerSheet() {
  const { target, isOpen, closeDocument } = useDocumentViewer()

  return (
    <AnimatePresence>
      {isOpen && target ? (
        <DocumentViewerPanel key={target.path} target={target} onClose={closeDocument} />
      ) : null}
    </AnimatePresence>
  )
}

function DocumentViewerPanel({
  target,
  onClose,
}: {
  target: { path: string; title?: string; startLine?: number; endLine?: number }
  onClose: () => void
}) {
  const [state, setState] = useState<FetchState>(() =>
    documentCache.has(target.path)
      ? { status: "loaded", content: documentCache.get(target.path) }
      : { status: "idle" },
  )
  const highlightRef = useRef<HTMLDivElement | null>(null)
  const scrollRef = useRef<HTMLDivElement | null>(null)
  const closeButtonRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose()
    }
    document.addEventListener("keydown", handleEscape)
    closeButtonRef.current?.focus()
    return () => document.removeEventListener("keydown", handleEscape)
  }, [onClose])

  useEffect(() => {
    if (documentCache.has(target.path)) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setState({ status: "loaded", content: documentCache.get(target.path) })
      return
    }
    let cancelled = false
    setState({ status: "loading" })
    fetch(`/api/documents?path=${encodeURIComponent(target.path)}`)
      .then(async (res) => {
        if (!res.ok) {
          const body = await res.json().catch(() => null)
          throw new Error(body?.error ?? "Failed to load document")
        }
        return res.json() as Promise<{ content: string }>
      })
      .then((data) => {
        if (cancelled) return
        documentCache.set(target.path, data.content)
        setState({ status: "loaded", content: data.content })
      })
      .catch((err: Error) => {
        if (cancelled) return
        setState({ status: "error", error: err.message })
      })
    return () => {
      cancelled = true
    }
  }, [target.path])

  // Auto-scroll to the cited line range once content is rendered.
  useEffect(() => {
    if (state.status !== "loaded") return
    const id = requestAnimationFrame(() => {
      highlightRef.current?.scrollIntoView({ block: "center", behavior: "smooth" })
    })
    return () => cancelAnimationFrame(id)
  }, [state.status])

  const lines = useMemo(() => state.content?.split("\n") ?? [], [state.content])
  const startLine = target.startLine
  const endLine = target.endLine ?? target.startLine

  return (
    <>
      <motion.div
        className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
        aria-hidden="true"
      />
      <motion.aside
        role="dialog"
        aria-modal="true"
        aria-label={target.title ?? "Source document"}
        className="fixed inset-y-0 right-0 z-50 flex w-full max-w-xl flex-col border-l border-theme-gray-light bg-theme-black shadow-2xl"
        initial={{ x: "100%" }}
        animate={{ x: 0 }}
        exit={{ x: "100%" }}
        transition={{ type: "spring", stiffness: 320, damping: 32 }}
      >
        <div className="flex items-center justify-between gap-3 border-b border-theme-gray-light px-4 py-3">
          <div className="flex min-w-0 items-center gap-2">
            <FileText className="size-4 shrink-0 text-theme-yellow" />
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-neutral-100">
                {target.title ?? target.path}
              </p>
              <p className="truncate text-xs text-neutral-500">{target.path}</p>
            </div>
          </div>
          <button
            ref={closeButtonRef}
            type="button"
            onClick={onClose}
            aria-label="Close document viewer"
            className="shrink-0 rounded-lg p-1.5 text-neutral-400 transition-colors hover:bg-theme-gray-light hover:text-neutral-100"
          >
            <X className="size-5" />
          </button>
        </div>

        <div ref={scrollRef} className="flex-1 overflow-y-auto">
          {state.status === "loading" || state.status === "idle" ? (
            <div className="flex h-full items-center justify-center gap-2 text-sm text-neutral-500">
              <Loader2 className="size-4 animate-spin" />
              Loading source…
            </div>
          ) : state.status === "error" ? (
            <div className="p-4 text-sm text-theme-red">{state.error}</div>
          ) : (
            <pre className="min-w-full whitespace-pre-wrap break-words px-0 py-2 font-mono text-xs leading-relaxed text-neutral-300">
              {lines.map((line, i) => {
                const lineNo = i + 1
                const isHighlighted =
                  startLine != null && lineNo >= startLine && lineNo <= (endLine ?? startLine)
                return (
                  <div
                    key={lineNo}
                    ref={isHighlighted && lineNo === startLine ? highlightRef : undefined}
                    className={cn(
                      "flex gap-3 px-4",
                      isHighlighted && "bg-theme-yellow/20 border-l-2 border-theme-yellow",
                    )}
                  >
                    <span className="w-10 shrink-0 select-none text-right text-neutral-600">
                      {lineNo}
                    </span>
                    <span className={cn(isHighlighted && "text-neutral-100")}>{line || " "}</span>
                  </div>
                )
              })}
            </pre>
          )}
        </div>
      </motion.aside>
    </>
  )
}
