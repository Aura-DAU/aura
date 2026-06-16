import React from "react";
import { Info } from "lucide-react";

interface DemoCredentialsProps {
  onFillDemo: (role: "student" | "parent") => void;
}

export function DemoCredentials({ onFillDemo }: DemoCredentialsProps) {
  return (
    <div className="mt-6 p-4 bg-white/40 dark:bg-slate-900/40 border border-slate-200 dark:border-slate-800/60 rounded-2xl shadow-sm">
      <div className="flex items-center gap-2 mb-2 text-xs font-semibold text-slate-700 dark:text-slate-300">
        <Info className="w-3.5 h-3.5 text-brand-500 shrink-0" />
        <span>Demo Quick-Fill Credentials</span>
      </div>
      <p className="text-[11px] text-slate-500 dark:text-slate-400 mb-3 leading-relaxed">
        Use these buttons to instantly log in using preset Student or Parent profiles for testing.
      </p>
      <div className="flex gap-3">
        <button
          type="button"
          onClick={() => onFillDemo("student")}
          className="flex-1 py-2 px-3 text-[11px] font-semibold border border-brand-200 dark:border-brand-900/50 hover:bg-brand-50 dark:hover:bg-brand-950/20 text-brand-700 dark:text-brand-400 bg-white/70 dark:bg-slate-900/70 rounded-xl transition-colors cursor-pointer"
        >
          Demo Student Account
        </button>
        <button
          type="button"
          onClick={() => onFillDemo("parent")}
          className="flex-1 py-2 px-3 text-[11px] font-semibold border border-brand-200 dark:border-brand-900/50 hover:bg-brand-50 dark:hover:bg-brand-950/20 text-brand-700 dark:text-brand-400 bg-white/70 dark:bg-slate-900/70 rounded-xl transition-colors cursor-pointer"
        >
          Demo Parent Account
        </button>
      </div>
    </div>
  );
}
