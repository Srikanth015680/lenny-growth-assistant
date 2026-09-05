# 07 — Artifact Generation and Viewer

## Goal

Allow the assistant to generate Markdown and HTML artifacts and render them
inside the application instead of showing only the generated source code.

## Backend

Implemented `artifact_generator.py`.

The artifact generator follows the same grounding approach as the Ship 30
skill.

Before generating an artifact:

1. Retrieve relevant transcript context.
2. Pass the grounded context to the selected LLM provider.
3. Generate the requested artifact.
4. Validate the generated output.
5. Persist the artifact.

If there is no usable transcript context, generation stops with
`InsufficientContextError`.

For HTML artifacts, the backend also checks that the generated response is
actually an HTML document before accepting it. Invalid output is rejected
instead of being persisted.

## Frontend

Implemented:

- `ArtifactViewer.tsx`
- `MarkdownArtifact.tsx`
- `SandboxedIframe.tsx`

Markdown artifacts are rendered using `react-markdown` with GitHub-flavored
Markdown support.

Raw HTML rendering is not enabled for Markdown content.

DOMPurify is also used as an additional sanitization layer.

## HTML Security

Generated HTML is treated as untrusted content.

HTML artifacts are rendered inside a sandboxed iframe using:

`sandbox="allow-scripts"`

The iframe does not use `allow-same-origin`.

This prevents the generated document from sharing the application's origin
and limits its ability to access application resources.

The sandbox configuration is intentionally restrictive rather than adding
permissions simply to make generated HTML more capable.

## Browser Verification

The artifact generation and validation logic was tested automatically.

The complete iframe isolation behavior could not be verified in the build
environment because it did not provide a real browser environment.

Therefore, browser-level sandbox behavior was documented as a manual
verification item rather than being reported as fully tested.

## Result

The application can generate Markdown and HTML artifacts and display them
inside the product while keeping generated HTML isolated from the main
applicatio

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
