import { IndianRupee } from "lucide-react"
import type { FeeDuesData } from "@/lib/api/ecampus.action"

interface FeeDuesCardProps {
  data: FeeDuesData | null
  error: string | null
}

/**
 * Fee / dues card — frontend half only.
 * Backend parser is partial; card degrades gracefully until it ships.
 */
export function FeeDuesCard({ data, error }: FeeDuesCardProps) {
  const hasEcampusIssue =
    error === "ecampus_not_linked" || error === "ecampus_unavailable"

  return (
    <div className="rounded-2xl border border-theme-gray-light bg-theme-gray p-5">
      <div className="mb-4 flex items-center gap-2">
        <IndianRupee className="size-4 shrink-0 text-theme-red" />
        <h2 className="text-sm font-semibold text-neutral-200">Fee &amp; Dues</h2>
      </div>

      {hasEcampusIssue ? (
        <p className="text-xs text-neutral-500">
          Link eCampus in Settings to see your dues.
        </p>
      ) : error ? (
        <p className="text-xs text-neutral-500">
          Fee data is not available yet. Check back soon.
        </p>
      ) : data ? (
        <div>
          <p className="text-3xl font-bold text-neutral-100">
            ₹{data.totalDues.toLocaleString("en-IN")}
          </p>
          {data.dueDate ? (
            <p className="mt-1 text-xs text-neutral-500">Due by {data.dueDate}</p>
          ) : null}
          {data.breakdown && data.breakdown.length > 0 ? (
            <ul className="mt-3 space-y-1.5">
              {data.breakdown.map((item, i) => (
                <li key={`${item.label}-${i}`} className="flex items-center justify-between text-xs">
                  <span className="text-neutral-400">{item.label}</span>
                  <span className="text-neutral-300">
                    ₹{item.amount.toLocaleString("en-IN")}
                  </span>
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}
    </div>
  )
}
