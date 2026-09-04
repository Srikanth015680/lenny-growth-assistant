"use client";

import { useCallback, useEffect, useState } from "react";
import { createSession, getSession, listSessions } from "@/lib/api";
import type { Session, SessionDetail } from "@/lib/types";

export function useSessions() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSession, setActiveSession] = useState<SessionDetail | null>(null);
  const [loadingSessions, setLoadingSessions] = useState(true);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refreshSessions = useCallback(async () => {
    try {
      setLoadingSessions(true);
      setSessions(await listSessions());
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load sessions.");
    } finally {
      setLoadingSessions(false);
    }
  }, []);

  const selectSession = useCallback(async (sessionId: string) => {
    try {
      setLoadingDetail(true);
      setActiveSession(await getSession(sessionId));
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load conversation.");
    } finally {
      setLoadingDetail(false);
    }
  }, []);

  const startNewChat = useCallback(async () => {
    const session = await createSession();
    setSessions((prev) => [session, ...prev]);
    setActiveSession({ ...session, messages: [] });
    return session;
  }, []);

  useEffect(() => {
    refreshSessions();
  }, [refreshSessions]);

  return {
    sessions,
    activeSession,
    setActiveSession,
    loadingSessions,
    loadingDetail,
    error,
    refreshSessions,
    selectSession,
    startNewChat,
  };
}
