"use server"

import { z } from "zod"
import { getServerSession } from "next-auth"
import { authOptions } from "@/lib/auth/options"
import { signInternalJwt } from "@/lib/auth/internal-jwt"
import { backendUrl } from "./backend"

type ActionResult<T> =
  | { ok: true; data: T }
  | { ok: false; error: string }

async function authHeaders(): Promise<Record<string, string> | null> {
  const session = await getServerSession(authOptions)
  if (!session?.user?.erpId) return null

  const token = signInternalJwt({
    role: session.user.role,
    erpId: session.user.erpId,
    department: session.user.department,
    email: session.user.email ?? undefined,
    fullName: session.user.fullName,
    currentYear: session.user.currentYear,
    currentSem: session.user.currentSem,
    currentSec: session.user.currentSec,
    currentLabGroup: session.user.currentLabGroup,
  })

  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  }
}

async function fetchBackend<T>(
  path: string,
  schema: z.ZodType<T>,
): Promise<ActionResult<T>> {
  const headers = await authHeaders()
  if (!headers) {
    return { ok: false, error: "ecampus_not_linked" }
  }

  let res: Response
  try {
    res = await fetch(backendUrl(path), {
      method: "GET",
      headers,
      cache: "no-store",
    })
  } catch {
    return { ok: false, error: "ecampus_unavailable" }
  }

  if (res.status === 401 || res.status === 403) {
    return { ok: false, error: "ecampus_not_linked" }
  }

  if (res.status === 404) {
    return { ok: false, error: "ecampus_unavailable" }
  }

  if (!res.ok) {
    return { ok: false, error: "ecampus_error" }
  }

  let json: unknown
  try {
    json = await res.json()
  } catch {
    return { ok: false, error: "ecampus_parse_error" }
  }

  const parsed = schema.safeParse(json)
  if (!parsed.success) {
    return { ok: false, error: "ecampus_schema_error" }
  }

  return { ok: true, data: parsed.data }
}

const timetableEntrySchema = z.object({
  course: z.string(),
  time: z.string(),
  room: z.string().optional(),
})

export type TimetableEntry = z.infer<typeof timetableEntrySchema>

const timetableResponseSchema = z.object({
  today: z.array(timetableEntrySchema),
})

export async function getTimetableToday(): Promise<ActionResult<TimetableEntry[]>> {
  const result = await fetchBackend("/ecampus/timetable/today", timetableResponseSchema)
  if (!result.ok) return result
  return { ok: true, data: result.data.today }
}

const cgpaResponseSchema = z.object({
  cgpa: z.number(),
  semester: z.number(),
})

export type CgpaData = z.infer<typeof cgpaResponseSchema>

export async function getCgpa(): Promise<ActionResult<CgpaData>> {
  return fetchBackend("/ecampus/cgpa", cgpaResponseSchema)
}

const courseEntrySchema = z.object({
  code: z.string(),
  name: z.string(),
  credits: z.number().optional(),
})

export type CourseEntry = z.infer<typeof courseEntrySchema>

const registrationResponseSchema = z.object({
  semester: z.number().optional(),
  courses: z.array(courseEntrySchema),
})

export type RegistrationData = z.infer<typeof registrationResponseSchema>

export async function getRegistration(): Promise<ActionResult<RegistrationData>> {
  return fetchBackend("/ecampus/registration", registrationResponseSchema)
}

const feeDuesResponseSchema = z.object({
  totalDues: z.number(),
  dueDate: z.string().optional(),
  breakdown: z
    .array(
      z.object({
        label: z.string(),
        amount: z.number(),
      }),
    )
    .optional(),
})

export type FeeDuesData = z.infer<typeof feeDuesResponseSchema>

export async function getFeeDues(): Promise<ActionResult<FeeDuesData>> {
  return fetchBackend("/ecampus/fees/dues", feeDuesResponseSchema)
}
