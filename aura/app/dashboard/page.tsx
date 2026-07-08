import { LayoutDashboard } from "lucide-react"
import { getServerSession } from "next-auth"
import { redirect } from "next/navigation"
import {
  getTimetableToday,
  getCgpa,
  getRegistration,
  getFeeDues,
} from "@/lib/api/ecampus.action"
import { authOptions } from "@/lib/auth/options"
import { TimetableCard } from "@/components/features/dashboard/TimetableCard"
import { CgpaCard } from "@/components/features/dashboard/CgpaCard"
import { CoursesCard } from "@/components/features/dashboard/CoursesCard"
import { FeeDuesCard } from "@/components/features/dashboard/FeeDuesCard"

// Attendance unavailable from eCampus — revisit when UniRP exposes this endpoint.
// TODO(unirp): Implement AttendanceCard once the UniRP attendance endpoint is confirmed.

export const metadata = {
  title: "Dashboard · AURA",
  description: "Your personal academic dashboard — timetable, CGPA, courses, and fees.",
}

/** Student Dashboard — all eCampus data fetched in parallel on the server. */
export default async function DashboardPage() {
  const session = await getServerSession(authOptions)

  if (!session?.user) {
    redirect("/login")
  }

  // Fetch all four data sources in parallel; each call is independent and fails gracefully.
  const [timetableResult, cgpaResult, registrationResult, feeDuesResult] =
    await Promise.all([
      getTimetableToday(),
      getCgpa(),
      getRegistration(),
      getFeeDues(),
    ])

  return (
    <div className="min-h-screen bg-theme-black px-4 py-8 md:px-8">
      {/* Subtle background grid — matches chat shell aesthetic */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(255,255,255,0.025)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.025)_1px,transparent_1px)] bg-[size:24px_24px]" />
        <div className="absolute -left-24 -top-24 size-72 rounded-full bg-theme-red/10 blur-3xl" />
        <div className="absolute -bottom-24 -right-24 size-72 rounded-full bg-theme-yellow/10 blur-3xl" />
      </div>

      <div className="relative mx-auto max-w-5xl">
        {/* Page heading */}
        <div className="mb-8 flex items-center gap-3">
          <LayoutDashboard className="size-5 text-theme-yellow" />
          <h1 className="bg-gradient-to-r from-theme-red to-theme-yellow bg-clip-text text-xl font-semibold text-transparent">
            My Dashboard
          </h1>
        </div>

        {/* Card grid */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {/* Timetable — spans full width on sm, 2 cols on lg */}
          <div className="sm:col-span-2 lg:col-span-2">
            <TimetableCard
              entries={timetableResult.ok ? timetableResult.data : null}
              error={timetableResult.ok ? null : timetableResult.error}
            />
          </div>

          {/* CGPA */}
          <CgpaCard
            data={cgpaResult.ok ? cgpaResult.data : null}
            error={cgpaResult.ok ? null : cgpaResult.error}
          />

          {/* Registered courses — spans full width on sm, 2 cols on lg */}
          <div className="sm:col-span-2 lg:col-span-2">
            <CoursesCard
              data={registrationResult.ok ? registrationResult.data : null}
              error={registrationResult.ok ? null : registrationResult.error}
            />
          </div>

          {/* Fee / dues */}
          <FeeDuesCard
            data={feeDuesResult.ok ? feeDuesResult.data : null}
            error={feeDuesResult.ok ? null : feeDuesResult.error}
          />
        </div>
      </div>
    </div>
  )
}
