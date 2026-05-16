import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))"
        },
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))"
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))"
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))"
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))"
        },
        conforma: {
          navy: "#08162d",
          blue: "#1f66ff",
          steel: "#8ea9d4",
          white: "#f6fbff",
          amber: "#f3c96b"
        }
      },
      boxShadow: {
        panel: "0 24px 60px rgba(6, 16, 33, 0.24)"
      },
      backgroundImage: {
        "grid-fade":
          "linear-gradient(rgba(124, 154, 207, 0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(124, 154, 207, 0.08) 1px, transparent 1px)"
      }
    }
  },
  plugins: []
};

export default config;
