"use client";

import Link from "next/link";
import { Menu, LogOut, Trash2, Download } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import BrandMark from "./BrandMark";
import { ThemeToggle } from "@/app/components/ThemeToggle";
import { UserSession } from "@/hooks/use-aura-chat";
import { cn } from "@/lib/utils";

interface BeforeInstallPromptEvent extends Event {
  readonly platforms: string[];
  readonly userChoice: Promise<{
    outcome: "accepted" | "dismissed";
    platform: string;
  }>;
  prompt(): Promise<void>;
}

interface HeaderProps {
  onOpenMobileSidebar: () => void;
  userSession: UserSession | null;
  onLogout: () => void;
  onClearChat: () => void;
  canClearChat: boolean;
}

export default function Header({
  onOpenMobileSidebar,
  userSession,
  onLogout,
  onClearChat,
  canClearChat,
}: HeaderProps) {
  const [confirmClear, setConfirmClear] = useState(false);
  const confirmTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [installPrompt, setInstallPrompt] =
    useState<BeforeInstallPromptEvent | null>(null);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const handleBeforeInstallPrompt = (e: Event) => {
      e.preventDefault();
      setInstallPrompt(e as BeforeInstallPromptEvent);
    };
    window.addEventListener("beforeinstallprompt", handleBeforeInstallPrompt);
    return () => {
      window.removeEventListener(
        "beforeinstallprompt",
        handleBeforeInstallPrompt,
      );
    };
  }, []);

  useEffect(() => {
    return () => {
      if (confirmTimeoutRef.current) clearTimeout(confirmTimeoutRef.current);
    };
  }, []);

  const handleClearClick = () => {
    if (!canClearChat) return;
    if (confirmClear) {
      if (confirmTimeoutRef.current) clearTimeout(confirmTimeoutRef.current);
      setConfirmClear(false);
      onClearChat();
    } else {
      setConfirmClear(true);
      confirmTimeoutRef.current = setTimeout(() => setConfirmClear(false), 3000);
    }
  };

  const handleInstallClick = async () => {
    if (!installPrompt) return;
    try {
      await installPrompt.prompt();
      await installPrompt.userChoice;
    } finally {
      setInstallPrompt(null);
    }
  };

  return (
    <>
      <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-theme-gray-light bg-theme-black/80 px-3 backdrop-blur supports-[backdrop-filter]:bg-theme-black/60 sm:px-4">
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={onOpenMobileSidebar}
            aria-label="Open sidebar"
            className="grid h-9 w-9 place-items-center rounded-full text-muted-foreground transition-colors hover:bg-theme-gray-light hover:text-foreground md:hidden"
          >
            <Menu className="h-5 w-5" />
          </button>
          <BrandMark size="md" />
          <span className="text-base font-bold tracking-tight text-foreground">AURA</span>
        </div>

        <div className="flex items-center gap-1">
          {installPrompt && (
            <button
              type="button"
              onClick={handleInstallClick}
              className="inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-sm text-muted-foreground transition-colors hover:bg-theme-gray-light hover:text-foreground"
              title="Install AURA app"
            >
              <Download className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">Install app</span>
            </button>
          )}
          <ThemeToggle />
          {canClearChat && (
            <button
              type="button"
              onClick={handleClearClick}
              title="Clear conversation"
              className={cn(
                "inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-sm transition-colors",
                confirmClear
                  ? "bg-theme-red/10 text-theme-red"
                  : "text-muted-foreground hover:bg-theme-gray-light hover:text-foreground",
              )}
            >
              <Trash2 className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">
                {confirmClear ? "Really clear?" : "Clear"}
              </span>
            </button>
          )}
          {userSession ? (
            <button
              type="button"
              onClick={onLogout}
              className="group relative inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
            >
              <LogOut className="h-3.5 w-3.5" />
              <span>Sign out</span>
              <span className="absolute -bottom-0.5 left-3 right-3 h-px w-0 bg-gradient-to-r from-theme-red to-theme-yellow transition-all group-hover:w-[calc(100%-1.5rem)]" />
            </button>
          ) : (
            <Link
              href="/login"
              className="group relative inline-flex items-center rounded-full px-3 py-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
            >
              Sign in
              <span className="absolute -bottom-0.5 left-3 right-3 h-px w-0 bg-gradient-to-r from-theme-red to-theme-yellow transition-all group-hover:w-[calc(100%-1.5rem)]" />
            </Link>
          )}
        </div>
      </header>
      <div className="h-px w-full bg-gradient-to-r from-transparent via-theme-red to-transparent opacity-50" />
    </>
  );
}
