# 08 — Frontend

Before writing any component, planned the visual direction deliberately
(recorded in `docs/design.md`) rather than defaulting to generic
Tailwind-starter styling: a quiet paper/ink palette with exactly two
meaningful accents (moss for the assistant, clay reserved for transcript
citations so sourced evidence is visually distinct from the model's own
words), system font stack (no webfont network dependency), avoiding the
usual AI-generated-UI tells (identical shadow-card grids, ALL-CAPS
eyebrows, em-dash labels, arrow-suffixed buttons).

Built bottom-up: `lib/types.ts` (hand-mirrored from the backend Pydantic
schemas) and `lib/api.ts` (including a hand-rolled SSE parser over
`fetch()`, since `EventSource` can't do POST) first, then UI primitives,
then Chat components, then Artifact components, then the two hooks
(`useSessions`, `useChatStream`) tying it together, then `page.tsx` last.

Two real errors caught and fixed here, not left in the delivered code:
- `next.config.ts` isn't supported by Next.js 14.x (that's a Next 15+
  feature) — `next build` failed immediately with a clear error;
  converted to `next.config.mjs`.
- `npm install` initially pulled Next.js 14.2.15, which `npm audit`
  flagged as having a critical/high-severity advisory with a public
  writeup. Bumped to the latest 14.2.x patch (14.2.35) plus a DOMPurify
  bump (moderate advisory) and re-ran audit — resolved the critical/high
  findings; 5 remaining high-severity findings are a transitive PostCSS
  dependency bundled *inside* Next 14's own toolchain (build-time
  source-map path traversal, not a runtime vulnerability), which would
  need a Next 15/16 major upgrade to fully clear — documented rather than
  silently ignored or force-upgraded blind.

`npm install` + `NEXT_PUBLIC_API_URL=... npx next build` were both run for
real and succeeded, including strict TypeScript checking
(`"strict": true` in `tsconfig.json`) — this is a genuinely compiling
Next.js app, not just syntactically-plausible-looking source files. Also
ran backend + frontend together (`next start` against a live local
`uvicorn`) and confirmed the built page serves with a 200 and the correct
title, and confirmed `/api/health` reflects real Postgres state through
to the browser-facing API contract.
