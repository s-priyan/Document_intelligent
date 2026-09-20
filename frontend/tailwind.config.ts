import type { Config } from "tailwindcss";

/**
 * Dark knowledge workspace with blue actions and muted slate surfaces.
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
          DEFAULT: "#0B1223",
          raised: "#080E1D",
          sunken: "#151E33",
        },
        ink: {
          DEFAULT: "#F3F6FC",
          soft: "#CCD5E5",
          muted: "#95A5BE",
          faint: "#8B9AB2",
        },
        accent: {
          DEFAULT: "#2454FF",
          hover: "#3D68FF",
          soft: "#A5B8FF",
          faint: "#101D43",
        },
        line: {
          DEFAULT: "#263044",
          strong: "#43516A",
        },
        success: "#79DBA6",
        danger: "#FF839A",
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
