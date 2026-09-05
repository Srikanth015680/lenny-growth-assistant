"use client";

import { useCallback, useState } from "react";
import { ApiRequestError, streamChat } from "@/lib/api";
import type {
  Artifact,
  ArtifactType,
  ChatMode,
  LLMProvider,
  Message,
  SessionDetail,
} from "@/lib/types";

interface UseChatStreamArgs {
  session: SessionDetail | null;
  setSession: (
    updater: (prev: SessionDetail | null) => SessionDetail | null
  ) => void;
  provider: LLMProvider;
  onArtifact?: (artifact: Artifact) => void;
}

function tempId() {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }

  return `temp-${Date.now()}-${Math.random()}`;
}

export function useChatStream({
  session,
  setSession,
  provider,
  onArtifact,
}: UseChatStreamArgs) {
  const [sending, setSending] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [streamingMessageId, setStreamingMessageId] = useState<string | null>(
    null
  );
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
        prev
          ? {
              ...prev,
              messages: [...prev.messages, userMessage, assistantMessage],
            }
          : prev
      );

      setStreamingMessageId(assistantId);

      const updateAssistant = (update: (message: Message) => Message) => {
        setSession((prev) => {
          if (!prev) return prev;

          return {
            ...prev,
            messages: prev.messages.map((message) =>
              message.id === assistantId ? update(message) : message
            ),
          };
        });
      };

      try {
        await streamChat(
          {
            sessionId: session.id,
            message: text,
            mode,
            provider,
            artifactType,
          },
          (event) => {
            switch (event.event) {
              case "status":
                setStatusMessage(event.data.message);
                break;

              case "sources":
                updateAssistant((message) => ({
                  ...message,
                  sources: event.data.sources,
                }));
                break;

              case "token":
                updateAssistant((message) => ({
                  ...message,
                  content: message.content + event.data.content,
                }));
                break;

              case "artifact": {
                const artifact: Artifact = {
                  id: tempId(),
                  message_id: assistantId,
                  artifact_type: event.data.type,
                  title: event.data.title,
                  content: event.data.content,
                  created_at: new Date().toISOString(),
                };

                updateAssistant((message) => ({
                  ...message,
                  artifacts: [...message.artifacts, artifact],
                }));

                onArtifact?.(artifact);
                break;
              }

              case "error":
                setError(event.data.error.message);
                break;

              case "done":
                setStatusMessage(null);
                break;
            }
          }
        );
      } catch (err) {
        setError(
          err instanceof ApiRequestError
            ? err.message
            : "The connection to the assistant was lost."
        );
      } finally {
        setSending(false);
        setStreamingMessageId(null);
        setStatusMessage(null);
      }
    },
    [session, sending, provider, setSession, onArtifact]
  );

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    sendMessage,
    sending,
    statusMessage,
    streamingMessageId,
    error,
    clearError,
  };
}