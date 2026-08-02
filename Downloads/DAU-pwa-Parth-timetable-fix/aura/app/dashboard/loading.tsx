import { DashboardSkeleton } from "@/components/features/dashboard/DashboardSkeleton"

/** Loading UI shown by Next.js while the dashboard page fetches eCampus data. */
export default function DashboardLoading() {
  return (
    <div className="min-h-screen bg-theme-black px-4 py-8 md:px-8">
      <div className="mx-auto max-w-5xl">
        <div className="mb-8 h-6 w-40 animate-pulse rounded-full bg-theme-gray-light" />
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <div className="sm:col-span-2 lg:col-span-2">
            <DashboardSkeleton rows={3} />
          </div>
          <DashboardSkeleton rows={1} />
          <div className="sm:col-span-2 lg:col-span-2">
            <DashboardSkeleton rows={4} />
          </div>
          <DashboardSkeleton rows={2} />
        </div>
      </div>
    </div>
  )
}
