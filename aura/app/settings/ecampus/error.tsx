"use client";

import React, { useEffect } from "react";
import { AlertCircle, RotateCcw } from "lucide-react";

export default function EcampusError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("eCampus settings error boundary caught:", error);
  }, [error]);

  return (
    <div className="flex min-h-[400px] w-full flex-col items-center justify-center p-8 text-center">
      <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur-md shadow-xl">
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-red-500/10 text-red-500">
          <AlertCircle className="h-6 w-6" />
        </div>
        <h2 className="mb-2 text-lg font-semibold text-white">Failed to load eCampus settings</h2>
        <p className="mb-6 text-sm text-slate-400">
          {error.message || "An unexpected error occurred. Please try again."}
        </p>
        <button
          onClick={() => reset()}
          className="flex mx-auto items-center justify-center gap-2 rounded-xl bg-blue-600 px-4 py-2.5 font-semibold text-white transition-all hover:bg-blue-500 active:scale-98"
        >
          <RotateCcw className="h-4 w-4" />
          Try Again
        </button>
      </div>
    </div>
  );
}