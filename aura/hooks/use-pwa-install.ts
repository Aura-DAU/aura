"use client"

import { useCallback, useEffect, useState, useSyncExternalStore } from "react"

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>
  userChoice: Promise<{ outcome: "accepted" | "dismissed"; platform: string }>
}

const DISMISS_KEY = "aura-install-dismissed"
const DISMISS_DAYS = 14
const DISMISS_EVENT = "aura-install-dismiss-changed"

function readDismissed(): boolean {
  try {
    const raw = localStorage.getItem(DISMISS_KEY)
    if (!raw) return false
    const until = Number(raw)
    return Number.isFinite(until) && Date.now() < until
  } catch {
    return false
  }
}

function detectIos(): boolean {
  if (typeof navigator === "undefined") return false
  const ua = navigator.userAgent
  return (
    /iPad|iPhone|iPod/.test(ua) ||
    (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1)
  )
}

function subscribeDismiss(onStoreChange: () => void) {
  window.addEventListener(DISMISS_EVENT, onStoreChange)
  window.addEventListener("storage", onStoreChange)
  return () => {
    window.removeEventListener(DISMISS_EVENT, onStoreChange)
    window.removeEventListener("storage", onStoreChange)
  }
}

function subscribeNoop() {
  return () => {}
}

export function usePWAInstall() {
  const [installPrompt, setInstallPrompt] =
    useState<BeforeInstallPromptEvent | null>(null)
  const [isInstalled, setIsInstalled] = useState(false)

  const isIos = useSyncExternalStore(subscribeNoop, detectIos, () => false)
  const dismissed = useSyncExternalStore(
    subscribeDismiss,
    readDismissed,
    () => true,
  )

  useEffect(() => {
    const media = window.matchMedia("(display-mode: standalone)")
    const syncInstalled = () => {
      setIsInstalled(media.matches || window.navigator.standalone === true)
    }
    syncInstalled()
    media.addEventListener("change", syncInstalled)

    const onBeforeInstallPrompt = (event: Event) => {
      event.preventDefault()
      setInstallPrompt(event as BeforeInstallPromptEvent)
    }

    const onAppInstalled = () => {
      setInstallPrompt(null)
      setIsInstalled(true)
    }

    window.addEventListener("beforeinstallprompt", onBeforeInstallPrompt)
    window.addEventListener("appinstalled", onAppInstalled)

    return () => {
      media.removeEventListener("change", syncInstalled)
      window.removeEventListener("beforeinstallprompt", onBeforeInstallPrompt)
      window.removeEventListener("appinstalled", onAppInstalled)
    }
  }, [])

  const promptInstall = useCallback(async () => {
    if (!installPrompt) return false
    await installPrompt.prompt()
    const { outcome } = await installPrompt.userChoice
    setInstallPrompt(null)
    return outcome === "accepted"
  }, [installPrompt])

  const dismissPrompt = useCallback(() => {
    const until = Date.now() + DISMISS_DAYS * 24 * 60 * 60 * 1000
    try {
      localStorage.setItem(DISMISS_KEY, String(until))
    } catch {
      /* storage unavailable */
    }
    window.dispatchEvent(new Event(DISMISS_EVENT))
  }, [])

  const canInstall = Boolean(installPrompt) && !isInstalled
  // Chromium: native install sheet. iOS Safari: show Add to Home Screen tips.
  const showInstallUi =
    !isInstalled && !dismissed && (canInstall || isIos)

  return {
    canInstall,
    isInstalled,
    isIos,
    showInstallUi,
    promptInstall,
    dismissPrompt,
  }
}

declare global {
  interface Navigator {
    standalone?: boolean
  }
}
