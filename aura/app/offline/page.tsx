"use client";

import React, { useState } from "react";
import { WifiOff, RotateCw, Home } from "lucide-react";
import Link from "next/link";

export default function OfflinePage() {
  const [checking, setChecking] = useState(false);

  // Allow the user to check if their connection has returned
  const handleRetry = () => {
    setChecking(true);
    if (typeof window !== "undefined") {
      setTimeout(() => {
        setChecking(false);
        if (window.navigator.onLine) {
          window.location.href = "/";
        }
      }, 800);
    }
  };

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-theme-black px-4 text-white">
      <div className="w-full max-w-md rounded-2xl border border-theme-gray-light bg-theme-gray/80 p-8 text-center backdrop-blur-md shadow-2xl">
        {/* Animated Wi-Fi Off Icon */}
        <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-theme-red/10 text-theme-red animate-pulse">
          <WifiOff className="h-10 w-10" />
        </div>

        <h1 className="mb-2 text-2xl font-bold tracking-tight text-white sm:text-3xl">
          You are offline
        </h1>
        
        <p className="mb-8 text-sm text-neutral-400">
          It looks like your internet connection is unavailable. AURA requires an active connection to search the knowledge base and query the ERP.
        </p>

        <div className="flex flex-col gap-3">
          <button
            onClick={handleRetry}
            disabled={checking}
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-theme-yellow px-4 py-3 font-semibold text-black transition-all hover:bg-theme-yellow/90 active:scale-98 disabled:opacity-50"
          >
            <RotateCw className={`h-4 w-4 ${checking ? "animate-spin" : ""}`} />
            {checking ? "Checking connection..." : "Retry Connection"}
          </button>

          <Link
            href="/"
            className="flex w-full items-center justify-center gap-2 rounded-xl border border-theme-gray-light bg-theme-black/40 px-4 py-3 font-semibold text-neutral-300 transition-all hover:bg-theme-gray-light"
          >
            <Home className="h-4 w-4" />
            Go to Home
          </Link>
        </div>
      </div>
    </div>
  );
}