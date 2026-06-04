"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth/authContext";

/**
 * Wraps any subtree and redirects unauthenticated visitors to the home page.
 * Renders a full-screen spinner while the session is being read from storage.
 */
export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !user) {
      router.replace("/");
    }
  }, [user, isLoading, router]);

  // Still reading localStorage — show a neutral loading screen
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#F8FAFC]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-[#E8400C] border-t-transparent rounded-full animate-spin" />
          <p className="text-xs font-semibold text-slate-400 tracking-wide">
            Loading session…
          </p>
        </div>
      </div>
    );
  }

  // Not logged in — render nothing while the redirect happens
  if (!user) return null;

  return <>{children}</>;
}
