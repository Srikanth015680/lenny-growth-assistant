"use client";

import { useEffect, useRef } from "react";
import { MessageSquareText } from "lucide-react";

import type { Message } from "@/lib/types";
import { MessageItem } from "./MessageItem";

interface MessageListProps {
  messages: Message[];
  streamingMessageId?: string | null;
  onOpenArtifact?: (artifactId: string) => void;
}

export function MessageList({
  messages,
  streamingMessageId,
  onOpenArtifact,
}: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-3 px-6 text-center text-ink/60">
        <MessageSquareText size={28} className="text-moss" />
        <p className="max-w-sm text-sm">
          Ask about activation, pricing, growth loops, or anything else covered
          in Lenny&apos;s Podcast archive. Every answer cites the episode it
          came from.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4 px-4 py-4">
      {messages.map((message) => (
        <MessageItem
          key={message.id}
          message={message}
          isStreaming={message.id === streamingMessageId}
          onOpenArtifact={onOpenArtifact}
        />
      ))}
      <div ref={bottomRef} />
    </div>
  );
}