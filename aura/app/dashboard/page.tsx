import { getServerSession } from "next-auth"
import { authOptions } from "@/lib/auth/options"
import { redirect } from "next/navigation"
import {
  getCgpa,
  getRegistration,
  getFeeDues,
} from "@/lib/api/ecampus.action"
import { StudentAcademicDashboard } from "@/components/features/dashboard/StudentAcademicDashboard"
import DashboardShell from "./dashboard-shell"

export const metadata = {
  title: "Dashboard · AURA",
  description: "Your personal academic dashboard — timetable, CGPA, courses, and fees.",
}

export default async function DashboardPage() {
  const session = await getServerSession(authOptions)

  if (!session?.user) {
    redirect("/login")
  }

  const user = session.user
  const role = (user.role as string) || ""

  if (role === "student") {
    const [cgpaResult, registrationResult, feeDuesResult] = await Promise.all([
      getCgpa(),
      getRegistration(),
      getFeeDues(),
    ])

    return (
      <StudentAcademicDashboard
        userName={user.name || "Student"}
        departmentName={user.department}
        cgpa={{
          data: cgpaResult.ok ? cgpaResult.data : null,
          error: cgpaResult.ok ? null : cgpaResult.error,
        }}
        registration={{
          data: registrationResult.ok ? registrationResult.data : null,
          error: registrationResult.ok ? null : registrationResult.error,
        }}
        feeDues={{
          data: feeDuesResult.ok ? feeDuesResult.data : null,
          error: feeDuesResult.ok ? null : feeDuesResult.error,
        }}
      />
    )
  }

  return <DashboardShell user={user} />
}
