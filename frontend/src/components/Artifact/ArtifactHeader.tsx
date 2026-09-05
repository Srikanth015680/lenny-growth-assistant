"use client";

import { Code2, FileText, X } from "lucide-react";
import type { ArtifactType } from "@/lib/types";

import { Badge } from "../UI/Badge";

interface ArtifactHeaderProps {
  title: string;
  artifactType: ArtifactType;
  onClose: () => void;
}

export function ArtifactHeader({
  title,
  artifactType,
  onClose,
}: ArtifactHeaderProps) {
  return (
    <div className="flex items-center justify-between border-b border-line bg-panel px-4 py-3">
      <div className="flex items-center gap-2 overflow-hidden">
        {artifactType === "html" ? (
          <Code2 size={16} className="flex-shrink-0 text-moss" />
        ) : (
          <FileText size={16} className="flex-shrink-0 text-moss" />
        )}

        <span className="truncate text-sm font-medium text-ink">
          {title}
        </span>

        <Badge tone="neutral">{artifactType}</Badge>
      </div>

      <button
        onClick={onClose}
        aria-label="Close artifact"
        className="rounded-md p-1 text-ink/60 hover:bg-paper hover:text-ink"
      >
        <X size={16} />
      </button>
    </div>
  );
}