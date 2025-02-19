/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./templates/**/*.{html,jinja2,js}", "./static/**/*.{html,jinja2,js}"],
  theme: {
    extend: {},
  },
  plugins: [require("daisyui")],
  daisyui: {
    themes: ["light", "dark"]
  },
};
