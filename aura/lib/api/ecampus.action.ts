"use server"

import { z } from "zod"
import { backendUrl } from "./backend"

// ─── Response envelope ────────────────────────────────────────────────────────

type ActionResult<T> =
  | { ok: true; data: T }
  | { ok: false; error: string }

// ─── Shared fetch helper ──────────────────────────────────────────────────────

async function fetchBackend<T>(
  path: string,
  schema: z.ZodType<T>,
): Promise<ActionResult<T>> {
  let res: Response
  try {
    res = await fetch(backendUrl(path), {
      method: "GET",
      headers: { "Content-Type": "application/json" },
      // Next.js: opt out of caching for live ERP data
      cache: "no-store",
    })
  } catch {
    return { ok: false, error: "ecampus_unavailable" }
  }

  if (res.status === 401 || res.status === 403) {
    return { ok: false, error: "ecampus_not_linked" }
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

// ─── Timetable ────────────────────────────────────────────────────────────────

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

// ─── CGPA ─────────────────────────────────────────────────────────────────────

const cgpaResponseSchema = z.object({
  cgpa: z.number(),
  semester: z.number(),
})

export type CgpaData = z.infer<typeof cgpaResponseSchema>

export async function getCgpa(): Promise<ActionResult<CgpaData>> {
  return fetchBackend("/ecampus/cgpa", cgpaResponseSchema)
}

// ─── Registration (enrolled courses) ─────────────────────────────────────────

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

// ─── Fee / Dues ───────────────────────────────────────────────────────────────
// NOTE: Backend parser (Parth) is still in progress (🟡 Partial).
// This action will return ok:false/ecampus_unavailable until it ships.

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
