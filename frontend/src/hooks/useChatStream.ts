"use client";

import { useCallback, useState } from "react";
import { ApiRequestError, streamChat } from "@/lib/api";
import type { Artifact, ArtifactType, ChatMode, LLMProvider, Message, SessionDetail } from "@/lib/types";

interface UseChatStreamArgs {
  session: SessionDetail | null;
  setSession: (updater: (prev: SessionDetail | null) => SessionDetail | null) => void;
  provider: LLMProvider;
  onArtifact?: (artifact: Artifact) => void;
}

function tempId(): string {
  return typeof crypto !== "undefined" && crypto.randomUUID
    ? crypto.randomUUID()
    : `temp-${Date.now()}-${Math.random()}`;
}

/**
 * Drives one /api/chat request and applies each SSE event (section 20) to
 * local state as it arrives, so the UI streams token-by-token instead of
 * waiting for the full response. Errors surface as a normal `error` SSE
 * event (see backend/app/api/chat.py) rather than an HTTP failure once the
 * stream has started — this hook treats both the same way.
 */
export function useChatStream({ session, setSession, provider, onArtifact }: UseChatStreamArgs) {
  const [sending, setSending] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [streamingMessageId, setStreamingMessageId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(
    async (text: string, mode: ChatMode, artifactType: ArtifactType) => {
      if (!session || sending) return;
      setSending(true);
      setError(null);
      setStatusMessage("Sending...");

      const userMessage: Message = {
        id: tempId(),
        session_id: session.id,
        role: "user",
        content: text,
        sources: null,
        created_at: new Date().toISOString(),
        artifacts: [],
      };
      const assistantId = tempId();
      const assistantMessage: Message = {
        id: assistantId,
        session_id: session.id,
        role: "assistant",
        content: "",
        sources: null,
        created_at: new Date().toISOString(),
        artifacts: [],
      };

      setSession((prev) =>
        prev ? { ...prev, messages: [...prev.messages, userMessage, assistantMessage] } : prev
      );
      setStreamingMessageId(assistantId);

      const applyToAssistant = (fn: (m: Message) => Message) => {
        setSession((prev) => {
          if (!prev) return prev;
          return {
            ...prev,
            messages: prev.messages.map((m) => (m.id === assistantId ? fn(m) : m)),
          };
        });
      };

      try {
        await streamChat({ sessionId: session.id, message: text, mode, provider, artifactType }, (evt) => {
          switch (evt.event) {
            case "status":
              setStatusMessage(evt.data.message);
              break;
            case "sources":
              applyToAssistant((m) => ({ ...m, sources: evt.data.sources }));
              break;
            case "token":
              applyToAssistant((m) => ({ ...m, content: m.content + evt.data.content }));
              break;
            case "artifact": {
              const artifact: Artifact = {
                id: tempId(),
                message_id: assistantId,
                artifact_type: evt.data.type,
                title: evt.data.title,
                content: evt.data.content,
                created_at: new Date().toISOString(),
              };
              applyToAssistant((m) => ({ ...m, artifacts: [...m.artifacts, artifact] }));
              onArtifact?.(artifact);
              break;
            }
            case "error":
              setError(evt.data.error.message);
              break;
            case "done":
              setStatusMessage(null);
              break;
          }
        });
      } catch (err) {
        setError(err instanceof ApiRequestError ? err.message : "The connection to the assistant was lost.");
      } finally {
        setSending(false);
        setStreamingMessageId(null);
        setStatusMessage(null);
      }
    },
    [session, sending, provider, setSession, onArtifact]
  );

  return { sendMessage, sending, statusMessage, streamingMessageId, error, clearError: () => setError(null) };
}
