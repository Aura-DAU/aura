"use client";

import React, { useEffect } from "react";
import { AlertCircle, RotateCcw } from "lucide-react";

export default function PrivacyError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Privacy settings error boundary caught:", error);
  }, [error]);

  return (
    <div className="flex min-h-[400px] w-full flex-col items-center justify-center p-8 text-center">
      <div className="w-full max-w-md rounded-2xl border border-theme-gray-light bg-theme-gray/80 p-6 backdrop-blur-md shadow-xl">
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-theme-red/10 text-theme-red">
          <AlertCircle className="h-6 w-6" />
        </div>
        <h2 className="mb-2 text-lg font-semibold text-white">Failed to load privacy settings</h2>
        <p className="mb-6 text-sm text-neutral-400">
          {error.message || "An unexpected error occurred. Please try again."}
        </p>
        <button
          onClick={() => reset()}
          className="flex mx-auto items-center justify-center gap-2 rounded-xl bg-theme-yellow px-4 py-2.5 font-semibold text-black transition-all hover:bg-theme-yellow/90 active:scale-98"
        >
          <RotateCcw className="h-4 w-4" />
          Try Again
        </button>
      </div>
    </div>
  );
}