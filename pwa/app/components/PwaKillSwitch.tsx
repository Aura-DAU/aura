"use client";

import { useEffect } from "react";

export function PwaKillSwitch() {
  useEffect(() => {
    if (process.env.NODE_ENV === "development" && "serviceWorker" in navigator) {
      navigator.serviceWorker.getRegistrations().then((registrations) => {
        for (const registration of registrations) {
          registration.unregister();
          console.log("💀 Zombie Service Worker Killed in Dev Mode");
        }
      });
    }
  }, []);

  return null;
}