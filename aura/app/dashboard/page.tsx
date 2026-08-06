import { getServerSession } from "next-auth"
import { authOptions } from "@/lib/auth/options"
import { redirect } from "next/navigation"
import { StudentAcademicDashboard } from "@/components/features/dashboard/StudentAcademicDashboard"
import DashboardShell from "./dashboard-shell"

export const metadata = {
  title: "Dashboard · AURA",
  description: "Your personal timetable dashboard — see today's classes and your weekly schedule.",
}

export default async function DashboardPage() {
  const session = await getServerSession(authOptions)

  if (!session?.user) {
    redirect("/login")
  }

  const user = session.user
  const role = (user.role as string) || ""

  if (role === "guest") {
    redirect("/")
  }

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
