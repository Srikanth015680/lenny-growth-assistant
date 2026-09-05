"use client";

import { useState } from "react";
import { ChevronDown } from "lucide-react";

import type { SourceCitation as SourceCitationType } from "@/lib/types";

export function SourceCitation({
  source,
}: {
  source: SourceCitationType;
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="rounded-md border border-clay/30 bg-clay-soft text-sm">
      <button
        type="button"
        onClick={() => setExpanded((prev) => !prev)}
        className="flex w-full items-center justify-between gap-2 px-3 py-2 text-left"
      >
        <span className="font-medium text-clay">
          {source.episode}
          {source.guest ? ` — ${source.guest}` : ""}
          {source.timestamp ? ` (${source.timestamp})` : ""}
        </span>

        <ChevronDown
          size={14}
          className={`flex-shrink-0 text-clay transition-transform ${
            expanded ? "rotate-180" : ""
          }`}
        />
      </button>

      {expanded && (
        <p className="border-t border-clay/20 px-3 py-2 text-ink/80">
          {source.text}
        </p>
      )}
    </div>
  );
}