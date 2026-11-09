/** Icônes en SVG inline, utilisées avec parcimonie : aucune dépendance, un poids négligeable. */
const TRACES = {
  envoyer: <path d="M5 12h14M13 6l6 6-6 6" />,
  externe: <path d="M14 5h5v5M19 5l-8 8M18 14v4a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h4" />,
} as const;

export type NomIcone = keyof typeof TRACES;

export function Icone({ nom, taille = 16, className = "" }: { nom: NomIcone; taille?: number; className?: string }) {
  return (
    <svg
      width={taille}
      height={taille}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      className={`inline-block shrink-0 ${className}`}
    >
      {TRACES[nom]}
    </svg>
  );
}

/** Marque de la charte, à plat : bouclier et G. */
export function Marque({ taille = 24, couleur = "white" }: { taille?: number; couleur?: string }) {
  return (
    <svg width={taille} height={taille} viewBox="0 0 24 24" fill="none" stroke={couleur} strokeWidth="1.8" aria-hidden="true">
      <path d="M12 2.5 L20.5 5.5 V12 C20.5 16.5 16.8 19.8 12 21.8 C7.2 19.8 3.500 16.5 3.500 12 V5.500 Z" />
      <path d="M15.500 9.200 C14.700 8.300 13.500 7.800 12.200 7.800 C9.800 7.800 8 9.500 8 11.900 C8 14.300 9.800 16 12.200 16 C13.700 16 15 15.400 15.800 14.300 V12 H12.500" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

/** Repère d'état : un carré de couleur et un libellé, lisible sans la couleur. */
export function Etat({ ton, children }: { ton: "ok" | "attention" | "erreur"; children: React.ReactNode }) {
  const couleurs = { ok: "bg-ok", attention: "bg-[#c47f00]", erreur: "bg-erreur" };
  return (
    <span className="inline-flex items-center gap-1.5 whitespace-nowrap">
      <span className={`h-2 w-2 shrink-0 ${couleurs[ton]}`} aria-hidden="true" />
      {children}
    </span>
  );
}
