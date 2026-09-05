"use client";

import { useCallback, useState } from "react";
import type { Artifact, SessionDetail } from "@/lib/types";

export function useArtifacts() {
  const [activeArtifact, setActiveArtifact] = useState<Artifact | null>(null);

  const openArtifact = useCallback((artifact: Artifact) => {
    setActiveArtifact(artifact);
  }, []);

  const closeArtifact = useCallback(() => {
    setActiveArtifact(null);
  }, []);

  const openArtifactById = useCallback(
    (session: SessionDetail | null, artifactId: string) => {
      if (!session) return;

      for (const message of session.messages) {
        const artifact = message.artifacts.find(
          (item) => item.id === artifactId
        );

        if (artifact) {
          setActiveArtifact(artifact);
          return;
        }
      }
    },
    []
  );

  return {
    activeArtifact,
    openArtifact,
    closeArtifact,
    openArtifactById,
  };
}