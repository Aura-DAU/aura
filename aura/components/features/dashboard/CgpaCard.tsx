import { TrendingUp } from "lucide-react"
import type { CgpaData } from "@/lib/api/ecampus.action"

interface CgpaCardProps {
  data: CgpaData | null
  error: string | null
}

/** Displays the student's current CGPA and semester fetched from eCampus. */
export function CgpaCard({ data, error }: CgpaCardProps) {
  const hasEcampusIssue =
    error === "ecampus_not_linked" || error === "ecampus_unavailable"

  return (
    <div className="rounded-2xl border border-theme-gray-light bg-theme-gray p-5">
      <div className="mb-4 flex items-center gap-2">
        <TrendingUp className="size-4 shrink-0 text-theme-red" />
        <h2 className="text-sm font-semibold text-neutral-200">CGPA</h2>
      </div>

      {hasEcampusIssue ? (
        <p className="text-xs text-neutral-500">
          Link eCampus in Settings to see your CGPA.
        </p>
      ) : error ? (
        <p className="text-xs text-neutral-500">Unable to load CGPA right now.</p>
      ) : data ? (
        <div>
          <p className="bg-gradient-to-r from-theme-red to-theme-yellow bg-clip-text text-4xl font-bold text-transparent">
            {data.cgpa.toFixed(2)}
          </p>
          <p className="mt-1 text-xs text-neutral-500">as of Semester {data.semester}</p>
        </div>
      ) : (
        <p className="text-4xl font-bold text-neutral-500">—</p>
      )}
    </div>
  )
}
