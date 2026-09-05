"use client";

import { Plus, MessageSquare } from "lucide-react";

import type { Session } from "@/lib/types";

interface SessionSelectorProps {
  sessions: Session[];
  activeSessionId: string | null;
  onSelect: (sessionId: string) => void;
  onNewChat: () => void;
  loading?: boolean;
}

export function SessionSelector({
  sessions,
  activeSessionId,
  onSelect,
  onNewChat,
  loading,
}: SessionSelectorProps) {
  return (
    <div className="flex h-full w-56 flex-shrink-0 flex-col border-r border-line bg-paper">
      <div className="p-3">
        <button
          onClick={onNewChat}
          className="flex w-full items-center gap-2 rounded-md border border-line bg-panel px-3 py-2 text-sm font-medium text-ink hover:border-moss"
        >
          <Plus size={15} />
          New chat
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-2 pb-3">
        {loading && (
          <p className="px-2 py-1 text-xs text-ink/50">
            Loading sessions…
          </p>
        )}

        {!loading && sessions.length === 0 && (
          <p className="px-2 py-1 text-xs text-ink/50">
            No conversations yet.
          </p>
        )}

        {sessions.map((session) => (
          <button
            key={session.id}
            onClick={() => onSelect(session.id)}
            className={`mb-1 flex w-full items-start gap-2 rounded-md px-2.5 py-2 text-left text-sm transition-colors ${
              session.id === activeSessionId
                ? "bg-moss-soft text-moss-deep"
                : "text-ink/80 hover:bg-panel"
            }`}
          >
            <MessageSquare
              size={14}
              className="mt-0.5 flex-shrink-0"
            />
            <span className="truncate">{session.title}</span>
          </button>
        ))}
      </div>
    </div>
  );
}