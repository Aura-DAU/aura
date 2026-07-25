"use client"

import { useState, useMemo } from "react"
import { useCohortProfile, CohortProgramOption } from "@/hooks/use-cohort-profile"

/**
 * CohortOnboarding -- shown when a student's year/section is not yet set.
 * Pulls available programs, years, and sections from the actual timetable
 * data so the dropdowns are always in sync with what exists in the DB.
 *
 * After saving, calls onComplete() so the parent can reload the session.
 */
export function CohortOnboarding({ onComplete }: { onComplete: () => void }) {
  const { options, loading, saving, error, saveCohort } = useCohortProfile()

  const [selectedProgram, setSelectedProgram] = useState<string>("")
  const [selectedYear, setSelectedYear] = useState<number | "">("")
  const [selectedSemester, setSelectedSemester] = useState<number | "">("")
  const [selectedSection, setSelectedSection] = useState<string>("")

  // Derived data from selections
  const programData: CohortProgramOption | undefined = useMemo(
    () => options.find((o) => o.program === selectedProgram),
    [options, selectedProgram],
  )

  const yearData = useMemo(
    () => programData?.years.find((y) => y.year === selectedYear),
    [programData, selectedYear],
  )

  const handleProgramChange = (prog: string) => {
    setSelectedProgram(prog)
    setSelectedYear("")
    setSelectedSemester("")
    setSelectedSection("")
  }

  const handleYearChange = (yr: number) => {
    setSelectedYear(yr)
    setSelectedSection("")
    // Auto-select semester if only one option
    const yd = programData?.years.find((y) => y.year === yr)
    if (yd && yd.semesters.length === 1) {
      setSelectedSemester(yd.semesters[0])
    } else {
      setSelectedSemester("")
    }
  }

  const canSubmit =
    selectedProgram && selectedYear && selectedSemester && selectedSection && !saving

  const handleSubmit = async () => {
    if (!canSubmit) return
    try {
      await saveCohort({
        program: selectedProgram,
        year: selectedYear as number,
        semester: selectedSemester as number,
        section: selectedSection,
      })
      onComplete()
    } catch {
      // Error is already set in the hook
    }
  }

  if (loading) {
    return (
      <div className="cohort-onboarding">
        <div className="cohort-onboarding__loading">Loading profile setup...</div>
      </div>
    )
  }

  return (
    <div className="cohort-onboarding">
      <div className="cohort-onboarding__card">
        <h2 className="cohort-onboarding__title">Set Up Your Profile</h2>
        <p className="cohort-onboarding__subtitle">
          AURA needs to know your program and section to show you the right timetable.
          This takes a few seconds and you can change it later.
        </p>

        {error && <div className="cohort-onboarding__error">{error}</div>}

        <div className="cohort-onboarding__form">
          {/* Program */}
          <div className="cohort-onboarding__field">
            <label className="cohort-onboarding__label">Program</label>
            <select
              className="cohort-onboarding__select"
              value={selectedProgram}
              onChange={(e) => handleProgramChange(e.target.value)}
            >
              <option value="">Select your program</option>
              {options.map((o) => (
                <option key={o.program} value={o.program}>
                  {o.program}
                </option>
              ))}
            </select>
          </div>

          {/* Year */}
          {programData && (
            <div className="cohort-onboarding__field">
              <label className="cohort-onboarding__label">Year</label>
              <div className="cohort-onboarding__chips">
                {programData.years.map((y) => (
                  <button
                    key={y.year}
                    type="button"
                    className={`cohort-onboarding__chip ${
                      selectedYear === y.year ? "cohort-onboarding__chip--active" : ""
                    }`}
                    onClick={() => handleYearChange(y.year)}
                  >
                    {y.year === 1
                      ? "1st Year"
                      : y.year === 2
                        ? "2nd Year"
                        : y.year === 3
                          ? "3rd Year"
                          : `${y.year}th Year`}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Semester (if multiple options) */}
          {yearData && yearData.semesters.length > 1 && (
            <div className="cohort-onboarding__field">
              <label className="cohort-onboarding__label">Semester</label>
              <div className="cohort-onboarding__chips">
                {yearData.semesters.map((s) => (
                  <button
                    key={s}
                    type="button"
                    className={`cohort-onboarding__chip ${
                      selectedSemester === s ? "cohort-onboarding__chip--active" : ""
                    }`}
                    onClick={() => setSelectedSemester(s)}
                  >
                    Sem {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Section */}
          {yearData && yearData.sections.length > 0 && (
            <div className="cohort-onboarding__field">
              <label className="cohort-onboarding__label">Section</label>
              <div className="cohort-onboarding__chips">
                {yearData.sections.map((sec) => (
                  <button
                    key={sec}
                    type="button"
                    className={`cohort-onboarding__chip ${
                      selectedSection === sec ? "cohort-onboarding__chip--active" : ""
                    }`}
                    onClick={() => setSelectedSection(sec)}
                  >
                    Section {sec}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Submit */}
        <button
          className="cohort-onboarding__submit"
          disabled={!canSubmit}
          onClick={handleSubmit}
        >
          {saving ? "Saving..." : "Continue to AURA"}
        </button>
      </div>

      <style jsx>{`
        .cohort-onboarding {
          display: flex;
          align-items: center;
          justify-content: center;
          min-height: 60vh;
          padding: 2rem;
        }
        .cohort-onboarding__card {
          background: var(--card-bg, #1a1a2e);
          border: 1px solid var(--border-color, rgba(255, 255, 255, 0.08));
          border-radius: 16px;
          padding: 2.5rem;
          max-width: 480px;
          width: 100%;
          box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }
        .cohort-onboarding__title {
          font-size: 1.5rem;
          font-weight: 600;
          margin: 0 0 0.5rem;
          color: var(--text-primary, #e0e0e0);
        }
        .cohort-onboarding__subtitle {
          font-size: 0.875rem;
          color: var(--text-secondary, #999);
          margin: 0 0 1.5rem;
          line-height: 1.5;
        }
        .cohort-onboarding__error {
          background: rgba(220, 38, 38, 0.1);
          border: 1px solid rgba(220, 38, 38, 0.3);
          border-radius: 8px;
          padding: 0.75rem 1rem;
          color: #ef4444;
          font-size: 0.8125rem;
          margin-bottom: 1rem;
        }
        .cohort-onboarding__form {
          display: flex;
          flex-direction: column;
          gap: 1.25rem;
        }
        .cohort-onboarding__field {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }
        .cohort-onboarding__label {
          font-size: 0.8125rem;
          font-weight: 500;
          color: var(--text-secondary, #aaa);
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }
        .cohort-onboarding__select {
          background: var(--input-bg, #16213e);
          border: 1px solid var(--border-color, rgba(255, 255, 255, 0.12));
          border-radius: 8px;
          padding: 0.625rem 0.875rem;
          color: var(--text-primary, #e0e0e0);
          font-size: 0.9375rem;
          outline: none;
          transition: border-color 0.2s;
          cursor: pointer;
        }
        .cohort-onboarding__select:focus {
          border-color: var(--accent, #6c63ff);
        }
        .cohort-onboarding__chips {
          display: flex;
          gap: 0.5rem;
          flex-wrap: wrap;
        }
        .cohort-onboarding__chip {
          background: var(--input-bg, #16213e);
          border: 1px solid var(--border-color, rgba(255, 255, 255, 0.12));
          border-radius: 8px;
          padding: 0.5rem 1rem;
          color: var(--text-primary, #ccc);
          font-size: 0.875rem;
          cursor: pointer;
          transition: all 0.15s ease;
        }
        .cohort-onboarding__chip:hover {
          border-color: var(--accent, #6c63ff);
          background: rgba(108, 99, 255, 0.08);
        }
        .cohort-onboarding__chip--active {
          background: var(--accent, #6c63ff);
          border-color: var(--accent, #6c63ff);
          color: #fff;
          font-weight: 500;
        }
        .cohort-onboarding__submit {
          margin-top: 1.5rem;
          width: 100%;
          padding: 0.75rem;
          background: var(--accent, #6c63ff);
          color: #fff;
          border: none;
          border-radius: 10px;
          font-size: 1rem;
          font-weight: 600;
          cursor: pointer;
          transition: opacity 0.2s, transform 0.1s;
        }
        .cohort-onboarding__submit:hover:not(:disabled) {
          opacity: 0.9;
          transform: translateY(-1px);
        }
        .cohort-onboarding__submit:disabled {
          opacity: 0.4;
          cursor: not-allowed;
        }
        .cohort-onboarding__loading {
          color: var(--text-secondary, #999);
          font-size: 0.9375rem;
        }
      `}</style>
    </div>
  )
}
