"use client"

import { createContext, useCallback, useContext, useMemo, useState } from "react"
import { prefetchDocumentContent } from "@/lib/document-cache"

export interface DocumentViewerTarget {
  /** Relative path to the markdown source, e.g. "infrastructure/ict_infrastructure.md". */
  path: string
  title?: string
  startLine?: number
  endLine?: number
}

interface DocumentViewerContextValue {
  target: DocumentViewerTarget | null
  isOpen: boolean
  openDocument: (target: DocumentViewerTarget) => void
  prefetchDocument: (target: DocumentViewerTarget) => void
  closeDocument: () => void
}

const DocumentViewerContext = createContext<DocumentViewerContextValue | null>(null)

export function DocumentViewerProvider({ children }: { children: React.ReactNode }) {
  const [target, setTarget] = useState<DocumentViewerTarget | null>(null)
  const [isOpen, setIsOpen] = useState(false)

  const openDocument = useCallback((next: DocumentViewerTarget) => {
    setTarget(next)
    setIsOpen(true)
  }, [])

  // Warm the module cache on hover. Never mutate `target` here — that used to
  // swap the open sheet's document when the user hovered a different citation.
  const prefetchDocument = useCallback((next: DocumentViewerTarget) => {
    void prefetchDocumentContent(next.path).catch(() => {
      /* prefetch is best-effort */
    })
  }, [])

  const closeDocument = useCallback(() => setIsOpen(false), [])

  const value = useMemo(
    () => ({ target, isOpen, openDocument, prefetchDocument, closeDocument }),
    [target, isOpen, openDocument, prefetchDocument, closeDocument],
  )

  return <DocumentViewerContext.Provider value={value}>{children}</DocumentViewerContext.Provider>
}

export function useDocumentViewer(): DocumentViewerContextValue {
  const ctx = useContext(DocumentViewerContext)
  if (!ctx) {
    throw new Error("useDocumentViewer must be used within a DocumentViewerProvider")
  }
  return ctx
}
