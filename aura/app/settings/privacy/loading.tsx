import React from "react";
import { Loader2 } from "lucide-react";

export default function PrivacyLoading() {
  return (
    <div className="flex min-h-[400px] w-full flex-col items-center justify-center gap-3 p-8 text-neutral-400">
      <Loader2 className="h-8 w-8 animate-spin text-theme-yellow" />
      <p className="text-sm font-medium animate-pulse">Loading privacy settings...</p>
    </div>
  );
}