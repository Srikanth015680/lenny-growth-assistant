import type {
  ApiError,
  ChatMode,
  ChatStreamEvent,
  Health,
  LLMProvider,
  Session,
  SessionDetail,
} from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiRequestError extends Error {
  code: string;
  status: number;

  constructor(status: number, body: ApiError) {
    super(body.error.message);
    this.code = body.error.code;
    this.status = status;
  }
}

async function parseJsonOrThrow<T>(resp: Response): Promise<T> {
  const body = await resp.json();
  if (!resp.ok) {
    throw new ApiRequestError(resp.status, body as ApiError);
  }
  return body as T;
}

export async function fetchHealth(): Promise<Health> {
  const resp = await fetch(`${API_URL}/api/health`, { cache: "no-store" });
  return parseJsonOrThrow<Health>(resp);
}

export async function createSession(title?: string): Promise<Session> {
  const resp = await fetch(`${API_URL}/api/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });
  return parseJsonOrThrow<Session>(resp);
}

export async function listSessions(): Promise<Session[]> {
  const resp = await fetch(`${API_URL}/api/sessions`, { cache: "no-store" });
  return parseJsonOrThrow<Session[]>(resp);
}

export async function getSession(sessionId: string): Promise<SessionDetail> {
  const resp = await fetch(`${API_URL}/api/sessions/${sessionId}`, { cache: "no-store" });
  return parseJsonOrThrow<SessionDetail>(resp);
}

export interface StreamChatParams {
  sessionId: string;
  message: string;
  mode: ChatMode;
  provider?: LLMProvider;
  artifactType?: "markdown" | "html";
  signal?: AbortSignal;
}

/**
 * POST /api/chat and parse the SSE response body as it arrives.
 *
 * We can't use EventSource here — it only supports GET — so this parses
 * the `text/event-stream` wire format by hand from a fetch() ReadableStream.
 * Events are delimited by a blank line; each block has an `event:` line and
 * a `data:` line, matching exactly what backend/app/api/chat.py writes.
 */
export async function streamChat(
  params: StreamChatParams,
  onEvent: (event: ChatStreamEvent) => void
): Promise<void> {
  const resp = await fetch(`${API_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    signal: params.signal,
    body: JSON.stringify({
      session_id: params.sessionId,
      message: params.message,
      mode: params.mode,
      provider: params.provider,
      artifact_type: params.artifactType ?? "markdown",
    }),
  });

  if (!resp.ok) {
    // Chat validation errors (empty message, unknown session, etc.) come
    // back as a normal JSON error response, not SSE — see chat.py.
    const body = (await resp.json()) as ApiError;
    throw new ApiRequestError(resp.status, body);
  }

  if (!resp.body) {
    throw new Error("Response body is not readable in this environment.");
  }

  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let boundary = buffer.indexOf("\n\n");
    while (boundary !== -1) {
      const block = buffer.slice(0, boundary);
      buffer = buffer.slice(boundary + 2);

      const eventLine = block.split("\n").find((l) => l.startsWith("event:"));
      const dataLine = block.split("\n").find((l) => l.startsWith("data:"));
      if (eventLine && dataLine) {
        const event = eventLine.slice("event:".length).trim();
        const data = JSON.parse(dataLine.slice("data:".length).trim());
        onEvent({ event, data } as ChatStreamEvent);
      }
      boundary = buffer.indexOf("\n\n");
    }
  }
}
