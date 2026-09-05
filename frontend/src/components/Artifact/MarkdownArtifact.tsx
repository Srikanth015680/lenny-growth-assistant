"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import DOMPurify from "dompurify";


export function MarkdownArtifact({ content }: { content: string }) {
  const sanitized =
    typeof window !== "undefined" ? DOMPurify.sanitize(content, { ALLOWED_TAGS: [] }) : content;

  return (
    <div className="prose prose-sm max-w-none px-6 py-5 prose-headings:text-ink prose-p:text-ink/90 prose-a:text-moss prose-strong:text-ink prose-code:text-clay">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{sanitized}</ReactMarkdown>
    </div>
  );
}
