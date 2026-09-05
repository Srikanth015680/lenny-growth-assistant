import { ReactNode } from "react";

type Tone = "moss" | "clay" | "danger" | "neutral";

const toneClasses: Record<Tone, string> = {
  moss: "bg-moss-soft text-moss-deep",
  clay: "bg-clay-soft text-clay",
  danger: "bg-danger-soft text-danger",
  neutral: "bg-paper text-ink/70 border border-line",
};

interface BadgeProps {
  tone?: Tone;
  children: ReactNode;
}

export function Badge({ tone = "neutral", children }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-sm px-2 py-0.5 text-xs font-medium ${toneClasses[tone]}`}
    >
      {children}
    </span>
  );
}