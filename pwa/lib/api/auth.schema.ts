import { z } from "zod";

// Zod validation schemas
export const LoginSchema = z.object({
  email: z.string().email("Please enter a valid email address."),
  password: z.string().min(6, "Password must be at least 6 characters."),
  role: z.enum(["student", "parent"]),
});

export const RegisterSchema = z.object({
  role: z.enum(["student", "parent"]),
  email: z.string().email("Please enter a valid email address."),
  password: z.string().min(6, "Password must be at least 6 characters."),
  name: z.string().min(1, "Full name is required."),
  branch: z.string().optional(),
  year: z.string().optional(),
  semester: z.string().optional(),
  interests: z.string().optional(),
  linkedStudentEmail: z.string().optional(),
}).superRefine((data, ctx) => {
  if (data.role === "student") {
    if (!data.email.toLowerCase().endsWith("@dau.edu")) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["email"],
        message: "Student registration requires a university domain email (@dau.edu).",
      });
    }
  }
  if (data.role === "parent") {
    if (!data.linkedStudentEmail || !data.linkedStudentEmail.trim()) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["linkedStudentEmail"],
        message: "Linked Student Email is required.",
      });
    } else {
      const emailResult = z.string().email().safeParse(data.linkedStudentEmail);
      if (!emailResult.success) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ["linkedStudentEmail"],
          message: "Please enter a valid linked student email address.",
        });
      }
    }
  }
});

export type LoginInput = z.infer<typeof LoginSchema>;
export type RegisterInput = z.infer<typeof RegisterSchema>;
