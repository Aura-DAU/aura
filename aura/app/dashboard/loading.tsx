import { DashboardSkeleton } from "@/components/features/dashboard/DashboardSkeleton"

/** Loading UI shown by Next.js while the dashboard page resolves the session. */
export default function DashboardLoading() {
  return (
    <div className="min-h-screen bg-theme-black px-4 py-8 md:px-8">
      <div className="mx-auto max-w-5xl">
        <div className="mb-8 h-6 w-40 animate-pulse rounded-full bg-theme-gray-light" />
        <DashboardSkeleton rows={5} />
      </div>
    </div>
  )
}
