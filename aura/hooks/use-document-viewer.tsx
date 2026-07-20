"use client"

import { createContext, useCallback, useContext, useMemo, useState } from "react"

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

  // Called on hover so the drawer's fetch (in DocumentViewerSheet) has a
  // head start by the time the user clicks — the sheet itself owns the
  // request/cache, this just primes `target` without opening the panel.
  const prefetchDocument = useCallback((next: DocumentViewerTarget) => {
    setTarget((prev) => (prev?.path === next.path ? prev : next))
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
