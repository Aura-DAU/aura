"use client"

import { useState } from "react"
import { CalendarDays, ChevronRight, Loader2 } from "lucide-react"
import { useCohortProfile } from "@/hooks/use-cohort-profile"
import { useElectives } from "@/hooks/use-electives"

interface TimetableSetupCardProps {
  onComplete: () => void
}

type Step = "year" | "section" | "lab_group" | "electives" | "saving"

const YEAR_OPTIONS = [
  { value: 1, label: "1st Year", sem: 1 },
  { value: 2, label: "2nd Year", sem: 3 },
  { value: 3, label: "3rd Year", sem: 5 },
  { value: 4, label: "4th Year", sem: 7 },
]

/** First-time setup wizard shown when a student has no cohort configured. */
export function TimetableSetupCard({ onComplete }: TimetableSetupCardProps) {
  const { options, saving, saveCohort } = useCohortProfile()
  const { data: electivesData, loading: electivesLoading } = useElectives()

  const [step, setStep] = useState<Step>("year")
  const [selectedYear, setSelectedYear] = useState<number | null>(null)
  const [selectedSem, setSelectedSem] = useState<number | null>(null)
  const [selectedSection, setSelectedSection] = useState<string | null>(null)
  const [selectedLabGroup, setSelectedLabGroup] = useState<string | null>(null)
  const [selectedElectives, setSelectedElectives] = useState<string[]>([])
  const [error, setError] = useState<string | null>(null)

  // Derive available sections from options, or use a sensible default
  const availableSections = (() => {
    if (options.length > 0) {
      const yr = options[0]?.years?.find((y) => y.year === selectedYear)
      if (yr?.sections?.length) return yr.sections
    }
    // Fallback: all known sections for BTech
    return ["A", "B", "C", "D"]
  })()

  const electives =
    electivesData?.electives?.filter((e) => !e.selected) ?? []

  const handleYearNext = () => {
    if (!selectedYear) return
    setStep("section")
  }

  const handleSectionNext = () => {
    if (!selectedSection) return
    setStep("lab_group")
  }

  const handleLabGroupNext = () => {
    // Offer elective selection only for years ≥ 3 where electives exist
    if (selectedYear && selectedYear >= 3 && electives.length > 0) {
      setStep("electives")
    } else {
      void handleSave([])
    }
  }

  const handleSave = async (electives: string[]) => {
    if (!selectedYear || !selectedSection || !selectedSem) return
    setStep("saving")
    setError(null)
    try {
      await saveCohort({
        program: "BTech",
        year: selectedYear,
        semester: selectedSem,
        section: selectedSection,
        lab_group: selectedLabGroup,
      })
      // Save elective selections if any
      if (electives.length > 0) {
        await fetch("/api/timetable/electives", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ course_codes: electives }),
        })
      }
      onComplete()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save. Please try again.")
      setStep("electives")
    }
  }

  const toggleElective = (code: string) => {
    setSelectedElectives((prev) =>
      prev.includes(code) ? prev.filter((c) => c !== code) : [...prev, code]
    )
  }

  return (
    <div className="rounded-2xl border border-theme-yellow/30 bg-theme-gray p-5">
      <div className="mb-4 flex items-center gap-2">
        <CalendarDays className="size-4 shrink-0 text-theme-yellow" />
        <h2 className="text-sm font-semibold text-neutral-200">
          Set Up Your Timetable
        </h2>
      </div>

      <p className="mb-5 text-xs leading-relaxed text-neutral-400">
        AURA needs your year and section to show your personalised class schedule.
        This only takes a few seconds.
      </p>

      {error && (
        <p className="mb-4 rounded-lg border border-theme-red/30 bg-theme-red/10 px-3 py-2 text-xs text-red-400">
          {error}
        </p>
      )}

      {/* ── Step: Year ─────────────────────────────────────────── */}
      {step === "year" && (
        <div>
          <p className="mb-3 text-xs font-medium text-neutral-300">
            Step 1 of 4 — Which year are you in?
          </p>
          <div className="grid grid-cols-2 gap-2">
            {YEAR_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                type="button"
                onClick={() => {
                  setSelectedYear(opt.value)
                  setSelectedSem(opt.sem)
                }}
                className={`rounded-xl border px-3 py-2.5 text-left text-xs font-medium transition-colors ${
                  selectedYear === opt.value
                    ? "border-theme-yellow bg-theme-yellow/10 text-theme-yellow"
                    : "border-theme-gray-light bg-theme-gray-light/40 text-neutral-300 hover:border-theme-gray-lighter"
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
          <button
            type="button"
            onClick={handleYearNext}
            disabled={!selectedYear}
            className="mt-4 flex w-full items-center justify-center gap-1.5 rounded-xl bg-gradient-to-r from-theme-red to-theme-yellow py-2.5 text-xs font-bold text-black transition-opacity hover:opacity-90 disabled:opacity-40"
          >
            Next <ChevronRight className="size-3.5" />
          </button>
        </div>
      )}

      {/* ── Step: Section ──────────────────────────────────────── */}
      {step === "section" && (
        <div>
          <p className="mb-3 text-xs font-medium text-neutral-300">
            Step 2 of 4 — Which section are you in?
          </p>
          <div className="grid grid-cols-4 gap-2">
            {availableSections.map((sec) => (
              <button
                key={sec}
                type="button"
                onClick={() => setSelectedSection(sec)}
                className={`rounded-xl border px-3 py-3 text-center text-sm font-bold transition-colors ${
                  selectedSection === sec
                    ? "border-theme-yellow bg-theme-yellow/10 text-theme-yellow"
                    : "border-theme-gray-light bg-theme-gray-light/40 text-neutral-300 hover:border-theme-gray-lighter"
                }`}
              >
                {sec}
              </button>
            ))}
          </div>
          <button
            type="button"
            onClick={handleSectionNext}
            disabled={!selectedSection}
            className="mt-4 flex w-full items-center justify-center gap-1.5 rounded-xl bg-gradient-to-r from-theme-red to-theme-yellow py-2.5 text-xs font-bold text-black transition-opacity hover:opacity-90 disabled:opacity-40"
          >
            Next <ChevronRight className="size-3.5" />
          </button>
          <button
            type="button"
            onClick={() => setStep("year")}
            className="mt-2 w-full text-center text-[10px] text-neutral-500 underline underline-offset-2"
          >
            ← Back
          </button>
        </div>
      )}

      {/* ── Step: Lab Group ──────────────────────────────────────── */}
      {step === "lab_group" && (
        <div>
          <p className="mb-3 text-xs font-medium text-neutral-300">
            Step 3 of 4 — Which lab group are you in?
          </p>
          <div className="grid grid-cols-4 gap-2">
            {["G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8"].map((grp) => (
              <button
                key={grp}
                type="button"
                onClick={() => setSelectedLabGroup(grp)}
                className={`rounded-xl border px-3 py-3 text-center text-sm font-bold transition-colors ${
                  selectedLabGroup === grp
                    ? "border-theme-yellow bg-theme-yellow/10 text-theme-yellow"
                    : "border-theme-gray-light bg-theme-gray-light/40 text-neutral-300 hover:border-theme-gray-lighter"
                }`}
              >
                {grp}
              </button>
            ))}
          </div>
          <button
            type="button"
            onClick={handleLabGroupNext}
            disabled={!selectedLabGroup}
            className="mt-4 flex w-full items-center justify-center gap-1.5 rounded-xl bg-gradient-to-r from-theme-red to-theme-yellow py-2.5 text-xs font-bold text-black transition-opacity hover:opacity-90 disabled:opacity-40"
          >
            Next <ChevronRight className="size-3.5" />
          </button>
          <button
            type="button"
            onClick={() => setStep("section")}
            className="mt-2 w-full text-center text-[10px] text-neutral-500 underline underline-offset-2"
          >
            ← Back
          </button>
          <button
             type="button"
             onClick={() => { setSelectedLabGroup(null); handleLabGroupNext(); }}
             className="mt-2 w-full text-center text-[10px] text-neutral-500 underline underline-offset-2"
          >
             I don&apos;t have a lab group
          </button>
        </div>
      )}

      {/* ── Step: Electives ────────────────────────────────────── */}
      {step === "electives" && (
        <div>
          <p className="mb-3 text-xs font-medium text-neutral-300">
            Step 4 of 4 — Select your elective courses (optional)
          </p>
          {electivesLoading ? (
            <div className="flex items-center gap-2 text-xs text-neutral-500">
              <Loader2 className="size-3.5 animate-spin" /> Loading electives…
            </div>
          ) : electives.length === 0 ? (
            <p className="text-xs text-neutral-500">No electives found for your cohort.</p>
          ) : (
            <div className="max-h-52 space-y-1.5 overflow-y-auto pr-1">
              {electives.map((elective) => (
                <button
                  key={elective.course_code}
                  type="button"
                  onClick={() => toggleElective(elective.course_code)}
                  className={`flex w-full items-center gap-2.5 rounded-xl border px-3 py-2.5 text-left text-xs transition-colors ${
                    selectedElectives.includes(elective.course_code)
                      ? "border-theme-yellow bg-theme-yellow/10"
                      : "border-theme-gray-light bg-theme-gray-light/40 hover:border-theme-gray-lighter"
                  }`}
                >
                  <span
                    className={`inline-flex size-4 shrink-0 items-center justify-center rounded border text-[10px] font-bold ${
                      selectedElectives.includes(elective.course_code)
                        ? "border-theme-yellow bg-theme-yellow text-black"
                        : "border-theme-gray-lighter text-neutral-500"
                    }`}
                  >
                    {selectedElectives.includes(elective.course_code) ? "✓" : ""}
                  </span>
                  <span>
                    <span className="block font-medium text-neutral-200">
                      {elective.course_name}
                    </span>
                    <span className="text-[10px] text-neutral-500">{elective.course_code}</span>
                  </span>
                </button>
              ))}
            </div>
          )}
          <button
            type="button"
            onClick={() => void handleSave(selectedElectives)}
            className="mt-4 flex w-full items-center justify-center gap-1.5 rounded-xl bg-gradient-to-r from-theme-red to-theme-yellow py-2.5 text-xs font-bold text-black transition-opacity hover:opacity-90"
          >
            Save &amp; Show My Timetable
          </button>
          <button
            type="button"
            onClick={() => void handleSave([])}
            className="mt-2 w-full text-center text-[10px] text-neutral-500 underline underline-offset-2"
          >
            Skip electives for now
          </button>
        </div>
      )}

      {/* ── Saving ─────────────────────────────────────────────── */}
      {(step === "saving" || saving) && (
        <div className="flex items-center justify-center gap-2 py-4 text-xs text-neutral-400">
          <Loader2 className="size-4 animate-spin text-theme-yellow" />
          Setting up your timetable…
        </div>
      )}
    </div>
  )
}
