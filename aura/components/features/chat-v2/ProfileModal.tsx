"use client"

import { type FormEvent, useState, useMemo } from "react"
import { AnimatePresence, motion } from "framer-motion"
import { X } from "lucide-react"
import { toast } from "sonner"
import type { StudentProfile } from "@/lib/chat-types"
import { useSession } from "next-auth/react"
import { useCohortProfile, type CohortProgramOption } from "@/hooks/use-cohort-profile"

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

  const { options, profile: cohortProfile, saveCohort } = useCohortProfile()

  // Infer admission year from ERP ID (e.g. 202401226 -> 2024 -> Year 3, Sem 5)
  const inferredCohort = useMemo(() => {
    const erpId = session?.user?.erpId || profile.name
    const match = erpId?.match(/^(\d{4})\d+/)
    if (match) {
      const admissionYear = Number.parseInt(match[1], 10)
      const currentYear = Math.min(4, Math.max(1, 2026 - admissionYear + 1))
      const currentSem = (currentYear - 1) * 2 + 1
      return { year: currentYear, sem: currentSem }
    }
    return { year: 2, sem: 3 }
  }, [session?.user?.erpId, profile.name])

  const initialYear = cohortProfile?.current_year ?? session?.user?.currentYear ?? inferredCohort.year
  const initialSem = cohortProfile?.current_sem ?? session?.user?.currentSem ?? inferredCohort.sem
  const initialSec = cohortProfile?.current_sec ?? session?.user?.currentSec ?? "A"

  const [selectedProgram, setSelectedProgram] = useState<string>("B.Tech ICT")
  const [selectedYear, setSelectedYear] = useState<number>(initialYear)
  const [selectedSem, setSelectedSem] = useState<number>(initialSem)
  const [selectedSec, setSelectedSec] = useState<string>(initialSec)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setSaving(true)
    try {
      // 1. Save Cohort (Year, Semester, Section, Program) to PostgreSQL database
      await saveCohort({
        program: selectedProgram,
        year: selectedYear,
        semester: selectedSem,
        section: selectedSec,
      })

      // 2. Save local draft profile
      await onSave({
        ...draft,
        program: selectedProgram,
        year: `${selectedYear}${selectedYear === 1 ? "st" : selectedYear === 2 ? "nd" : selectedYear === 3 ? "rd" : "th"} year (Sem ${selectedSem}, Sec ${selectedSec})`,
      })

      toast.success("Profile & Cohort saved permanently!")
      onClose()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to save profile")
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
        className="relative w-full max-w-md max-h-[90vh] overflow-y-auto rounded-2xl border border-theme-gray-light bg-theme-gray p-6 shadow-2xl"
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
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="rounded-lg p-1.5 text-neutral-400 transition-colors hover:bg-theme-gray-light hover:text-neutral-100"
          >
            <X className="size-5" />
          </button>
        </div>

        {session?.user && (
          <div className="mb-5 rounded-xl border border-theme-gray-lighter bg-theme-black p-4">
            <div className="text-xs font-semibold text-theme-yellow uppercase tracking-wider mb-2">Verified Identity</div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <div className="text-[11px] text-neutral-500 mb-0.5">Role</div>
                <div className="text-xs font-medium text-neutral-200 capitalize">{session.user.role}</div>
              </div>
              <div>
                <div className="text-[11px] text-neutral-500 mb-0.5">Department</div>
                <div className="text-xs font-medium text-neutral-200">{session.user.department || "ICT"}</div>
              </div>
              <div className="col-span-2">
                <div className="text-[11px] text-neutral-500 mb-0.5">Student ID / ERP ID</div>
                <div className="text-xs font-mono font-medium text-theme-yellow">{session.user.erpId}</div>
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

          {/* Program Selection */}
          <div className="flex flex-col gap-1.5">
            <label htmlFor="program-select" className="text-xs font-medium text-neutral-400">
              Program / Branch
            </label>
            <select
              id="program-select"
              value={selectedProgram}
              onChange={(e) => setSelectedProgram(e.target.value)}
              className="rounded-xl border border-theme-gray-light bg-theme-black px-3 py-2 text-sm text-neutral-100 outline-none focus:border-theme-yellow"
            >
              {options.length > 0 ? (
                options.map((o: CohortProgramOption) => (
                  <option key={o.program} value={o.program}>
                    {o.program}
                  </option>
                ))
              ) : (
                <>
                  <option value="B.Tech ICT">B.Tech ICT</option>
                  <option value="B.Tech CSE">B.Tech CSE</option>
                  <option value="B.Tech MnC">B.Tech MnC</option>
                  <option value="B.Tech EVD">B.Tech EVD</option>
                </>
              )}
            </select>
          </div>

          {/* Year Selection (Auto-detected from ID) */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium text-neutral-400 flex items-center justify-between">
              <span>Academic Year</span>
              <span className="text-[10px] text-theme-yellow">Auto-detected from Student ID</span>
            </label>
            <div className="grid grid-cols-4 gap-2">
              {[1, 2, 3, 4].map((yr) => (
                <button
                  key={yr}
                  type="button"
                  onClick={() => {
                    setSelectedYear(yr)
                    setSelectedSem((yr - 1) * 2 + 1)
                  }}
                  className={`rounded-xl border py-2 text-xs font-medium transition-all ${
                    selectedYear === yr
                      ? "border-theme-yellow bg-theme-yellow/10 text-theme-yellow"
                      : "border-theme-gray-light bg-theme-black text-neutral-400 hover:border-theme-gray-lighter"
                  }`}
                >
                  {yr === 1 ? "1st" : yr === 2 ? "2nd" : yr === 3 ? "3rd" : "4th"} Year
                </button>
              ))}
            </div>
          </div>

          {/* Semester & Section Selection */}
          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-1.5">
              <label htmlFor="sem-select" className="text-xs font-medium text-neutral-400">
                Semester
              </label>
              <select
                id="sem-select"
                value={selectedSem}
                onChange={(e) => setSelectedSem(Number(e.target.value))}
                className="rounded-xl border border-theme-gray-light bg-theme-black px-3 py-2 text-sm text-neutral-100 outline-none focus:border-theme-yellow"
              >
                {[1, 2, 3, 4, 5, 6, 7, 8].map((s) => (
                  <option key={s} value={s}>
                    Semester {s}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex flex-col gap-1.5">
              <label htmlFor="sec-select" className="text-xs font-medium text-neutral-400">
                Section / Group
              </label>
              <select
                id="sec-select"
                value={selectedSec}
                onChange={(e) => setSelectedSec(e.target.value)}
                className="rounded-xl border border-theme-gray-light bg-theme-black px-3 py-2 text-sm text-neutral-100 outline-none focus:border-theme-yellow"
              >
                {["A", "B", "C", "D"].map((sec) => (
                  <option key={sec} value={sec}>
                    Section {sec}
                  </option>
                ))}
              </select>
            </div>
          </div>

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
            className="mt-2 inline-flex items-center justify-center rounded-full bg-gradient-to-r from-theme-red to-theme-yellow px-4 py-2.5 text-sm font-semibold text-black transition-opacity disabled:opacity-50 hover:opacity-90"
          >
            {saving ? "Saving to PostgreSQL…" : "Save profile permanently"}
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
}

function Field({ id, label, value, onChange, placeholder }: FieldProps) {
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
    </div>
  )
}
