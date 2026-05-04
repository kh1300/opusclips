import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#07070a",
        panel: "#111217",
        line: "rgba(255,255,255,0.1)"
      },
      boxShadow: {
        glow: "0 0 40px rgba(52, 211, 153, 0.16)"
      }
    }
  },
  plugins: []
};

export default config;

