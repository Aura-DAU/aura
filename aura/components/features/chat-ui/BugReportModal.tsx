"use client"

import {
  type ChangeEvent,
  type FormEvent,
  useEffect,
  useRef,
  useState,
} from "react"
import { AnimatePresence, motion } from "framer-motion"
import { ImagePlus, X } from "lucide-react"
import { toast } from "sonner"
import { useSession } from "next-auth/react"
import { toastError } from "@/lib/toast"
import { cn } from "@/lib/utils"

interface BugReportModalProps {
  open: boolean
  onClose: () => void
}

export function BugReportModal({ open, onClose }: BugReportModalProps) {
  return (
    <AnimatePresence>
      {open ? (
        <BugReportDialog key="bug-report-dialog" onClose={onClose} />
      ) : null}
    </AnimatePresence>
  )
}

function BugReportDialog({ onClose }: { onClose: () => void }) {
  const { data: session } = useSession()
  const [queryText, setQueryText] = useState("")
  const [image, setImage] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const closeButtonRef = useRef<HTMLButtonElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Keyboard dismiss
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose()
    }
    document.addEventListener("keydown", onKey)
    closeButtonRef.current?.focus()
    return () => document.removeEventListener("keydown", onKey)
  }, [onClose])

  // Preview cleanup
  useEffect(() => {
    return () => {
      if (preview) URL.revokeObjectURL(preview)
    }
  }, [preview])

  const handleImageChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] ?? null
    if (!file) return

    // 5 MB client-side guard (mirrors server)
    if (file.size > 5 * 1024 * 1024) {
      toastError("Screenshot must be under 5 MB")
      e.target.value = ""
      return
    }
    setImage(file)
    if (preview) URL.revokeObjectURL(preview)
    setPreview(URL.createObjectURL(file))
  }

  const removeImage = () => {
    setImage(null)
    if (preview) {
      URL.revokeObjectURL(preview)
      setPreview(null)
    }
    if (fileInputRef.current) fileInputRef.current.value = ""
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!queryText.trim()) {
      toastError("Please describe the bug before submitting")
      return
    }

    setSubmitting(true)
    try {
      const fd = new FormData()
      fd.append("query_text", queryText.trim())
      if (image) fd.append("image", image, image.name)

      const res = await fetch("/api/bug-report", { method: "POST", body: fd })
      if (!res.ok) {
        const body = (await res.json().catch(() => ({}))) as { error?: string }
        throw new Error(body.error ?? "Submission failed")
      }

      toast.success("Bug reported — thanks! We'll look into it.")
      onClose()
    } catch (err) {
      toastError(err instanceof Error ? err.message : "Could not submit report")
    } finally {
      setSubmitting(false)
    }
  }

  const role = session?.user?.role ?? "unknown"
  const displayRole = role
    .replace("faculty_", "Faculty – ")
    .replace("dean_", "Dean – ")
    .replace(/\b\w/g, (c) => c.toUpperCase())

  return (
    <motion.div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/70 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Dialog */}
      <motion.div
        role="dialog"
        aria-modal="true"
        aria-label="Report a bug"
        className="relative w-full max-w-md rounded-2xl border border-theme-gray-light bg-theme-gray p-6 shadow-2xl"
        initial={{ scale: 0.95, opacity: 0, y: 12 }}
        animate={{ scale: 1, opacity: 1, y: 0 }}
        exit={{ scale: 0.95, opacity: 0, y: 12 }}
        transition={{ type: "spring", stiffness: 300, damping: 26 }}
      >
        {/* Header */}
        <div className="mb-5 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-neutral-100">
              Report a Bug
            </h2>
            <p className="mt-0.5 text-xs text-neutral-500">
              Something broken? Tell us and we&apos;ll fix it.
            </p>
          </div>
          <button
            ref={closeButtonRef}
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="rounded-lg p-1.5 text-neutral-400 transition-colors hover:bg-theme-gray-light hover:text-neutral-100"
          >
            <X className="size-5" />
          </button>
        </div>

        {/* Role chip */}
        <div className="mb-5 rounded-xl border border-theme-gray-lighter bg-theme-black px-4 py-3">
          <div className="mb-1 text-xs font-semibold uppercase tracking-wider text-theme-yellow">
            Submitting as
          </div>
          <div className="text-sm text-neutral-200">{displayRole}</div>
          {session?.user?.email && (
            <div className="mt-0.5 text-xs text-neutral-500">
              {session.user.email}
            </div>
          )}
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          {/* Query textarea */}
          <div className="flex flex-col gap-1.5">
            <label
              htmlFor="bug-query"
              className="text-xs font-medium text-neutral-400"
            >
              Describe the bug{" "}
              <span className="text-theme-red">*</span>
            </label>
            <textarea
              id="bug-query"
              rows={4}
              value={queryText}
              onChange={(e) => setQueryText(e.target.value)}
              placeholder="What went wrong? What were you doing when it happened?"
              maxLength={5000}
              required
              className="resize-none rounded-xl border border-theme-gray-light bg-theme-black px-3 py-2.5 text-sm text-neutral-100 outline-none transition-colors focus:border-theme-gray-lighter placeholder:text-neutral-600"
            />
            <span className="self-end text-[11px] text-neutral-600">
              {queryText.length}/5000
            </span>
          </div>

          {/* Image upload */}
          <div className="flex flex-col gap-1.5">
            <span className="text-xs font-medium text-neutral-400">
              Screenshot{" "}
              <span className="font-normal text-neutral-600">(optional)</span>
            </span>

            {preview ? (
              /* Preview card */
              <div className="relative overflow-hidden rounded-xl border border-theme-gray-light bg-theme-black">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={preview}
                  alt="Screenshot preview"
                  className="max-h-40 w-full object-contain"
                />
                <button
                  type="button"
                  onClick={removeImage}
                  aria-label="Remove screenshot"
                  className="absolute right-2 top-2 rounded-full bg-black/60 p-1 text-neutral-300 transition-colors hover:bg-theme-red/80 hover:text-white"
                >
                  <X className="size-4" />
                </button>
                <div className="border-t border-theme-gray-light px-3 py-1.5 text-[11px] text-neutral-500">
                  {image?.name ?? "screenshot"}
                </div>
              </div>
            ) : (
              /* Drop-zone button */
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className={cn(
                  "flex h-24 w-full flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-theme-gray-light bg-theme-black text-sm text-neutral-500 transition-colors",
                  "hover:border-neutral-500 hover:text-neutral-300",
                )}
              >
                <ImagePlus className="size-5" />
                <span>Click to attach a screenshot</span>
                <span className="text-[11px] text-neutral-600">
                  PNG, JPG, WEBP, GIF — max 5 MB
                </span>
              </button>
            )}

            <input
              ref={fileInputRef}
              type="file"
              accept="image/png,image/jpeg,image/webp,image/gif"
              className="hidden"
              onChange={handleImageChange}
            />
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={submitting || !queryText.trim()}
            className="mt-1 inline-flex items-center justify-center rounded-full bg-gradient-to-r from-theme-red to-theme-yellow px-4 py-2.5 text-sm font-semibold text-black transition-all hover:brightness-110 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50"
          >
            {submitting ? "Submitting…" : "Submit report"}
          </button>
        </form>
      </motion.div>
    </motion.div>
  )
}
