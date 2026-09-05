"use client";

import type { Artifact } from "@/lib/types";
import { ArtifactHeader } from "./ArtifactHeader";
import { MarkdownArtifact } from "./MarkdownArtifact";
import { SandboxedIframe } from "./SandboxedIframe";

interface ArtifactViewerProps {
  artifact: Artifact | null;
  onClose: () => void;
}

export function ArtifactViewer({
  artifact,
  onClose,
}: ArtifactViewerProps) {
  if (!artifact) return null;

  return (
    <div className="fixed inset-0 z-30 flex h-full w-full flex-col border-l border-line bg-panel md:static md:z-auto md:w-[45%] lg:w-[50%]">
      <ArtifactHeader
        title={artifact.title}
        artifactType={artifact.artifact_type}
        onClose={onClose}
      />

      <div className="flex-1 overflow-y-auto">
        {artifact.artifact_type === "html" ? (
          <SandboxedIframe html={artifact.content} />
        ) : (
          <MarkdownArtifact content={artifact.content} />
        )}
      </div>
    </div>
  );
}