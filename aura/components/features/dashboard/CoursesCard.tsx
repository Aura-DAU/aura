"use client"

import { useState } from "react"
import { BookOpen, ChevronDown, ChevronUp } from "lucide-react"
import { cn } from "@/lib/utils"
import type { RegistrationData } from "@/lib/api/ecampus.action"

const COLLAPSED_LIMIT = 4

interface CoursesCardProps {
  data: RegistrationData | null
  error: string | null
}

/** Lists enrolled courses for the current semester with a collapse/expand toggle. */
export function CoursesCard({ data, error }: CoursesCardProps) {
  const [expanded, setExpanded] = useState(false)
  const courses = data?.courses ?? []
  const hasEcampusIssue =
    error === "ecampus_not_linked" || error === "ecampus_unavailable"

  const visibleCourses = expanded ? courses : courses.slice(0, COLLAPSED_LIMIT)
  const hasMore = courses.length > COLLAPSED_LIMIT

  return (
    <div className="rounded-2xl border border-theme-gray-light bg-theme-gray p-5">
      <div className="mb-4 flex items-center gap-2">
        <BookOpen className="size-4 shrink-0 text-theme-yellow" />
        <h2 className="text-sm font-semibold text-neutral-200">
          Registered Courses
          {data?.semester ? (
            <span className="ml-1.5 text-xs font-normal text-neutral-500">
              — Sem {data.semester}
            </span>
          ) : null}
        </h2>
      </div>

      {hasEcampusIssue ? (
        <p className="text-xs text-neutral-500">
          Link eCampus in Settings to see your registered courses.
        </p>
      ) : error ? (
        <p className="text-xs text-neutral-500">Unable to load courses right now.</p>
      ) : courses.length === 0 ? (
        <p className="text-xs text-neutral-500">No courses registered this semester.</p>
      ) : (
        <>
          <ul className="space-y-2">
            {visibleCourses.map((course, i) => (
              <li
                key={`${course.code}-${i}`}
                className="flex items-center justify-between gap-3 rounded-xl border border-theme-gray-light bg-theme-gray-light/40 px-3 py-2.5"
              >
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-neutral-100">{course.name}</p>
                  <p className="mt-0.5 text-xs text-neutral-500">{course.code}</p>
                </div>
                {course.credits != null ? (
                  <span className="shrink-0 rounded-full bg-theme-gray-lighter px-2 py-0.5 text-xs text-neutral-400">
                    {course.credits} cr
                  </span>
                ) : null}
              </li>
            ))}
          </ul>

          {hasMore ? (
            <button
              type="button"
              onClick={() => setExpanded((v) => !v)}
              className={cn(
                "mt-3 flex items-center gap-1 text-xs text-theme-yellow transition-opacity hover:opacity-80",
              )}
            >
              {expanded ? (
                <>
                  <ChevronUp className="size-3.5" />
                  Show less
                </>
              ) : (
                <>
                  <ChevronDown className="size-3.5" />
                  Show all ({courses.length - COLLAPSED_LIMIT} more)
                </>
              )}
            </button>
          ) : null}
        </>
      )}
    </div>
  )
}
