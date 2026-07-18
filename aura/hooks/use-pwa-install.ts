"use client"

import { useCallback, useEffect, useState } from "react"

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>
  userChoice: Promise<{ outcome: "accepted" | "dismissed"; platform: string }>
}

export function usePWAInstall() {
  const [installPrompt, setInstallPrompt] =
    useState<BeforeInstallPromptEvent | null>(null)
  const [isInstalled, setIsInstalled] = useState(false)

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

  return {
    canInstall: Boolean(installPrompt) && !isInstalled,
    isInstalled,
    promptInstall,
  }
}

declare global {
  interface Navigator {
    standalone?: boolean
  }
}
