import type { Config } from "tailwindcss";

/**
 * Claude-inspired theme: warm cream canvas, terracotta accent, calm slate text,
 * soft rounded surfaces and a clean humanist sans-serif stack.
 */
const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        canvas: {
          DEFAULT: "#F0EEE6",
          raised: "#F7F5EF",
          sunken: "#E8E5DA",
        },
        ink: {
          DEFAULT: "#2E2C28",
          soft: "#4A4741",
          muted: "#6B6862",
          faint: "#928F86",
        },
        accent: {
          DEFAULT: "#D97757",
          hover: "#C8623F",
          soft: "#EBC7B6",
          faint: "#F4E4DB",
        },
        line: {
          DEFAULT: "#DED9CC",
          strong: "#C9C3B2",
        },
        success: "#4F7D5B",
        danger: "#B4453A",
      },
      fontFamily: {
        sans: [
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Helvetica Neue",
          "Arial",
          "sans-serif",
        ],
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "Consolas", "monospace"],
      },
      borderRadius: {
        bubble: "1.25rem",
        card: "1rem",
      },
      boxShadow: {
        soft: "0 1px 2px rgba(46, 44, 40, 0.06), 0 4px 16px rgba(46, 44, 40, 0.05)",
        raised: "0 2px 4px rgba(46, 44, 40, 0.08), 0 8px 28px rgba(46, 44, 40, 0.08)",
      },
      keyframes: {
        "fade-in-up": {
          "0%": { opacity: "0", transform: "translateY(6px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "typing-bounce": {
          "0%, 80%, 100%": { transform: "translateY(0)", opacity: "0.4" },
          "40%": { transform: "translateY(-3px)", opacity: "1" },
        },
      },
      animation: {
        "fade-in-up": "fade-in-up 0.25s ease-out",
        "typing-bounce": "typing-bounce 1.2s infinite ease-in-out",
      },
    },
  },
  plugins: [],
};

export default config;
