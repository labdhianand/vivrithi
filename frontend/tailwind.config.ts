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
          DEFAULT: "#09111f",
          50: "#0f182b",
          100: "#142038",
          200: "#1b2a46",
          300: "#243658",
          400: "#2d436a",
        },
        accent: {
          DEFAULT: "#4f7cff",
          dim: "#3b63d9",
          glow: "#9cb8ff",
          50: "#edf3ff",
        },
        gold: {
          DEFAULT: "#d6a655",
          dim: "#b8893f",
          glow: "#f0cb85",
        },
        emerald: {
          DEFAULT: "#22b07d",
          dim: "#17845f",
          glow: "#75d3ad",
        },
        rose: {
          DEFAULT: "#d85a71",
          dim: "#ba455c",
          glow: "#f19aaa",
        },
        slate: {
          DEFAULT: "#9aa7c2",
          dim: "#72809b",
          bright: "#e7eefb",
          50: "#f7f9fd",
        },
      },
      fontFamily: {
        sans: ["var(--font-manrope)"],
        serif: ["var(--font-fraunces)"],
      },
      boxShadow: {
        glow: "0 18px 42px rgba(79, 124, 255, 0.2)",
        "glow-gold": "0 18px 42px rgba(214, 166, 85, 0.18)",
        "glow-emerald": "0 18px 42px rgba(34, 176, 125, 0.16)",
        "glow-rose": "0 18px 42px rgba(216, 90, 113, 0.18)",
        panel: "0 28px 72px rgba(3, 10, 24, 0.44)",
        card: "0 12px 36px rgba(5, 12, 30, 0.22)",
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "mesh-gradient":
          "radial-gradient(at 18% 18%, rgba(79, 124, 255, 0.16) 0px, transparent 42%), radial-gradient(at 82% 0%, rgba(34, 176, 125, 0.12) 0px, transparent 40%), radial-gradient(at 50% 100%, rgba(214, 166, 85, 0.08) 0px, transparent 48%)",
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
          "0%, 100%": { boxShadow: "0 0 18px rgba(79, 124, 255, 0.22)" },
          "50%": { boxShadow: "0 0 30px rgba(79, 124, 255, 0.34)" },
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
