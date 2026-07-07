import { CalendarDays } from "lucide-react"
import type { TimetableEntry } from "@/lib/api/ecampus.action"

interface TimetableCardProps {
  /** Today's timetable entries, or null when eCampus is not linked / unavailable */
  entries: TimetableEntry[] | null
  error: string | null
}

/** Displays today's classes fetched from the eCampus timetable tool. */
export function TimetableCard({ entries, error }: TimetableCardProps) {
  return (
    <div className="rounded-2xl border border-theme-gray-light bg-theme-gray p-5">
      <div className="mb-4 flex items-center gap-2">
        <CalendarDays className="size-4 text-theme-yellow shrink-0" />
        <h2 className="text-sm font-semibold text-neutral-200">Today&apos;s Timetable</h2>
      </div>

      {error === "ecampus_not_linked" || error === "ecampus_unavailable" ? (
        <p className="text-xs text-neutral-500">
          Link eCampus in Settings to see your timetable.
        </p>
      ) : error ? (
        <p className="text-xs text-neutral-500">Unable to load timetable right now.</p>
      ) : entries && entries.length === 0 ? (
        <p className="text-xs text-neutral-500">No classes today. 🎉</p>
      ) : entries ? (
        <ul className="space-y-2">
          {entries.map((entry, i) => (
            <li
              key={i}
              className="flex items-start justify-between gap-3 rounded-xl border border-theme-gray-light bg-theme-gray-light/40 px-3 py-2.5"
            >
              <div className="min-w-0">
                <p className="truncate text-sm font-medium text-neutral-100">{entry.course}</p>
                {entry.room ? (
                  <p className="mt-0.5 text-xs text-neutral-500">{entry.room}</p>
                ) : null}
              </div>
              <span className="shrink-0 rounded-full bg-theme-gray-lighter px-2 py-0.5 text-xs text-neutral-400">
                {entry.time}
              </span>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  )
}
