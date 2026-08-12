import type { Config } from "tailwindcss";

export default {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./features/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: "#24252d",
        primary: "#3B82F6",
        violet: "#8B5CF6",
        tertiary: "#D16900",
        neutral: "#757780",
        mist: "#F0F1F8",
      },
      fontFamily: {
        display: ["Plus Jakarta Sans", "Inter", "Segoe UI", "sans-serif"],
        sans: ["Inter", "Segoe UI", "sans-serif"],
      },
      boxShadow: {
        soft: "0 18px 45px rgba(48,52,78,.10)",
      },
    },
  },
  plugins: [],
} satisfies Config;
