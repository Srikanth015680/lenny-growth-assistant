"use client";

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