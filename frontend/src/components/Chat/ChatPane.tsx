"use client";

import type {
  ArtifactType,
  ChatMode,
  LLMProvider,
  SessionDetail,
} from "@/lib/types";

import { MessageList } from "./MessageList";
import { ChatInput } from "./ChatInput";
import { ErrorState } from "../UI/ErrorState";
import { Spinner } from "../UI/Spinner";

interface ChatPaneProps {
  session: SessionDetail | null;
  loadingDetail: boolean;
  sending: boolean;
  statusMessage: string | null;
  streamingMessageId: string | null;
  error: string | null;
  onDismissError: () => void;
  onSend: (
    message: string,
    mode: ChatMode,
    artifactType: ArtifactType
  ) => void;
  onOpenArtifact: (artifactId: string) => void;
}

export function ChatPane({
  session,
  loadingDetail,
  sending,
  statusMessage,
  streamingMessageId,
  error,
  onDismissError,
  onSend,
  onOpenArtifact,
}: ChatPaneProps) {
  if (!session) {
    return (
      <div className="flex flex-1 items-center justify-center text-sm text-ink/50">
        Start a new chat to begin.
      </div>
    );
  }

  return (
    <div className="flex h-full flex-1 flex-col overflow-hidden">
      <div className="flex-1 overflow-y-auto">
        {loadingDetail ? (
          <div className="flex h-full items-center justify-center">
            <Spinner className="text-moss" />
          </div>
        ) : (
          <MessageList
            messages={session.messages}
            streamingMessageId={streamingMessageId}
            onOpenArtifact={onOpenArtifact}
          />
        )}
      </div>

      {(statusMessage || error) && (
        <div className="px-4 pb-2">
          {statusMessage && !error && (
            <p className="flex items-center gap-2 text-xs text-ink/50">
              <Spinner className="text-moss" />
              {statusMessage}
            </p>
          )}

          {error && (
            <ErrorState
              message={error}
              onRetry={onDismissError}
            />
          )}
        </div>
      )}

      <ChatInput disabled={sending} onSend={onSend} />
    </div>
  );
}