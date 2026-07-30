import { getServerSession } from "next-auth"
import { authOptions } from "@/lib/auth/options"
import { redirect } from "next/navigation"
import { StudentAcademicDashboard } from "@/components/features/dashboard/StudentAcademicDashboard"
import DashboardShell from "./dashboard-shell"

export const metadata = {
  title: "Dashboard · AURA",
  description: "Your personal timetable — synced with your latest changes in chat.",
}

export default async function DashboardPage() {
  const session = await getServerSession(authOptions)

  if (!session?.user) {
    redirect("/login")
  }

  const user = session.user
  const role = (user.role as string) || ""

  // The student dashboard is timetable-only by design (see
  // StudentAcademicDashboard) — it no longer fetches CGPA, registration, or
  // fee-dues data, so there's nothing to await here before rendering.
  if (role === "student") {
    return (
      <StudentAcademicDashboard
        userName={user.name || "Student"}
        departmentName={user.department}
      />
    )
  }

  return <DashboardShell user={user} />
}
