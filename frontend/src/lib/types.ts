export type ChatMode = "default" | "ship30" | "artifact";

export type LLMProvider = "ollama" | "anthropic";

export type Role = "user" | "assistant" | "system";

export type ArtifactType = "markdown" | "html";

export interface SourceCitation {
  episode: string;
  guest: string | null;
  timestamp: string | null;
  text: string;
  score: number;
}

export interface Artifact {
  id: string;
  message_id: string;
  artifact_type: ArtifactType;
  title: string;
  content: string;
  created_at: string;
}

export interface Message {
  id: string;
  session_id: string;
  role: Role;
  content: string;
  sources: SourceCitation[] | null;
  created_at: string;
  artifacts: Artifact[];
}

export interface Session {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface SessionDetail extends Session {
  messages: Message[];
}

export interface HealthComponent {
  status: "ok" | "degraded" | "down" | "not_configured";
  detail: string | null;
}

export interface Health {
  status: "ok" | "degraded" | "down";
  database: HealthComponent;
  pgvector: HealthComponent;
  ollama: HealthComponent;
  anthropic: HealthComponent;
  application: HealthComponent;
}

export interface ApiError {
  error: {
    code: string;
    message: string;
  };
}

export type ChatStreamEvent =
  | { event: "status"; data: { message: string } }
  | { event: "sources"; data: { sources: SourceCitation[] } }
  | { event: "token"; data: { content: string } }
  | {
      event: "artifact";
      data: {
        type: ArtifactType;
        title: string;
        content: string;
      };
    }
  | { event: "done"; data: { message_id: string } }
  | {
      event: "error";
      data: {
        error: {
          code: string;
          message: string;
        };
      };
    };