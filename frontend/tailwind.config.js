/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        // Surfaces et texte
        fond: "var(--fond)",
        surface: "var(--surface)",
        texte: "var(--texte)",
        "texte-2": "var(--texte-2)",
        ligne: "var(--ligne)",
        "ligne-forte": "var(--ligne-forte)",
        // Institutionnel : marine pour l'en-tête et le texte fort, bleu pour les liens et boutons
        marine: "var(--marine)",
        titre: "var(--titre)",
        bouton: "var(--bouton)",
        "bouton-fonce": "var(--bouton-fonce)",
        desactive: "var(--desactive)",
        "sur-desactive": "var(--sur-desactive)",
        bulle: "var(--bulle)",
        "marine-2": "var(--marine-2)",
        "sur-marine": "var(--sur-marine)",
        accent: "var(--accent)",
        "accent-fonce": "var(--accent-fonce)",
        "accent-clair": "var(--accent-clair)",
        // États : « vif » sert aux pastilles graphiques, la couleur pleine au texte
        ok: "var(--ok)",
        "ok-fonce": "var(--ok-fonce)",
        "ok-clair": "var(--ok-clair)",
        attention: "var(--attention)",
        "attention-vif": "var(--attention-vif)",
        "attention-clair": "var(--attention-clair)",
        erreur: "var(--erreur)",
        "erreur-clair": "var(--erreur-clair)",
        // Couleurs nationales
        vert: "var(--vert)",
        rouge: "var(--rouge)",
        jaune: "var(--jaune)",
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
