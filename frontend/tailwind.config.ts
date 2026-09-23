import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./hooks/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        obsidian: "#05070d",
        panel: "#0a0f1c",
        panel2: "#0d1424",
        edge: "#1a2332",
        edgelit: "#24314a",
        emeraldx: "#34d399",
        violetx: "#a78bfa",
        cyanx: "#22d3ee",
        amberx: "#fbbf24",
        rosex: "#fb7185",
        ink: "#f8fafc",
        inkdim: "#c8d3e5",
        inkfaint: "#94a3b8",
      },
      fontFamily: {
        sans: ["var(--font-inter)", "ui-sans-serif", "system-ui", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "sans-serif"],
        display: ["var(--font-space)", "var(--font-inter)", "ui-sans-serif", "system-ui", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "sans-serif"],
        mono: ["var(--font-jetbrains)", "ui-monospace", "SFMono-Regular", "Menlo", "Consolas", "monospace"],
      },
      animation: {
        "pulse-dot": "pulseDot 1.8s infinite",
      },
      keyframes: {
        pulseDot: {
          "0%, 100%": { transform: "scale(0.85)", opacity: "0.7" },
          "50%": { transform: "scale(1.25)", opacity: "1" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
