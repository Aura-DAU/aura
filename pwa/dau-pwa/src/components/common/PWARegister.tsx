"use client";

import { useEffect } from "react";

export default function PWARegister() {
  useEffect(() => {
    if (
      typeof window !== "undefined" &&
      "serviceWorker" in navigator
    ) {
      window.addEventListener("load", () => {
        navigator.serviceWorker
          .register("/sw.js")
          .then((registration) => {
            console.log("DAU PWA Service Worker registered with scope:", registration.scope);
          })
          .catch((error) => {
            console.error("DAU PWA Service Worker registration failed:", error);
          });
      });
    }
  }, []);

  return null;
}
