import type { Config } from "tailwindcss";

export default {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        cyber: {
          black: "#020202",
          dark: "#0a0a0a",
          panel: "#111111",
          primary: "#00f3ff",
          purple: "#bc13fe",
          success: "#0aff0a",
          danger: "#ff003c",
          warning: "#fcee0a",
          muted: "#444444",
          border: "rgba(255,255,255,0.1)",
        },
      },
      fontFamily: {
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "Monaco", "Consolas", "Liberation Mono", "Courier New", "monospace"],
      },
      boxShadow: {
        "glow-cyan": "0 0 10px rgba(0, 243, 255, 0.3)",
        "glow-purple": "0 0 10px rgba(188, 19, 254, 0.3)",
        "glow-green": "0 0 10px rgba(10, 255, 10, 0.3)",
      },
    },
  },
  plugins: [],
} satisfies Config;
