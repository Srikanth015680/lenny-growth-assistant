"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import DOMPurify from "dompurify";

/**
 * react-markdown does not render raw HTML embedded in markdown source
 * unless the rehype-raw plugin is added — we deliberately don't add it, so
 * this is already safe against script injection by default. We still run
 * the raw markdown through DOMPurify first as a defense-in-depth measure
 * (per section 21's dependency list): if any inline HTML tags are present
 * in the source, they're stripped before react-markdown ever parses them,
 * so the safety property holds even if a future change adds rehype-raw.
 */
export function MarkdownArtifact({ content }: { content: string }) {
  const sanitized =
    typeof window !== "undefined" ? DOMPurify.sanitize(content, { ALLOWED_TAGS: [] }) : content;

  return (
    <div className="prose prose-sm max-w-none px-6 py-5 prose-headings:text-ink prose-p:text-ink/90 prose-a:text-moss prose-strong:text-ink prose-code:text-clay">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{sanitized}</ReactMarkdown>
    </div>
  );
}
