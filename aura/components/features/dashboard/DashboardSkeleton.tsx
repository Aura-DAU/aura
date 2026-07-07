import { cn } from "@/lib/utils"

interface DashboardSkeletonProps {
  className?: string
  /** Number of skeleton rows to render inside the card body */
  rows?: number
}

/** Reusable skeleton card used by all dashboard cards while data is loading. */
export function DashboardSkeleton({ className, rows = 3 }: DashboardSkeletonProps) {
  return (
    <div
      className={cn(
        "rounded-2xl border border-theme-gray-light bg-theme-gray p-5 animate-pulse",
        className,
      )}
    >
      {/* Title bar */}
      <div className="mb-4 h-4 w-1/3 rounded-full bg-theme-gray-light" />
      {/* Content rows */}
      <div className="space-y-2.5">
        {Array.from({ length: rows }).map((_, i) => (
          <div
            key={i}
            className="h-3 rounded-full bg-theme-gray-light"
            style={{ width: `${75 - i * 10}%` }}
          />
        ))}
      </div>
    </div>
  )
}
