import { describe, it, expect, vi } from "vitest";
import { login } from "./auth.action";
import { LoginSchema, RegisterSchema, LoginInput, RegisterInput } from "./auth.schema";

vi.mock("../db/user-db", () => {
  const mockUsers = [
    {
      role: "student",
      email: "test@dau.edu",
      passwordHash: "password123",
      name: "Test Student",
      branch: "B.Tech (ICT)",
      year: "3rd Year",
      semester: "Semester V",
    }
  ];
  return {
    getUsers: vi.fn(async () => mockUsers),
    saveUser: vi.fn(async (user) => {
      if (user.email === "test@dau.edu") {
        throw new Error("User already exists");
      }
      mockUsers.push({
        ...user,
        passwordHash: user.password
      });
    }),
    updateUserProfile: vi.fn(async () => {}),
    verifyPassword: vi.fn((password, stored) => password === stored),
  };
});

vi.mock("next/headers", () => {
  const store: Record<string, string> = {};
  return {
    cookies: vi.fn(async () => ({
      set: vi.fn((key, val) => { store[key] = val; }),
      get: vi.fn((key) => store[key] ? { name: key, value: store[key] } : undefined),
      delete: vi.fn((key) => { delete store[key]; }),
    })),
    headers: vi.fn(async () => ({
      get: vi.fn((key) => {
        if (key === "x-forwarded-for") return "127.0.0.1";
        return null;
      }),
    })),
  };
});

describe("Auth Schemas", () => {
  it("should validate a correct student login", () => {
    const data = {
      email: "test@dau.edu",
      password: "password123",
      role: "student",
    };
    const parsed = LoginSchema.safeParse(data);
    expect(parsed.success).toBe(true);
  });

  it("should reject an invalid email for login", () => {
    const data = {
      email: "not-an-email",
      password: "password123",
      role: "student",
    };
    const parsed = LoginSchema.safeParse(data);
    expect(parsed.success).toBe(false);
  });

  it("should reject a password under 6 characters", () => {
    const data = {
      email: "test@dau.edu",
      password: "123",
      role: "student",
    };
    const parsed = LoginSchema.safeParse(data);
    expect(parsed.success).toBe(false);
  });

  it("should validate a student register with @dau.edu", () => {
    const data = {
      role: "student",
      email: "newstudent@dau.edu",
      password: "password123",
      name: "New Student",
    };
    const parsed = RegisterSchema.safeParse(data);
    expect(parsed.success).toBe(true);
  });

  it("should reject a student register without @dau.edu", () => {
    const data = {
      role: "student",
      email: "student@example.com",
      password: "password123",
      name: "New Student",
    };
    const parsed = RegisterSchema.safeParse(data);
    expect(parsed.success).toBe(false);
  });
});

describe("Auth Server Actions", () => {
  it("should log in successfully with valid credentials", async () => {
    const res = await login({
      email: "test@dau.edu",
      password: "password123",
      role: "student",
    });
    expect(res.success).toBe(true);
    expect(res.session?.name).toBe("Test Student");
  });

  it("should return an error for invalid credentials", async () => {
    const res = await login({
      email: "test@dau.edu",
      password: "wrongpassword",
      role: "student",
    });
    expect(res.success).toBe(false);
    expect(res.error).toBeDefined();
  });
});
