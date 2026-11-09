/** Icônes en SVG inline, utilisées avec parcimonie : aucune dépendance, un poids négligeable. */
const TRACES = {
  envoyer: <path d="M5 12h14M13 6l6 6-6 6" />,
  retour: <path d="M19 12H5M11 6l-6 6 6 6" />,
  externe: <path d="M14 5h5v5M19 5l-8 8M18 14v4a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h4" />,
  liste: <path d="M9 6h11M9 12h11M9 18h11M4.5 6h.01M4.5 12h.01M4.5 18h.01" />,
  dialogue: <path d="M4 5h16a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1h-9.5l-5 4v-4H4a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1z" />,
  document: <path d="M6 3h8l5 5v13H6zM14 3v5h5M9 13h7M9 17h7" />,
  "document-barre": <path d="M6 3h8l5 5v13H6zM14 3v5h5M9 13h7M9 17h4M3.5 3.5l17 17" />,
  bouclier: <path d="M12 3l8 3v6c0 4.6-3.2 7.9-8 9-4.8-1.1-8-4.4-8-9V6zM8.5 12l2.5 2.5 4.5-5" />,
  loupe: (
    <>
      <circle cx="11" cy="11" r="6.5" />
      <path d="M20 20l-4.2-4.2" />
    </>
  ),
  "coche-cercle": (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M8 12.5l3 3 5-6" />
    </>
  ),
  coche: <path d="M5 12.5l4.5 4.5L19 7.5" />,
  alerte: <path d="M12 3.5L21.5 20h-19zM12 10v4.5M12 17.5h.01" />,
  "croix-cercle": (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M9 9l6 6M15 9l-6 6" />
    </>
  ),
  interrogation: <path d="M8.8 9a3.3 3.3 0 1 1 4.6 3c-1 .5-1.4 1.1-1.4 2.3M12 18.2h.01" />,
  info: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 11v5.5M12 7.6h.01" />
    </>
  ),
  cadenas: (
    <>
      <rect x="5" y="11" width="14" height="9.5" rx="1.5" />
      <path d="M8 11V8a4 4 0 0 1 8 0v3" />
    </>
  ),
  copier: (
    <>
      <rect x="9" y="9" width="11" height="11" rx="1.5" />
      <path d="M5 15V6.5A1.5 1.5 0 0 1 6.5 5H15" />
    </>
  ),
  "chevron-bas": <path d="M6 9l6 6 6-6" />,
  batiment: <path d="M3 21h18M5.5 21V10.5M9.5 21V10.5M14.5 21V10.5M18.5 21V10.5M2.5 10.5L12 4l9.5 6.5z" />,
} as const;

export type NomIcone = keyof typeof TRACES;

export function Icone({ nom, taille = 16, className = "", epaisseur = 2 }: { nom: NomIcone; taille?: number; className?: string; epaisseur?: number }) {
  return (
    <svg
      width={taille}
      height={taille}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={epaisseur}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      className={`inline-block shrink-0 ${className}`}
    >
      {TRACES[nom]}
    </svg>
  );
}

/** Étoile à cinq branches, celle du drapeau. */
export function Etoile({ className = "" }: { className?: string }) {
  return (
    <svg viewBox="0 0 10 10" aria-hidden="true" className={className}>
      <path d="M5 0l1.2 3.6H10L6.9 5.8 8.1 9.5 5 7.2 1.9 9.5 3.1 5.8 0 3.6h3.8z" fill="currentColor" />
    </svg>
  );
}

/** Marque de la charte : bouclier, étoile du drapeau et G, au trait blanc pour l'en-tête marine. */
export function Marque({ taille = 24, couleur = "white" }: { taille?: number; couleur?: string }) {
  return (
    <svg width={taille} height={taille} viewBox="0 0 24 24" fill="none" stroke={couleur} strokeWidth="1.7" aria-hidden="true">
      <path d="M12 2.5 L20.5 5.5 V12 C20.5 16.5 16.8 19.8 12 21.8 C7.2 19.8 3.5 16.5 3.5 12 V5.5 Z" />
      <path d="M15.8 10.3 C15 9.2 13.7 8.7 12.3 8.7 C9.9 8.7 8.2 10.4 8.2 12.7 C8.2 15 9.9 16.7 12.3 16.7 C13.8 16.7 15.1 16.1 15.9 15 V12.8 H12.6" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M12 3.5l.6 1.8h1.9l-1.5 1.1.6 1.8-1.6-1.1-1.6 1.1.6-1.8-1.5-1.1h1.9z" fill="#fcd116" stroke="none" />
    </svg>
  );
}

type Ton = "ok" | "attention" | "erreur";

const ICONE_PAR_TON: Record<Ton, NomIcone> = { ok: "coche-cercle", attention: "alerte", erreur: "croix-cercle" };
const COULEUR_PAR_TON: Record<Ton, string> = { ok: "text-ok", attention: "text-attention-vif", erreur: "text-erreur" };

/** Repère d'état : une forme propre à chaque état, sa couleur et un libellé. Jamais la couleur seule. */
export function Etat({ ton, children, icone, taille = 15 }: { ton: Ton; children: React.ReactNode; icone?: NomIcone; taille?: number }) {
  return (
    <span className="inline-flex items-center gap-1.5">
      <Icone nom={icone || ICONE_PAR_TON[ton]} taille={taille} className={COULEUR_PAR_TON[ton]} />
      <span>{children}</span>
    </span>
  );
}
