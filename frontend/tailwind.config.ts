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
        ink: "#172033",
        primary: "#3157D5",
        violet: "#6454D9",
        tertiary: "#B7791F",
        neutral: "#647084",
        mist: "#F1F4F8",
      },
      fontFamily: {
        display: ["Segoe UI Variable Display", "Segoe UI", "Noto Sans Arabic", "sans-serif"],
        sans: ["Segoe UI Variable Text", "Segoe UI", "Noto Sans Arabic", "sans-serif"],
      },
      boxShadow: {
        soft: "0 8px 24px rgba(23,32,51,.08)",
      },
    },
  },
  plugins: [],
} satisfies Config;
