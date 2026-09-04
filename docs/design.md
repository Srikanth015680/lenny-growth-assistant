# Design — The Lenny Growth Assistant

## Visual principles

This is an internal research tool a PM has open for extended stretches —
not a marketing surface. Three principles drove every choice in
`frontend/src/`:

1. **Quiet by default, loud where it matters.** The palette (warm paper
   `#F6F4EF`, ink `#201F1C`) is close to neutral everywhere except two
   deliberate accents: moss green for the assistant/primary actions, and
   clay/amber *only* for transcript citations. That second accent exists
   specifically so sourced evidence is visually distinguishable from the
   model's own words at a glance (section 10's citation-visibility goal),
   not for decoration.
2. **System fonts, on purpose.** No webfont import — instant paint, zero
   network dependency, and this app is used all day, so shaving the font
   FOUC/flash matters more than a bespoke typeface would.
3. **No AI-tool clichés.** No identical-shadow card grid, no ALL-CAPS
   section eyebrows, no em-dash-separated labels, no arrow-suffixed
   buttons. Section headers in generated Markdown artifacts come from the
   LLM's own output, not a template imposed by the viewer.

## Information architecture

```
Session rail (collapsible)  |  Chat thread  |  Artifact viewer (collapsible)
```

Three panes, but only two are ever both visible at once on a typical
laptop width: the session rail is a slim utility, not a primary work
surface, so it collapses first (at `md` breakpoint) before the chat/
artifact split does.

## Desktop layout

- Top bar: app name, mobile nav toggle (hidden ≥`md`), provider selector
  with a live health dot (section 22 "obvious model state").
- Left: session rail, 224px fixed width, scrollable list + "New chat".
- Center: chat thread (flexes to fill remaining width), composer pinned to
  the bottom with the Ask / Ship 30 essay / Artifact mode picker.
- Right: artifact viewer, 45-50% width, only rendered (and only taking
  width) when an artifact is open — closing it hands the space straight
  back to chat (section 22 "obvious artifact state").

## Mobile layout

- Session rail becomes a full-screen overlay behind the hamburger toggle,
  not a squeezed sidebar.
- Artifact viewer becomes a full-screen overlay too (`fixed inset-0`
  below the `md` breakpoint) rather than a cramped side sliver — matches
  section 17's "mobile: collapsible/drawer" instruction; implemented here
  as a full overlay rather than a bottom sheet for time reasons, noted in
  README's known limitations.
- Composer and mode picker are unchanged — they're already narrow-friendly
  (wrapping pill buttons, full-width textarea).

## Chat interaction states

- **Empty session**: a centered prompt suggesting example topics, not a
  blank white pane (`MessageList.tsx`'s empty state).
- **Streaming**: assistant bubble grows token-by-token with a blinking
  text cursor (`streaming-cursor` in `globals.css`), status line above the
  composer ("Searching transcripts" → "Generating response").
- **Sources**: rendered as expandable clay-toned cards under the assistant
  message, collapsed by default so a dense answer doesn't turn into a wall
  of quoted transcript — click to expand one at a time.
- **Artifacts produced by a message**: a labeled chip under that message
  (file icon for Markdown, code icon for HTML) that reopens the viewer —
  so switching sessions or scrolling back doesn't lose track of which
  message produced which artifact.

## Artifact interaction

- Opening an artifact doesn't interrupt the chat stream — they're
  independent pieces of state (`useArtifacts` vs `useChatStream`).
  deliberately.
- Closing the viewer never deletes the artifact — it's still reachable via
  the chip on its originating message.
- HTML artifacts render in a sandboxed iframe with its own scroll region;
  Markdown artifacts use `prose` typography tuned to the app's own ink/moss
  palette rather than Tailwind Typography's defaults, so an artifact still
  feels like part of the same product.

## Loading states

- Session list: a small text placeholder, not a skeleton grid — this is a
  short list, a skeleton would be more motion than information.
- Session detail: centered spinner — matches the chat pane's own empty
  state positioning so there's no layout jump once messages arrive.
- Health polling (30s interval) updates the provider dot silently — no
  loading state for this at all, since flashing a spinner every 30 seconds
  would be worse than the two-second-stale status it prevents.

## Error states

- Chat/session fetch failures render inline (`ErrorState.tsx`) with a
  "Try again" affordance, not a toast that disappears before it's read.
- Mid-stream errors (`event: error`) surface the same `ErrorState`
  component under the composer — same visual language whether the failure
  was a bad request or Ollama going down mid-answer.
- The assistant bubble that was streaming when an error hit is left as-is
  (partial content, no cursor) rather than wiped — partial grounded output
  is still more useful than nothing.

## Accessibility

- Every interactive element is a real `<button>`/`<select>`/`<textarea>`,
  not a styled `<div>` — keyboard and screen-reader navigation come for
  free.
- Visible focus ring (`:focus-visible` in `globals.css`) uses the moss
  accent at 2px, distinct from hover states.
- `prefers-reduced-motion` disables the streaming cursor blink and other
  transitions.
- Icon-only buttons (send, close artifact, toggle nav) all carry
  `aria-label`.
- Source citation cards are real `<button>` disclosure toggles
  (`aria-expanded` semantics via the chevron rotation), not click-anywhere
  divs.

## Keyboard navigation

- `Enter` sends a message; `Shift+Enter` inserts a newline
  (`ChatInput.tsx`).
- Standard tab order follows visual order (rail → chat → composer →
  artifact) — no manual `tabIndex` overrides were needed given the DOM
  order already matches.

## Responsive behavior

Single Tailwind breakpoint (`md`, 768px) governs both collapses (session
rail, artifact viewer) — deliberately one breakpoint, not three, since the
three-pane layout only really has two states that matter: "enough room for
two panes" and "one pane at a time."

## Design trade-offs

- **No dark mode.** Cut for time; the palette was chosen to be easy on the
  eyes in light mode for long sessions rather than needing a dark variant
  to achieve that.
- **No message editing/regeneration.** Out of scope per PRD; the UI has no
  affordance implying it's possible, rather than a disabled button that
  invites a bug report.
- **Artifact viewer as full-screen mobile overlay, not a bottom sheet.**
  A bottom sheet is the more polished mobile pattern for this but needs
  drag-gesture handling that a full overlay doesn't; documented as a known
  simplification rather than left unexplained.
