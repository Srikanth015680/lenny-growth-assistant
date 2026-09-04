import type { Config } from "tailwindcss";

// Design tokens for The Lenny Growth Assistant.
//
// This is an internal research tool, not a marketing surface — the palette
// is deliberately quiet (warm paper + ink) with exactly two accents that
// each mean something specific: moss (the assistant / primary actions) and
// clay (transcript citations, so sourced evidence always reads as visually
// distinct from the assistant's own words). A system font stack is a
// deliberate choice here too — zero network dependency, instant paint, and
// this is a tool people will have open all day.
const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: "#F6F4EF",
        ink: "#201F1C",
        panel: "#FFFFFF",
        line: "#E2DED2",
        moss: {
          DEFAULT: "#2F6B4E",
          deep: "#204A35",
          soft: "#E7F0EA",
        },
        clay: {
          DEFAULT: "#A9702F",
          soft: "#F4E9DA",
        },
        danger: {
          DEFAULT: "#B3432B",
          soft: "#F6E4DE",
        },
      },
      fontFamily: {
        sans: [
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "Roboto",
          "Helvetica Neue",
          "Arial",
          "sans-serif",
        ],
      },
      borderRadius: {
        sm: "4px",
        md: "8px",
        lg: "12px",
      },
    },
  },
  plugins: [],
};

export default config;
