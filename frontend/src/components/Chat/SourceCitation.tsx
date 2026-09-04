"use client";

import { useState } from "react";
import { ChevronDown } from "lucide-react";
import type { SourceCitation as SourceCitationType } from "@/lib/types";

/**
 * Sources render as visibly distinct clay-toned cards — deliberately not
 * the same treatment as the assistant's own words, so "this is transcript
 * evidence, not the model talking" is legible at a glance, not just in the
 * data (section 10).
 */
export function SourceCitation({ source }: { source: SourceCitationType }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="rounded-md border border-clay/30 bg-clay-soft text-sm">
      <button
        type="button"
        onClick={() => setExpanded((e) => !e)}
        className="flex w-full items-center justify-between gap-2 px-3 py-2 text-left"
      >
        <span className="font-medium text-clay">
          {source.episode}
          {source.guest ? ` — ${source.guest}` : ""}
          {source.timestamp ? ` (${source.timestamp})` : ""}
        </span>
        <ChevronDown
          size={14}
          className={`flex-shrink-0 text-clay transition-transform ${expanded ? "rotate-180" : ""}`}
        />
      </button>
      {expanded && (
        <p className="border-t border-clay/20 px-3 py-2 text-ink/80">{source.text}</p>
      )}
    </div>
  );
}
