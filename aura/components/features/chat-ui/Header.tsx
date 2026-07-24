"use client"

import React, { useEffect, useRef, useState } from "react"
import { useRouter } from "next/navigation"
import { Download, LogIn, LogOut, Menu, Trash2 } from "lucide-react"
import { cn } from "@/lib/utils"
import { useSession, signOut } from "next-auth/react"
import { BrandMark } from "@/components/ui/brand-mark"

interface HeaderProps {
  onToggleSidebar: () => void
  onClearChat: () => void
  canInstall: boolean
  onInstall: () => void
}

export function Header({
  onToggleSidebar,
  onClearChat,
  canInstall,
  onInstall,
}: HeaderProps) {
  const router = useRouter()
  const { data: session } = useSession()
  const [confirmClear, setConfirmClear] = useState(false)
  const confirmTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    return () => {
      if (confirmTimerRef.current) clearTimeout(confirmTimerRef.current)
    }
  }, [])

  const handleClear = () => {
    if (confirmTimerRef.current) {
      clearTimeout(confirmTimerRef.current)
      confirmTimerRef.current = null
    }
    if (confirmClear) {
      onClearChat()
      setConfirmClear(false)
    } else {
      setConfirmClear(true)
      confirmTimerRef.current = setTimeout(() => setConfirmClear(false), 3000)
    }
  }

  return (
    <header className="sticky top-0 z-30 h-14 bg-theme-black/70 backdrop-blur-xl">
      <div className="flex h-full items-center justify-between px-3 md:px-5">
        <div className="flex items-center gap-2.5">
          <button
            type="button"
            onClick={onToggleSidebar}
            aria-label="Open menu"
            className="rounded-xl p-2 text-neutral-300 transition-colors hover:bg-theme-gray-light active:scale-95 md:hidden"
          >
            <Menu className="size-5" />
          </button>
          <BrandMark className="size-7 md:hidden" />
          <div className="flex flex-col leading-none">
            <span className="bg-gradient-to-r from-theme-red to-theme-yellow bg-clip-text text-lg font-semibold tracking-tight text-transparent">
              AURA
            </span>
            <span className="hidden text-[10px] text-neutral-500 sm:block">
              DAU Assistant
            </span>
          </div>
        </div>

        <div className="flex items-center gap-1">
          {canInstall ? (
            <IconButton label="Install app" onClick={onInstall}>
              <Download className="size-4" />
            </IconButton>
          ) : null}
          <button
            type="button"
            onClick={handleClear}
            className={cn(
              "inline-flex items-center gap-1.5 rounded-xl px-2.5 py-1.5 text-sm transition-all active:scale-[0.98]",
              confirmClear
                ? "bg-theme-red text-black shadow-[0_0_16px_-4px_rgba(244,80,59,0.6)]"
                : "text-neutral-300 hover:bg-theme-gray-light",
            )}
          >
            <Trash2 className="size-4" />
            <span className="hidden sm:inline">
              {confirmClear ? "Confirm clear" : "Clear"}
            </span>
          </button>
          {session?.user ? (
            <button
              type="button"
              onClick={() => signOut({ callbackUrl: "/login" })}
              className="inline-flex items-center gap-1.5 rounded-xl px-2.5 py-1.5 text-sm text-neutral-300 transition-colors hover:bg-theme-gray-light"
            >
              <LogOut className="size-4" />
              <span className="hidden sm:inline">Sign out</span>
            </button>
          ) : (
            <button
              type="button"
              onClick={() => router.push("/login")}
              className="inline-flex items-center gap-1.5 rounded-xl bg-gradient-to-r from-theme-red to-theme-yellow px-3 py-1.5 text-sm font-medium text-black transition-opacity hover:opacity-90"
            >
              <LogIn className="size-4" />
              <span className="hidden sm:inline">Sign in</span>
            </button>
          )}
        </div>
      </div>
      <div className="h-px bg-gradient-to-r from-transparent via-theme-gray-light to-transparent" />
    </header>
  )
}

interface IconButtonProps {
  label: string
  onClick: () => void
  children: React.ReactNode
}

function IconButton({ label, onClick, children }: IconButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={label}
      className="rounded-xl p-2 text-neutral-300 transition-colors hover:bg-theme-gray-light"
    >
      {children}
    </button>
  )
}
