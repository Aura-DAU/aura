"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Copy, RotateCw, ThumbsUp, ThumbsDown, Check } from "lucide-react";
import { cn } from "@/lib/utils";
import { ChatMessage, Citation } from "@/app/api/chat.service";
import BrandMark from "./BrandMark";

interface MessageProps {
  message: ChatMessage;
  citations?: Citation[];
  onRegenerate?: () => void;
  isLast?: boolean;
}

export default function Message({ message, citations, onRegenerate, isLast }: MessageProps) {
  const [copied, setCopied] = useState(false);
  const [feedback, setFeedback] = useState<"up" | "down" | null>(null);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // ignore
    }
  };

  if (message.role === "user") {
    return (
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2 }}
        className="flex justify-end"
      >
        <div className="max-w-[75%] rounded-2xl bg-theme-gray-light px-4 py-3 text-foreground whitespace-pre-wrap break-words">
          {message.content}
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className="group flex gap-3"
    >
      <BrandMark size="md" />
      <div className="min-w-0 flex-1">
        <div className="chat-v2-prose prose prose-invert max-w-none text-foreground whitespace-pre-wrap break-words leading-relaxed">
          {message.content}
        </div>

        {citations && citations.length > 0 && isLast && (
          <div className="mt-4 flex flex-wrap gap-2">
            {citations.map((c, i) => (
              <span
                key={`${c.file}-${i}`}
                className="inline-flex items-center gap-1.5 rounded-full border border-theme-gray-light bg-theme-gray-light/40 px-2.5 py-1 text-xs text-muted-foreground"
              >
                <span className="h-1.5 w-1.5 rounded-full bg-theme-yellow" />
                {c.title || c.file}
              </span>
            ))}
          </div>
        )}

        <div className="mt-2 flex items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100">
          <button
            type="button"
            onClick={handleCopy}
            aria-label="Copy"
            className="rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-theme-gray-light hover:text-theme-red"
          >
            {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
          </button>
          {onRegenerate && (
            <button
              type="button"
              onClick={onRegenerate}
              aria-label="Regenerate"
              className="rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-theme-gray-light hover:text-theme-red"
            >
              <RotateCw className="h-3.5 w-3.5" />
            </button>
          )}
          <button
            type="button"
            onClick={() => setFeedback((f) => (f === "up" ? null : "up"))}
            aria-label="Thumbs up"
            className={cn(
              "rounded-md p-1.5 transition-colors hover:bg-theme-gray-light",
              feedback === "up"
                ? "text-theme-yellow"
                : "text-muted-foreground hover:text-theme-red",
            )}
          >
            <ThumbsUp className="h-3.5 w-3.5" />
          </button>
          <button
            type="button"
            onClick={() => setFeedback((f) => (f === "down" ? null : "down"))}
            aria-label="Thumbs down"
            className={cn(
              "rounded-md p-1.5 transition-colors hover:bg-theme-gray-light",
              feedback === "down"
                ? "text-theme-red"
                : "text-muted-foreground hover:text-theme-red",
            )}
          >
            <ThumbsDown className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>
    </motion.div>
  );
}
