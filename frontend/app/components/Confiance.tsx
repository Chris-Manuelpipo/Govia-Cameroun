"use client";
import { Confiance } from "../lib/confiance";
import { Textes } from "../i18n";
import { Icone, NomIcone } from "./icones";

/** Une forme, une couleur et un libellé par niveau : la couleur n'est jamais le seul signe. */
export const STYLE_CONFIANCE: Record<Confiance["niveau"], { icone: NomIcone; couleur: string; barre: string; boite: string }> = {
  verifie: { icone: "coche-cercle", couleur: "text-ok", barre: "border-l-ok", boite: "border-ok bg-ok-clair" },
  a_verifier: { icone: "alerte", couleur: "text-attention-vif", barre: "border-l-attention-vif", boite: "border-attention-vif bg-attention-clair" },
  aucun: { icone: "document-barre", couleur: "text-erreur", barre: "border-l-erreur", boite: "border-erreur bg-erreur-clair" },
};

/** Version en ligne, pour l'en-tête d'une bulle. */
export function ConfianceEnLigne({ confiance, t }: { confiance: Confiance; t: Textes }) {
  const style = STYLE_CONFIANCE[confiance.niveau];
  return (
    <p className="flex items-center gap-1.5 text-[14px] font-semibold text-texte">
      <Icone nom={style.icone} taille={17} className={style.couleur} />
      {t.confiance[confiance.niveau].libelle}
    </p>
  );
}

/** Version complète, pour l'en-tête de la fiche : libellé, ce qu'il signifie et, au besoin, la raison. */
export function ConfianceComplete({ confiance, t }: { confiance: Confiance; t: Textes }) {
  const style = STYLE_CONFIANCE[confiance.niveau];
  const { libelle, detail } = t.confiance[confiance.niveau];
  return (
    <div className={`flex items-start gap-2.5 border-l-4 px-3 py-2 ${style.boite}`}>
      <Icone nom={style.icone} taille={20} className={`mt-0.5 ${style.couleur}`} />
      <div>
        <p className="font-semibold text-texte">{libelle}</p>
        <p className="text-[14px] text-texte-2">{confiance.raison ? t.raisons[confiance.raison] : detail}</p>
      </div>
    </div>
  );
}
