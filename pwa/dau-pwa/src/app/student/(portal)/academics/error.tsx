"use client";

import React, { useEffect } from "react";

export default function AcademicsError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Academics Route Error:", error);
  }, [error]);

  return (
    <div className="space-y-6 max-w-xl text-center py-12 mx-auto">
      <div className="bg-red-50 border border-red-200 rounded-3xl p-8 shadow-sm">
        <div className="w-12 h-12 bg-red-100 text-red-650 rounded-full flex items-center justify-center mx-auto text-xl font-bold mb-4">
          !
        </div>
        <h2 className="text-base font-black text-red-900 mb-2">Failed to Load Content</h2>
        <p className="text-xs text-red-700 leading-relaxed mb-6">
          AURA encountered an error while retrieving academic files. Please check your network or reload the page.
        </p>
        <button
          onClick={reset}
          className="bg-primary-dau hover:bg-[#D7380A] text-white px-5 py-2.5 rounded-xl text-xs font-bold transition-colors"
        >
          Try Again
        </button>
      </div>
    </div>
  );
}
