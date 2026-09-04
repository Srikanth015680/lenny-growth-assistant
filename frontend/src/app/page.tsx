"use client";

import { useCallback, useEffect, useState } from "react";
import { Menu, X } from "lucide-react";
import { SessionSelector } from "@/components/Chat/SessionSelector";
import { ProviderSelector } from "@/components/Chat/ProviderSelector";
import { ChatPane } from "@/components/Chat/ChatPane";
import { ArtifactViewer } from "@/components/Artifact/ArtifactViewer";
import { useSessions } from "@/hooks/useSessions";
import { useChatStream } from "@/hooks/useChatStream";
import { useArtifacts } from "@/hooks/useArtifacts";
import { fetchHealth } from "@/lib/api";
import type { Health, LLMProvider } from "@/lib/types";

const HEALTH_POLL_MS = 30_000;

export default function Home() {
  const {
    sessions,
    activeSession,
    setActiveSession,
    loadingSessions,
    loadingDetail,
    selectSession,
    startNewChat,
  } = useSessions();

  const [provider, setProvider] = useState<LLMProvider>("ollama");
  const [health, setHealth] = useState<Health | null>(null);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  const { activeArtifact, openArtifact, closeArtifact, openArtifactById } = useArtifacts();

  const { sendMessage, sending, statusMessage, streamingMessageId, error, clearError } =
    useChatStream({
      session: activeSession,
      setSession: setActiveSession,
      provider,
      onArtifact: openArtifact,
    });

  useEffect(() => {
    const poll = () => fetchHealth().then(setHealth).catch(() => setHealth(null));
    poll();
    const interval = setInterval(poll, HEALTH_POLL_MS);
    return () => clearInterval(interval);
  }, []);

  const handleNewChat = useCallback(async () => {
    closeArtifact();
    await startNewChat();
    setMobileNavOpen(false);
  }, [startNewChat, closeArtifact]);

  const handleSelectSession = useCallback(
    async (sessionId: string) => {
      closeArtifact();
      await selectSession(sessionId);
      setMobileNavOpen(false);
    },
    [selectSession, closeArtifact]
  );

  return (
    <div className="flex h-screen flex-col bg-paper">
      <header className="flex flex-shrink-0 items-center justify-between border-b border-line bg-panel px-4 py-2.5">
        <div className="flex items-center gap-3">
          <button
            className="rounded-md p-1.5 text-ink/70 hover:bg-paper md:hidden"
            onClick={() => setMobileNavOpen((open) => !open)}
            aria-label="Toggle conversation list"
          >
            {mobileNavOpen ? <X size={18} /> : <Menu size={18} />}
          </button>
          <h1 className="text-sm font-semibold text-ink">The Lenny Growth Assistant</h1>
        </div>
        <ProviderSelector provider={provider} onChange={setProvider} health={health} />
      </header>

      <div className="relative flex flex-1 overflow-hidden">
        <div
          className={`${mobileNavOpen ? "fixed inset-0 z-40 flex" : "hidden"} md:static md:z-auto md:flex`}
        >
          <SessionSelector
            sessions={sessions}
            activeSessionId={activeSession?.id ?? null}
            onSelect={handleSelectSession}
            onNewChat={handleNewChat}
            loading={loadingSessions}
          />
        </div>

        <ChatPane
          session={activeSession}
          loadingDetail={loadingDetail}
          sending={sending}
          statusMessage={statusMessage}
          streamingMessageId={streamingMessageId}
          error={error}
          onDismissError={clearError}
          onSend={sendMessage}
          onOpenArtifact={(artifactId) => openArtifactById(activeSession, artifactId)}
        />

        <ArtifactViewer artifact={activeArtifact} onClose={closeArtifact} />
      </div>
    </div>
  );
}
