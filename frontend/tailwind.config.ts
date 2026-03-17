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
          DEFAULT: "#1a0a0f",
          50: "#1f0d16",
          100: "#2d1420",
          200: "#3d1a2a",
          300: "#4a1530",
          400: "#7a2550",
        },
        accent: {
          DEFAULT: "#e91e8c",
          dim: "#c4187a",
          glow: "#ff6bb5",
          50: "#fce4ec",
        },
        brand: {
          950: "#1a0a0f",
          900: "#2d1420",
          800: "#3d1a2a",
          700: "#4a1530",
          600: "#7a2550",
          500: "#8b2252",
          400: "#ad6883",
          300: "#f48fb1",
          200: "#ff6bb5",
          100: "#fce4ec",
          DEFAULT: "#e91e8c",
          hover: "#c4187a",
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
          DEFAULT: "#f48fb1",
          dim: "#ad6883",
          bright: "#fce4ec",
          50: "#1f0d16",
        },
      },
      fontFamily: {
        sans: ["var(--font-manrope)"],
        serif: ["var(--font-fraunces)"],
      },
      boxShadow: {
        glow: "0 18px 42px rgba(233, 30, 140, 0.22)",
        "glow-gold": "0 18px 42px rgba(214, 166, 85, 0.18)",
        "glow-emerald": "0 18px 42px rgba(34, 176, 125, 0.16)",
        "glow-rose": "0 18px 42px rgba(216, 90, 113, 0.18)",
        panel: "0 28px 72px rgba(26, 8, 16, 0.5)",
        card: "0 12px 36px rgba(26, 8, 16, 0.32)",
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "mesh-gradient":
          "radial-gradient(at 18% 18%, rgba(233, 30, 140, 0.16) 0px, transparent 42%), radial-gradient(at 82% 0%, rgba(255, 107, 181, 0.12) 0px, transparent 40%), radial-gradient(at 50% 100%, rgba(139, 34, 82, 0.12) 0px, transparent 48%)",
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
          "0%, 100%": { boxShadow: "0 0 18px rgba(233, 30, 140, 0.22)" },
          "50%": { boxShadow: "0 0 30px rgba(233, 30, 140, 0.34)" },
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
