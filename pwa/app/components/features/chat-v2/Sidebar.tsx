"use client";

import { motion, AnimatePresence } from "framer-motion";
import { Plus, MessageSquare, Trash2, X, User } from "lucide-react";
import { cn } from "@/lib/utils";
import { ChatThread, UserSession } from "@/hooks/use-aura-chat";

interface SidebarProps {
  threads: ChatThread[];
  activeThreadId: string | null;
  onSelectThread: (id: string) => void;
  onDeleteThread: (id: string) => void;
  onNewChat: () => void;
  userSession: UserSession | null;
  onOpenProfile: () => void;
  mobileOpen: boolean;
  onCloseMobile: () => void;
}

function SidebarBody({
  threads,
  activeThreadId,
  onSelectThread,
  onDeleteThread,
  onNewChat,
  userSession,
  onOpenProfile,
}: Omit<SidebarProps, "mobileOpen" | "onCloseMobile">) {
  return (
    <div className="flex h-full flex-col bg-theme-gray">
      <div className="p-3">
        <button
          type="button"
          onClick={onNewChat}
          className="inline-flex w-full items-center justify-center gap-2 rounded-full bg-gradient-to-r from-theme-red to-theme-yellow px-4 py-2.5 text-sm font-semibold text-black transition-all hover:from-theme-red/90 hover:to-theme-yellow/90"
        >
          <Plus className="h-4 w-4" strokeWidth={2.5} />
          New chat
        </button>
      </div>

      <div className="chat-v2-scroll flex-1 overflow-y-auto px-2 pb-2">
        {threads.length === 0 ? (
          <div className="px-3 py-4 text-xs text-muted-foreground">
            No chats yet. Start a new conversation.
          </div>
        ) : (
          <ul className="space-y-0.5">
            {threads.map((t) => {
              const active = t.id === activeThreadId;
              return (
                <li key={t.id} className="group">
                  <div
                    className={cn(
                      "flex w-full items-center gap-2 rounded-lg p-2 text-sm transition-colors",
                      active
                        ? "bg-theme-gray-light text-foreground"
                        : "text-muted-foreground hover:bg-theme-gray-light hover:text-foreground",
                    )}
                  >
                    <button
                      type="button"
                      onClick={() => onSelectThread(t.id)}
                      className="flex min-w-0 flex-1 items-center gap-2 text-left"
                    >
                      <MessageSquare className="h-3.5 w-3.5 shrink-0" />
                      <span className="flex-1 truncate">{t.title}</span>
                    </button>
                    {active ? (
                      <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-theme-red" />
                    ) : (
                      <button
                        type="button"
                        aria-label="Delete chat"
                        onClick={(e) => {
                          e.stopPropagation();
                          onDeleteThread(t.id);
                        }}
                        className="hidden h-5 w-5 place-items-center rounded text-muted-foreground transition-colors hover:bg-theme-gray-lighter hover:text-theme-red group-hover:grid"
                      >
                        <Trash2 className="h-3 w-3" />
                      </button>
                    )}
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </div>

      <div className="border-t border-theme-gray-light p-3">
        <button
          type="button"
          onClick={onOpenProfile}
          className="flex w-full items-center gap-3 rounded-lg p-2 text-left transition-colors hover:bg-theme-gray-light"
        >
          <div className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-gradient-to-br from-theme-red to-theme-yellow text-black">
            <User className="h-4 w-4" strokeWidth={2.5} />
          </div>
          <div className="min-w-0 flex-1">
            <div className="truncate text-sm font-medium text-foreground">
              {userSession?.name || "Guest Account"}
            </div>
            <div className="truncate text-xs text-muted-foreground">
              {userSession ? userSession.email : "Sign in to get started"}
            </div>
          </div>
        </button>
      </div>

    </div>
  );
}

export default function Sidebar(props: SidebarProps) {
  return (
    <>
      <aside className="hidden h-full w-72 shrink-0 border-r border-theme-gray-light md:block">
        <SidebarBody {...props} />
      </aside>

      <AnimatePresence>
        {props.mobileOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.15 }}
              onClick={props.onCloseMobile}
              className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm md:hidden"
            />
            <motion.div
              initial={{ x: "-100%" }}
              animate={{ x: 0 }}
              exit={{ x: "-100%" }}
              transition={{ type: "spring", stiffness: 320, damping: 32 }}
              className="fixed inset-y-0 left-0 z-50 flex w-72 max-w-[85vw] flex-col border-r border-theme-gray-light bg-theme-gray md:hidden"
            >
              <div className="flex items-center justify-between p-3">
                <span className="text-sm font-semibold text-foreground">Chats</span>
                <button
                  type="button"
                  onClick={props.onCloseMobile}
                  aria-label="Close sidebar"
                  className="grid h-8 w-8 place-items-center rounded-full text-muted-foreground hover:bg-theme-gray-light hover:text-foreground"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
              <div className="flex-1 overflow-hidden">
                <SidebarBody {...props} />
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
