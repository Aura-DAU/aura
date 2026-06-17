"use client";

import BrandMark from "./BrandMark";

interface StreamingIndicatorProps {
  step?: string;
}

export default function StreamingIndicator({ step }: StreamingIndicatorProps) {
  return (
    <div className="flex gap-3">
      <BrandMark size="md" />
      <div className="flex min-w-0 flex-1 flex-col gap-1.5">
        <div className="flex items-center gap-1.5">
          <span
            className="chat-v2-dot h-2 w-2 rounded-full bg-gradient-to-r from-theme-red to-theme-yellow"
            style={{ animationDelay: "0ms" }}
          />
          <span
            className="chat-v2-dot h-2 w-2 rounded-full bg-gradient-to-r from-theme-red to-theme-yellow"
            style={{ animationDelay: "150ms" }}
          />
          <span
            className="chat-v2-dot h-2 w-2 rounded-full bg-gradient-to-r from-theme-red to-theme-yellow"
            style={{ animationDelay: "300ms" }}
          />
        </div>
        {step && <p className="text-xs text-muted-foreground">{step}</p>}
      </div>
    </div>
  );
}
