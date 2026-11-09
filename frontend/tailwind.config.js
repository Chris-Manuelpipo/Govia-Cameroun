/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        fond: "var(--fond)",
        surface: "var(--surface)",
        texte: "var(--texte)",
        "texte-2": "var(--texte-2)",
        ligne: "var(--ligne)",
        "ligne-forte": "var(--ligne-forte)",
        marine: "var(--marine)",
        accent: "var(--accent)",
        "accent-fonce": "var(--accent-fonce)",
        "accent-clair": "var(--accent-clair)",
        ok: "var(--ok)",
        attention: "var(--attention)",
        "attention-clair": "var(--attention-clair)",
        erreur: "var(--erreur)",
        "erreur-clair": "var(--erreur-clair)",
      },
      fontFamily: {
        sans: ["var(--font-texte)", "system-ui", "sans-serif"],
      },
      borderRadius: {
        DEFAULT: "3px",
      },
    },
  },
  plugins: [],
};
