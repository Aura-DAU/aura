"use client"

import { Download, Share, X } from "lucide-react"
import { usePWAInstall } from "@/hooks/use-pwa-install"

/**
 * In-app install nudge (toast-style banner). Not an OS push notification —
 * browsers only allow the native install sheet after beforeinstallprompt,
 * and iOS requires Share → Add to Home Screen.
 */
export function InstallPromptBanner() {
  const { canInstall, isIos, showInstallUi, promptInstall, dismissPrompt } =
    usePWAInstall()

  if (!showInstallUi) return null

  return (
    <div
      role="status"
      aria-live="polite"
      className="pointer-events-none fixed inset-x-0 bottom-0 z-30 flex justify-center p-3 pb-[max(0.75rem,env(safe-area-inset-bottom))] sm:p-4"
    >
      <div className="pointer-events-auto flex w-full max-w-md items-start gap-3 rounded-2xl border border-theme-yellow/30 bg-theme-gray-light/95 px-4 py-3 text-neutral-100 shadow-[0_12px_40px_-12px_rgba(0,0,0,0.65)] backdrop-blur-md">
        <div className="mt-0.5 flex size-9 shrink-0 items-center justify-center rounded-xl bg-theme-yellow/15 text-theme-yellow">
          <Download className="size-4" aria-hidden />
        </div>

        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold text-neutral-50">Install AURA</p>
          {isIos && !canInstall ? (
            <p className="mt-0.5 text-xs leading-relaxed text-neutral-400">
              Tap{" "}
              <Share className="inline size-3.5 align-text-bottom text-theme-yellow" aria-hidden />{" "}
              Share, then <span className="text-neutral-200">Add to Home Screen</span>.
            </p>
          ) : (
            <p className="mt-0.5 text-xs leading-relaxed text-neutral-400">
              Add to your home screen for faster access and offline use.
            </p>
          )}

          {canInstall ? (
            <button
              type="button"
              onClick={() => {
                void promptInstall()
              }}
              className="mt-2 inline-flex items-center gap-1.5 rounded-full bg-theme-yellow px-3 py-1.5 text-xs font-semibold text-black transition-opacity hover:opacity-90"
            >
              <Download className="size-3.5" aria-hidden />
              Install app
            </button>
          ) : null}
        </div>

        <button
          type="button"
          onClick={dismissPrompt}
          aria-label="Dismiss install prompt"
          className="rounded-lg p-1.5 text-neutral-400 transition-colors hover:bg-white/5 hover:text-neutral-200"
        >
          <X className="size-4" />
        </button>
      </div>
    </div>
  )
}
