"use client"

import { useCallback, useEffect, useState } from "react"
import { toastError } from "@/lib/toast"

export type PushStatus = "unsupported" | "denied" | "unsubscribed" | "subscribed" | "loading"

export type PushPending = "subscribe" | "unsubscribe" | null

function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4)
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/")
  const rawData = window.atob(base64)
  const outputArray = new Uint8Array(rawData.length)
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i)
  }
  return outputArray
}

/**
 * Manages the "notify me 10 minutes before class" toggle: registers the
 * service worker, requests Notification permission, and creates/removes a
 * Web Push subscription synced with the backend (server/rag/pipeline/
 * timetable/notifier.py sends the actual reminders).
 */
export function usePushNotifications() {
  const [status, setStatus] = useState<PushStatus>("loading")
  const [pending, setPending] = useState<PushPending>(null)

  const checkStatus = useCallback(async () => {
    if (typeof window === "undefined" || !("serviceWorker" in navigator) || !("PushManager" in window)) {
      setStatus("unsupported")
      return
    }
    if (Notification.permission === "denied") {
      setStatus("denied")
      return
    }
    try {
      const registration = await navigator.serviceWorker.register("/sw.js")
      const existing = await registration.pushManager.getSubscription()
      setStatus(existing ? "subscribed" : "unsubscribed")
    } catch {
      setStatus("unsubscribed")
    }
  }, [])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    checkStatus()
  }, [checkStatus])

  const subscribe = useCallback(async () => {
    setPending("subscribe")
    try {
      const permission = await Notification.requestPermission()
      if (permission !== "granted") {
        setStatus(permission === "denied" ? "denied" : "unsubscribed")
        if (permission === "denied") {
          toastError("Notification permission was denied. Enable it in browser settings.")
        } else {
          toastError("Notification permission is required for class reminders.")
        }
        return
      }

      const keyRes = await fetch("/api/push/vapid-public-key")
      const keyJson = await keyRes.json()
      if (!keyRes.ok || !keyJson.publicKey) {
        console.warn("Push notifications aren't configured on the server yet.")
        setStatus("unsubscribed")
        toastError("Push notifications aren't configured on the server yet.")
        return
      }

      const registration = await navigator.serviceWorker.register("/sw.js")
      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(keyJson.publicKey),
      })

      const json = subscription.toJSON()
      const res = await fetch("/api/push/subscribe", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          endpoint: json.endpoint,
          keys: json.keys,
          user_agent: navigator.userAgent,
        }),
      })
      if (!res.ok) {
        throw new Error("Failed to save push subscription")
      }

      setStatus("subscribed")
    } catch (err) {
      console.error("Failed to subscribe to push notifications:", err)
      setStatus("unsubscribed")
      toastError("Could not enable class reminders. Please try again.")
    } finally {
      setPending(null)
    }
  }, [])

  const unsubscribe = useCallback(async () => {
    setPending("unsubscribe")
    try {
      const registration = await navigator.serviceWorker.getRegistration()
      const subscription = await registration?.pushManager.getSubscription()
      if (subscription) {
        const endpoint = subscription.endpoint
        await subscription.unsubscribe()
        const res = await fetch(`/api/push/subscribe?endpoint=${encodeURIComponent(endpoint)}`, {
          method: "DELETE",
        })
        if (!res.ok) {
          throw new Error("Failed to remove push subscription")
        }
      }
      setStatus("unsubscribed")
    } catch (err) {
      console.error("Failed to unsubscribe from push notifications:", err)
      setStatus("subscribed")
      toastError("Could not turn off class reminders. Please try again.")
    } finally {
      setPending(null)
    }
  }, [])

  return { status, pending, subscribe, unsubscribe }
}
