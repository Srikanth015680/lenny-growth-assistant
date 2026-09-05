"use client";

import { KeyboardEvent, useState } from "react";
import { Send } from "lucide-react";

import type { ArtifactType, ChatMode } from "@/lib/types";
import { Button } from "../UI/Button";

interface ChatInputProps {
  disabled?: boolean;
  onSend: (
    message: string,
    mode: ChatMode,
    artifactType: ArtifactType
  ) => void;
}

const MODE_OPTIONS: { value: ChatMode; label: string }[] = [
  { value: "default", label: "Ask" },
  { value: "ship30", label: "Ship 30 essay" },
  { value: "artifact", label: "Artifact" },
];

export function ChatInput({ disabled, onSend }: ChatInputProps) {
  const [text, setText] = useState("");
  const [mode, setMode] = useState<ChatMode>("default");
  const [artifactType, setArtifactType] =
    useState<ArtifactType>("markdown");

  const handleSend = () => {
    const trimmed = text.trim();

    if (!trimmed || disabled) return;

    onSend(trimmed, mode, artifactType);
    setText("");
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="border-t border-line bg-panel px-4 py-3">
      <div className="mb-2 flex items-center gap-1.5">
        {MODE_OPTIONS.map((option) => (
          <button
            key={option.value}
            type="button"
            onClick={() => setMode(option.value)}
            className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
              mode === option.value
                ? "bg-moss text-white"
                : "bg-paper text-ink/70 hover:bg-moss-soft"
            }`}
          >
            {option.label}
          </button>
        ))}

        {mode === "artifact" && (
          <select
            value={artifactType}
            onChange={(e) =>
              setArtifactType(e.target.value as ArtifactType)
            }
            className="rounded-full border border-line bg-paper px-2.5 py-1 text-xs text-ink/70"
          >
            <option value="markdown">Markdown</option>
            <option value="html">HTML</option>
          </select>
        )}
      </div>

      <div className="flex items-end gap-2">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          rows={2}
          placeholder={
            mode === "ship30"
              ? "What should the essay be about?"
              : mode === "artifact"
                ? "What should the artifact cover?"
                : "Ask a question about growth or product..."
          }
          className="flex-1 resize-none rounded-md border border-line bg-paper px-3 py-2 text-sm text-ink placeholder:text-ink/40 focus:border-moss focus:outline-none disabled:opacity-60"
        />

        <Button
          onClick={handleSend}
          disabled={disabled || !text.trim()}
          aria-label="Send message"
        >
          <Send size={16} />
        </Button>
      </div>
    </div>
  );
}