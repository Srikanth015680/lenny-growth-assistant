import type { Config } from "tailwindcss";

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
          soft: "#E7F0EA"
        },
        clay: {
          DEFAULT: "#A9702F",
          soft: "#F4E9DA"
        },
        danger: {
          DEFAULT: "#B3432B",
          soft: "#F6E4DE"
        }
      },
      fontFamily: {
        sans: [
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "Roboto",
          "Helvetica Neue",
          "Arial",
          "sans-serif"
        ]
      },
      borderRadius: {
        sm: "4px",
        md: "8px",
        lg: "12px"
      }
    }
  },
  plugins: []
};

export default config;