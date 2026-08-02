"use client"

import { type FormEvent, useState, useEffect, useRef } from "react"
import { AnimatePresence, motion } from "framer-motion"
import { X } from "lucide-react"
import { toast } from "sonner"
import type { StudentProfile } from "@/lib/chat-types"
import { useSession } from "next-auth/react"
import { toastError } from "@/lib/toast"

interface ProfileModalProps {
  open: boolean
  onClose: () => void
  profile: StudentProfile
  onSave: (profile: StudentProfile) => Promise<void>
}

export function ProfileModal({ open, onClose, profile, onSave }: ProfileModalProps) {
  return (
    <AnimatePresence>
      {open ? (
        <ProfileModalDialog
          key="profile-dialog"
          onClose={onClose}
          profile={profile}
          onSave={onSave}
        />
      ) : null}
    </AnimatePresence>
  )
}

interface ProfileModalDialogProps {
  onClose: () => void
  profile: StudentProfile
  onSave: (profile: StudentProfile) => Promise<void>
}

function ProfileModalDialog({ onClose, profile, onSave }: ProfileModalDialogProps) {
  const [draft, setDraft] = useState<StudentProfile>(profile)
  const [saving, setSaving] = useState(false)
  const { data: session } = useSession()
  const closeButtonRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose()
    }
    document.addEventListener("keydown", handleEscape)
    closeButtonRef.current?.focus()
    return () => document.removeEventListener("keydown", handleEscape)
  }, [onClose])

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setSaving(true)
    try {
      await onSave(draft)
      toast.success("Profile saved")
      onClose()
    } catch {
      toastError("Could not save profile")
    } finally {
      setSaving(false)
    }
  }

  return (
    <motion.div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      <div
        className="absolute inset-0 bg-black/70 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden="true"
      />
      <motion.div
        role="dialog"
        aria-modal="true"
        aria-label="Edit profile"
        className="relative w-full max-w-md rounded-2xl border border-theme-gray-light bg-theme-gray p-6"
        initial={{ scale: 0.95, opacity: 0, y: 12 }}
        animate={{ scale: 1, opacity: 1, y: 0 }}
        exit={{ scale: 0.95, opacity: 0, y: 12 }}
        transition={{ type: "spring", stiffness: 300, damping: 26 }}
      >
        <div className="mb-5 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-neutral-100">
            Your profile
          </h2>
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

        {session?.user && (
          <div className="mb-6 rounded-xl border border-theme-gray-lighter bg-theme-black p-4">
            <div className="text-xs font-semibold text-theme-yellow uppercase tracking-wider mb-3">Verified Identity</div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-xs text-neutral-500 mb-1">Role</div>
                <div className="text-sm text-neutral-200 capitalize">{session.user.role}</div>
              </div>
              <div>
                <div className="text-xs text-neutral-500 mb-1">Department</div>
                <div className="text-sm text-neutral-200">{session.user.department || "N/A"}</div>
              </div>
              <div className="col-span-2">
                <div className="text-xs text-neutral-500 mb-1">ERP ID</div>
                <div className="text-sm text-neutral-200">{session.user.erpId}</div>
              </div>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <Field
            id="name"
            label="Name"
            value={draft.name}
            onChange={(v) => setDraft((d) => ({ ...d, name: v }))}
          />
          <Field
            id="program"
            label="Program"
            placeholder="B.Tech CSE"
            value={draft.program}
            onChange={(v) => setDraft((d) => ({ ...d, program: v }))}
            hint={session?.user ? "Auto-filled from your ERP ID — edit if it's wrong" : undefined}
          />
          <Field
            id="year"
            label="Year"
            placeholder="2nd year"
            value={draft.year}
            onChange={(v) => setDraft((d) => ({ ...d, year: v }))}
            hint={session?.user ? "Auto-filled from your ERP ID — edit if it's wrong" : undefined}
          />
          <Field
            id="interests"
            label="Interests"
            placeholder="AI, robotics, design"
            value={draft.interests}
            onChange={(v) => setDraft((d) => ({ ...d, interests: v }))}
          />
          <button
            type="submit"
            disabled={saving}
            className="mt-2 inline-flex items-center justify-center rounded-full bg-gradient-to-r from-theme-red to-theme-yellow px-4 py-2.5 text-sm font-semibold text-black transition-opacity disabled:opacity-50"
          >
            {saving ? "Saving…" : "Save profile"}
          </button>
        </form>
      </motion.div>
    </motion.div>
  )
}

interface FieldProps {
  id: string
  label: string
  value: string
  onChange: (v: string) => void
  placeholder?: string
  hint?: string
}

function Field({ id, label, value, onChange, placeholder, hint }: FieldProps) {
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={id} className="text-xs font-medium text-neutral-400">
        {label}
      </label>
      <input
        id={id}
        type="text"
        value={value}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
        className="rounded-xl border border-theme-gray-light bg-theme-black px-3 py-2 text-sm text-neutral-100 outline-none transition-colors focus:border-theme-gray-lighter placeholder:text-neutral-600"
      />
      {hint && value ? (
        <span className="text-[11px] text-neutral-500">{hint}</span>
      ) : null}
    </div>
  )
}
