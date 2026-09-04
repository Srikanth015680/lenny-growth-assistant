"use client";

import { useCallback, useState } from "react";
import type { Artifact, SessionDetail } from "@/lib/types";

/**
 * Tracks which artifact is currently open in the viewer pane. Deliberately
 * separate from chat state — closing the viewer shouldn't touch message
 * history, and switching sessions shouldn't leave a stale artifact open.
 */
export function useArtifacts() {
  const [activeArtifact, setActiveArtifact] = useState<Artifact | null>(null);

  const openArtifact = useCallback((artifact: Artifact) => setActiveArtifact(artifact), []);
  const closeArtifact = useCallback(() => setActiveArtifact(null), []);

  const openArtifactById = useCallback((session: SessionDetail | null, artifactId: string) => {
    if (!session) return;
    for (const message of session.messages) {
      const found = message.artifacts.find((a) => a.id === artifactId);
      if (found) {
        setActiveArtifact(found);
        return;
      }
    }
  }, []);

  return { activeArtifact, openArtifact, closeArtifact, openArtifactById };
}
