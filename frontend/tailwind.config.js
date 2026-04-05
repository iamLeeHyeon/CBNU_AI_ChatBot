/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        cbnu: {
          blue: "#003087",
          light: "#0057B8",
        },
      },
    },
  },
  plugins: [],
};
