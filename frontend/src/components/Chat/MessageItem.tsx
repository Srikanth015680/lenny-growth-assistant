"use client";

import type { Message } from "@/lib/types";
import { SourceCitation } from "./SourceCitation";
import { FileText, Code2 } from "lucide-react";

interface MessageItemProps {
  message: Message;
  isStreaming?: boolean;
  onOpenArtifact?: (artifactId: string) => void;
}

export function MessageItem({ message, isStreaming, onOpenArtifact }: MessageItemProps) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div className={`max-w-[80ch] ${isUser ? "" : "w-full"}`}>
        <div
          className={
            isUser
              ? "rounded-lg bg-moss px-4 py-2.5 text-white"
              : "rounded-lg bg-panel px-4 py-2.5 text-ink"
          }
        >
          <p className="whitespace-pre-wrap text-sm leading-relaxed">
            {message.content}
            {isStreaming && <span className="streaming-cursor">▍</span>}
          </p>
        </div>

        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="mt-2 space-y-1.5">
            {message.sources.map((source, i) => (
              <SourceCitation key={i} source={source} />
            ))}
          </div>
        )}

        {!isUser && message.artifacts.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-2">
            {message.artifacts.map((artifact) => (
              <button
                key={artifact.id}
                onClick={() => onOpenArtifact?.(artifact.id)}
                className="flex items-center gap-1.5 rounded-md border border-line bg-panel px-3 py-1.5 text-sm text-ink hover:border-moss"
              >
                {artifact.artifact_type === "html" ? (
                  <Code2 size={14} className="text-moss" />
                ) : (
                  <FileText size={14} className="text-moss" />
                )}
                {artifact.title}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
