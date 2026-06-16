"use client";

import { KeyboardEvent, useRef } from "react";
import TextareaAutosize from "react-textarea-autosize";
import { ArrowUp, Mic, Square, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface ComposerProps {
  value: string;
  onChange: (v: string) => void;
  onSubmit: () => void;
  disabled?: boolean;
  isRecording?: boolean;
  isTranscribing?: boolean;
  micSupported?: boolean;
  onMicClick?: () => void;
  placeholder?: string;
}

export default function Composer({
  value,
  onChange,
  onSubmit,
  disabled,
  isRecording,
  isTranscribing,
  micSupported,
  onMicClick,
  placeholder,
}: ComposerProps) {
  const formRef = useRef<HTMLFormElement | null>(null);
  const trimmed = value.trim();
  const canSend = !!trimmed && !disabled && !isRecording;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (canSend) onSubmit();
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (canSend) onSubmit();
    }
  };

  return (
    <div className="mx-auto w-full max-w-3xl px-4 pt-2 pb-3">
      <form
        ref={formRef}
        onSubmit={handleSubmit}
        className="flex items-end gap-2 rounded-2xl border border-theme-gray-light bg-theme-gray/80 p-2 backdrop-blur transition-all focus-within:ring-2 focus-within:ring-theme-red/50"
      >
        <TextareaAutosize
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled || isRecording}
          minRows={1}
          maxRows={8}
          maxLength={2000}
          placeholder={placeholder ?? "Message AURA…"}
          className="flex-1 resize-none bg-transparent px-1 py-2 text-sm leading-6 text-foreground placeholder:text-muted-foreground focus:outline-none disabled:opacity-50"
        />

        {micSupported && onMicClick && (
          <button
            type="button"
            onClick={onMicClick}
            disabled={disabled || isTranscribing}
            aria-label={isRecording ? "Stop recording" : "Record voice"}
            className={cn(
              "grid h-9 w-9 shrink-0 place-items-center rounded-full transition-colors",
              isRecording
                ? "bg-theme-red text-black animate-pulse"
                : "text-muted-foreground hover:bg-theme-gray-light hover:text-foreground disabled:opacity-40 disabled:hover:bg-transparent",
            )}
          >
            {isTranscribing ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : isRecording ? (
              <Square className="h-3.5 w-3.5 fill-current" />
            ) : (
              <Mic className="h-4 w-4" />
            )}
          </button>
        )}

        <button
          type="submit"
          disabled={!canSend}
          aria-label="Send message"
          className={cn(
            "grid h-9 w-9 shrink-0 place-items-center rounded-full bg-gradient-to-r from-theme-red to-theme-yellow text-black transition-all",
            "hover:from-theme-red/90 hover:to-theme-yellow/90",
            !canSend && "opacity-50 hover:from-theme-red hover:to-theme-yellow",
          )}
        >
          <ArrowUp className="h-4 w-4" strokeWidth={2.5} />
        </button>
      </form>
      <p className="mt-2 text-center text-xs text-muted-foreground">
        AI can make mistakes. Verify important info.
      </p>
    </div>
  );
}
