
# 08 — Frontend

## Goal

Build a responsive interface for The Lenny Growth Assistant with streaming
chat, conversation management, source citations, provider selection, and an
in-app artifact viewer.

## Frontend Stack

The frontend uses:

* Next.js 16
* React 19
* TypeScript
* Tailwind CSS
* React Markdown
* Playwright for browser-level testing

The application uses strict TypeScript settings so that API contracts and
component props are checked during development and production builds.

## Design

The visual direction was defined in `docs/design.md` before implementing the
main components.

The interface uses a quiet paper-and-ink visual style with a small number of
meaningful accents.

Assistant responses and transcript citations use visually different
treatments so users can quickly distinguish generated explanations from
source evidence.

A system font stack is used to avoid an external font dependency.

## Implementation

The frontend was built in layers:

1. Shared API types
2. API client
3. UI primitives
4. Chat components
5. Source citation components
6. Artifact components
7. Session and streaming hooks
8. Main application page

The main interface supports:

* creating a new conversation
* switching between sessions
* streaming assistant responses
* displaying transcript sources
* selecting the LLM provider
* generating Ship 30 for 30 essays
* generating artifacts
* viewing Markdown artifacts
* viewing HTML artifacts
* loading states
* error states
* responsive layouts

## Streaming

Chat responses are streamed from FastAPI using Server-Sent Events.

The frontend uses `fetch()` for the chat request because the request needs to
send the session, message, provider, and mode in the POST body.

The client parses the SSE stream and handles structured events including:

* status
* sources
* token
* artifact
* error
* done

## Artifact Viewer

The artifact viewer is displayed alongside the conversation on larger
screens.

On smaller screens it becomes a collapsible section so the chat remains the
primary interaction.

Markdown artifacts are rendered using `react-markdown` with GitHub-flavored
Markdown support.

HTML artifacts are rendered inside a restricted sandboxed iframe.

## Security

Generated HTML is treated as untrusted content.

The HTML viewer uses:

`sandbox="allow-scripts"`

and does not grant `allow-same-origin`.

The Markdown renderer does not enable arbitrary raw HTML rendering.

The security model is documented separately in the architecture and design
documentation.

## Accessibility

The interface includes:

* keyboard-accessible controls
* visible focus states
* semantic buttons
* accessible labels
* appropriate loading states
* readable contrast
* responsive layouts
* reduced reliance on color alone to communicate state

## Testing

Frontend validation includes:

* TypeScript checking
* production builds
* component-level tests where appropriate
* browser-level testing with Playwright for important user flows

Important browser flows include:

1. Creating a session.
2. Sending a message.
3. Receiving a streamed response.
4. Viewing sources.
5. Generating an artifact.
6. Opening the artifact viewer.
7. Switching between sessions.
8. Handling backend/provider failures.

## Result

The frontend provides a complete interface for the assistant while keeping
the underlying AI, retrieval, and infrastructure details hidden from the
user.
