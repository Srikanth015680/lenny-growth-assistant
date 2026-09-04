# 07 — Artifact generation + viewer

Backend (`artifact_generator.py`): same shape as the Ship30 skill —
grounded generation, `InsufficientContextError` on empty context. HTML
output is validated server-side to actually start with
`<!DOCTYPE html>`/`<html` before being accepted (`ArtifactGenerationError`
otherwise) — a model that ignores the "respond with only the HTML
document" instruction fails loudly instead of persisting garbage.

Frontend (`SandboxedIframe.tsx`, `MarkdownArtifact.tsx`,
`ArtifactViewer.tsx`): the security-critical decision here is
`sandbox="allow-scripts"` with **no** `allow-same-origin` — documented at
length in `SandboxedIframe.tsx`'s own docstring, since section 18
specifically calls out not weakening this "to make generated HTML more
capable." Markdown goes through `react-markdown` (which doesn't render
raw HTML unless `rehype-raw` is added — not added) plus a DOMPurify pass
on the raw source as defense-in-depth.

This is the one area where the security *design* is complete and
documented but the isolation property itself (does the sandboxed iframe
really block parent-DOM access, cookies, localStorage) needs a real
browser to exercise — this sandbox could verify the code compiles and the
generation-layer contracts (valid-HTML-document check, code-fence
stripping) via pytest, but not a live browser sandbox escape test. Flagged
in `docs/PRD.md`'s acceptance criteria and `docs/troubleshooting.md`
rather than claimed as verified.
