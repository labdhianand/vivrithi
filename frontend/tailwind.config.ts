import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        surface: {
          DEFAULT: "#080d1a",
          50: "#0c1225",
          100: "#101827",
          200: "#161e30",
          300: "#1e2740",
          400: "#263050",
        },
        accent: {
          DEFAULT: "#06b6d4",
          dim: "#0891b2",
          glow: "#22d3ee",
          50: "#ecfeff",
        },
        gold: {
          DEFAULT: "#f59e0b",
          dim: "#d97706",
          glow: "#fbbf24",
        },
        emerald: {
          DEFAULT: "#10b981",
          dim: "#059669",
          glow: "#34d399",
        },
        rose: {
          DEFAULT: "#f43f5e",
          dim: "#e11d48",
          glow: "#fb7185",
        },
        slate: {
          DEFAULT: "#94a3b8",
          dim: "#64748b",
          bright: "#cbd5e1",
          50: "#f8fafc",
        },
      },
      fontFamily: {
        sans: ["var(--font-sora)"],
        serif: ["var(--font-instrument-serif)"],
      },
      boxShadow: {
        glow: "0 0 40px rgba(6, 182, 212, 0.15)",
        "glow-gold": "0 0 40px rgba(245, 158, 11, 0.15)",
        "glow-emerald": "0 0 40px rgba(16, 185, 129, 0.15)",
        "glow-rose": "0 0 40px rgba(244, 63, 94, 0.15)",
        panel: "0 24px 64px rgba(0, 0, 0, 0.4)",
        card: "0 1px 3px rgba(0, 0, 0, 0.3), 0 8px 24px rgba(0, 0, 0, 0.2)",
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "mesh-gradient":
          "radial-gradient(at 40% 20%, hsla(187, 85%, 35%, 0.15) 0px, transparent 50%), radial-gradient(at 80% 0%, hsla(189, 75%, 30%, 0.1) 0px, transparent 50%), radial-gradient(at 0% 50%, hsla(265, 55%, 30%, 0.08) 0px, transparent 50%)",
      },
      animation: {
        "fade-in": "fadeIn 0.5s ease-out forwards",
        "slide-up": "slideUp 0.5s ease-out forwards",
        "slide-in-right": "slideInRight 0.4s ease-out forwards",
        pulse: "pulse 3s ease-in-out infinite",
        "glow-pulse": "glowPulse 2s ease-in-out infinite",
        shimmer: "shimmer 2s linear infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(16px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        slideInRight: {
          "0%": { opacity: "0", transform: "translateX(16px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
        pulse: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.7" },
        },
        glowPulse: {
          "0%, 100%": { boxShadow: "0 0 20px rgba(6, 182, 212, 0.2)" },
          "50%": { boxShadow: "0 0 40px rgba(6, 182, 212, 0.4)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
