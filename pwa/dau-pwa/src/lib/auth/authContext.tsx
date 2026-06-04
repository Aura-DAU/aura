"use client";

import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
} from "react";

// ── Types ────────────────────────────────────────────────────────────────────

export interface AuthUser {
  studentId: string;
  /** Display name derived on login */
  name: string;
}

interface AuthContextValue {
  user: AuthUser | null;
  /** True while the session is being read from storage on first mount */
  isLoading: boolean;
  login: (
    studentId: string,
    password: string
  ) => Promise<{ success: boolean; error?: string }>;
  logout: () => void;
}

// ── Storage key ──────────────────────────────────────────────────────────────

const AUTH_KEY = "dau_auth_session";

// ── Context ──────────────────────────────────────────────────────────────────

const AuthContext = createContext<AuthContextValue | null>(null);

// ── Provider ─────────────────────────────────────────────────────────────────

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Restore session from localStorage on first mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(AUTH_KEY);
      if (stored) {
        setUser(JSON.parse(stored) as AuthUser);
      }
    } catch {
      // Corrupt data — ignore and treat as logged out
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Mock login: accepts any non-empty studentId + password.
   * TODO: replace with real API call to backend auth endpoint when ready.
   */
  const login = useCallback(
    async (
      studentId: string,
      password: string
    ): Promise<{ success: boolean; error?: string }> => {
      const id = studentId.trim();
      const pw = password.trim();

      if (!id || !pw) {
        return { success: false, error: "Student ID and password are required." };
      }

      if (pw.length < 4) {
        return { success: false, error: "Password must be at least 4 characters." };
      }

      // Simulate a small network delay
      await new Promise((r) => setTimeout(r, 600));

      const newUser: AuthUser = {
        studentId: id,
        // Use the student ID as the display name for now;
        // replace with real name from API response in production
        name: id,
      };

      try {
        localStorage.setItem(AUTH_KEY, JSON.stringify(newUser));
      } catch {
        // localStorage may be unavailable (e.g. private browsing)
      }

      setUser(newUser);
      return { success: true };
    },
    []
  );

  const logout = useCallback(() => {
    try {
      localStorage.removeItem(AUTH_KEY);
    } catch {
      // ignore
    }
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

// ── Hook ─────────────────────────────────────────────────────────────────────

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth() must be called inside <AuthProvider>.");
  }
  return ctx;
}
