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
    <div className="flex min-h-screen flex-col items-center justify-center bg-radial from-slate-900 to-slate-950 px-4 text-white">
      <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900/60 p-8 text-center backdrop-blur-md shadow-2xl">
        {/* Animated Wi-Fi Off Icon */}
        <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-red-500/10 text-red-500 animate-pulse">
          <WifiOff className="h-10 w-10" />
        </div>

        <h1 className="mb-2 text-2xl font-bold tracking-tight text-white sm:text-3xl">
          You are offline
        </h1>
        
        <p className="mb-8 text-sm text-slate-400">
          It looks like your internet connection is unavailable. AURA requires an active connection to search the knowledge base and query the ERP.
        </p>

        <div className="flex flex-col gap-3">
          <button
            onClick={handleRetry}
            disabled={checking}
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-blue-600 px-4 py-3 font-semibold text-white transition-all hover:bg-blue-500 active:scale-98 disabled:opacity-50"
          >
            <RotateCw className={`h-4 w-4 ${checking ? "animate-spin" : ""}`} />
            {checking ? "Checking connection..." : "Retry Connection"}
          </button>

          <Link
            href="/"
            className="flex w-full items-center justify-center gap-2 rounded-xl border border-slate-800 bg-slate-950/40 px-4 py-3 font-semibold text-slate-300 transition-all hover:bg-slate-900"
          >
            <Home className="h-4 w-4" />
            Go to Home
          </Link>
        </div>
      </div>
    </div>
  );
}