"use client";

import type { Health, LLMProvider } from "@/lib/types";

interface ProviderSelectorProps {
  provider: LLMProvider;
  onChange: (provider: LLMProvider) => void;
  health: Health | null;
}

function statusColor(status?: string): string {
  if (status === "ok") return "bg-moss";
  if (status === "not_configured") return "bg-ink/20";
  return "bg-danger";
}

/**
 * Shows the currently selected provider's health as a colored dot right on
 * the selector — "obvious model state" (section 22) without a separate
 * status panel to go check.
 */
export function ProviderSelector({ provider, onChange, health }: ProviderSelectorProps) {
  const dot = statusColor(health?.[provider]?.status);
  const detail = health?.[provider]?.detail;

  return (
    <div className="flex items-center gap-2">
      <span className={`h-2 w-2 rounded-full ${dot}`} title={detail ?? undefined} />
      <select
        value={provider}
        onChange={(e) => onChange(e.target.value as LLMProvider)}
        className="rounded-md border border-line bg-panel px-2 py-1 text-sm text-ink"
      >
        <option value="ollama">Ollama (local)</option>
        <option value="anthropic">Anthropic</option>
      </select>
    </div>
  );
}
