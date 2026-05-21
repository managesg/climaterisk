/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#f0f9ff",
          100: "#e0f2fe",
          600: "#0284c7",
          700: "#0369a1",
          900: "#0c4a6e",
        },
        risk: {
          verylow: "#16a34a",
          low: "#65a30d",
          moderate: "#ca8a04",
          high: "#ea580c",
          veryhigh: "#dc2626",
        },
      },
    },
  },
  plugins: [],
};
