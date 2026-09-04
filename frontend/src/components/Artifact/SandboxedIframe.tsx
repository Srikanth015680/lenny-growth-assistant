"use client";

/**
 * Renders LLM-generated HTML artifacts (section 18 — "Artifact Security").
 *
 * THREAT MODEL: generated HTML is untrusted executable content. An iframe
 * with sandbox="allow-scripts" and srcDoc gets its own opaque origin — it
 * cannot read this page's DOM, cookies, or localStorage, and (because we
 * deliberately do NOT add allow-same-origin) it cannot use that opaque
 * origin's own storage either, or call document.domain to rejoin ours.
 *
 * What this permits: the artifact's own <script> can run and manipulate
 * its own document (so an LLM-generated interactive one-pager still works).
 * What this blocks: reading/writing anything belonging to the parent app,
 * navigating the parent page (no allow-top-navigation), opening new
 * windows/popups (no allow-popups), and submitting forms outside the
 * frame (no allow-forms). We do not add allow-same-origin "to make
 * generated HTML more capable" — that would let the sandboxed document
 * script its way back out, which defeats the isolation entirely.
 */
export function SandboxedIframe({ html }: { html: string }) {
  return (
    <iframe
      title="Generated artifact"
      srcDoc={html}
      sandbox="allow-scripts"
      className="h-full w-full border-0 bg-white"
    />
  );
}
