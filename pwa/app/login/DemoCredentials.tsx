import React from "react";
import { FlaskConical } from "lucide-react";

interface DemoCredentialsProps {
  onFillDemo: (role: "student" | "parent") => void;
}

export function DemoCredentials({ onFillDemo }: DemoCredentialsProps) {
  return (
    <div className="mt-5 rounded-3xl border-2 border-dashed border-[var(--color-aura-ink)]/60 dark:border-slate-600 p-4">
      <div className="flex items-center gap-2 mb-3 text-[10px] font-black uppercase tracking-wider text-[var(--color-aura-ink)] dark:text-slate-300">
        <FlaskConical className="w-3.5 h-3.5 text-brand-500 shrink-0" />
        <span>demo quick-fill</span>
      </div>
      <div className="flex gap-3">
        <button
          type="button"
          onClick={() => onFillDemo("student")}
          className="flex-1 py-2.5 px-3 text-xs font-black rounded-2xl border-2 border-[var(--color-aura-ink)] bg-[var(--color-aura-mint)] text-[var(--color-aura-ink)] shadow-sticker-sm hover:-translate-y-0.5 active:translate-x-0.5 active:translate-y-0.5 active:shadow-none transition-all cursor-pointer dark:border-slate-100"
        >
          🎓 demo · student
        </button>
        <button
          type="button"
          onClick={() => onFillDemo("parent")}
          className="flex-1 py-2.5 px-3 text-xs font-black rounded-2xl border-2 border-[var(--color-aura-ink)] bg-[var(--color-aura-coral)] text-[var(--color-aura-ink)] shadow-sticker-sm hover:-translate-y-0.5 active:translate-x-0.5 active:translate-y-0.5 active:shadow-none transition-all cursor-pointer dark:border-slate-100"
        >
          👪 demo · parent
        </button>
      </div>
    </div>
  );
}
