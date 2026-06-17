"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Download, LogIn, LogOut, Menu, Trash2 } from "lucide-react"
import { cn } from "@/lib/utils"
import type { UserSession } from "@/lib/chat-types"
import { BrandMark } from "@/components/common/BrandMark"

interface HeaderProps {
  onToggleSidebar: () => void
  onClearChat: () => void
  canInstall: boolean
  onInstall: () => void
  userSession: UserSession | null
  onLogout: () => void
}

export function Header({
  onToggleSidebar,
  onClearChat,
  canInstall,
  onInstall,
  userSession,
  onLogout,
}: HeaderProps) {
  const router = useRouter()
  const [confirmClear, setConfirmClear] = useState(false)

  const handleClear = () => {
    if (confirmClear) {
      onClearChat()
      setConfirmClear(false)
    } else {
      setConfirmClear(true)
      setTimeout(() => setConfirmClear(false), 3000)
    }
  }

  return (
    <header className="sticky top-0 z-30 h-14 border-b border-transparent bg-theme-black/60 backdrop-blur">
      <div className="flex h-full items-center justify-between px-3 md:px-5">
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={onToggleSidebar}
            aria-label="Open menu"
            className="rounded-lg p-2 text-neutral-300 transition-colors hover:bg-theme-gray-light md:hidden"
          >
            <Menu className="size-5" />
          </button>
          <BrandMark className="size-7 text-xs md:hidden" />
          <span className="bg-gradient-to-r from-theme-red to-theme-yellow bg-clip-text text-lg font-semibold text-transparent">
            AURA
          </span>
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
              "inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-sm transition-colors",
              confirmClear
                ? "bg-theme-red text-black"
                : "text-neutral-300 hover:bg-theme-gray-light",
            )}
          >
            <Trash2 className="size-4" />
            <span className="hidden sm:inline">
              {confirmClear ? "Confirm clear" : "Clear"}
            </span>
          </button>
          {userSession ? (
            <button
              type="button"
              onClick={onLogout}
              className="inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-sm text-neutral-300 transition-colors hover:bg-theme-gray-light"
            >
              <LogOut className="size-4" />
              <span className="hidden sm:inline">Sign out</span>
            </button>
          ) : (
            <button
              type="button"
              onClick={() => router.push("/login")}
              className="inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-sm text-neutral-300 transition-colors hover:bg-theme-gray-light"
            >
              <LogIn className="size-4" />
              <span className="hidden sm:inline">Sign in</span>
            </button>
          )}
        </div>
      </div>
      <div className="h-px bg-gradient-to-r from-theme-red/40 via-theme-yellow/30 to-transparent" />
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
      className="rounded-lg p-2 text-neutral-300 transition-colors hover:bg-theme-gray-light"
    >
      {children}
    </button>
  )
}
