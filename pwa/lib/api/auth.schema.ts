import { z } from "zod";

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
}); // Keep any existing .superRefine() logic if you had it attached here

export type LoginInput = z.infer<typeof LoginSchema>;
export type RegisterInput = z.infer<typeof RegisterSchema>;

export interface UserSession {
  role: "student" | "parent";
  email: string;
  name: string;
  linkedStudentEmail?: string;
}
