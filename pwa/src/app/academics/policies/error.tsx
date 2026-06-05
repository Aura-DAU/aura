"use client";

import React, { useEffect } from "react";

export default function PoliciesError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Policies page error:", error);
  }, [error]);

  return (
    <div className="flex flex-col items-center justify-center min-h-[400px] p-6 text-center space-y-4">
      <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-full text-red-500 mb-2">
        <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
      </div>
      <h2 className="text-lg font-bold text-foreground">Something went wrong!</h2>
      <p className="text-xs text-text-muted max-w-sm leading-relaxed">
        Failed to load the university academic policies handbook. This could be due to a missing data folder or an access permission error.
      </p>
      <button
        onClick={() => reset()}
        className="px-4 py-2 bg-primary-dau text-white text-xs font-bold rounded-xl shadow-lg shadow-primary-dau/20 hover:scale-[1.02] active:scale-95 transition-all duration-200"
      >
        Try Again
      </button>
    </div>
  );
}
