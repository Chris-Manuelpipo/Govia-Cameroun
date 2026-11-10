"use client";
import { useState } from "react";
import { Langue, Textes } from "../i18n";
import { Conversation } from "../lib/historique";
import { Icone } from "./icones";

/** Liste des conversations gardées sur cet appareil : ouvrir, supprimer une conversation, ou tout effacer. */
export function Historique({
  conversations,
  idCourant,
  langue,
  t,
  onOuvrir,
  onSupprimer,
  onToutEffacer,
}: {
  conversations: Conversation[];
  idCourant: string | null;
  langue: Langue;
  t: Textes;
  onOuvrir: (id: string) => void;
  onSupprimer: (id: string) => void;
  onToutEffacer: () => void;
}) {
  const [confirme, setConfirme] = useState(false);
  const date = (iso: string) => new Date(iso).toLocaleString(langue === "FR" ? "fr-FR" : "en-GB", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });

  return (
    <div>
      <p className="px-4 py-3 text-[13px] text-texte-2">{t.historiqueNote}</p>
      {conversations.length === 0 ? (
        <p className="px-4 pb-4 text-sm text-texte-2">{t.historiqueVide}</p>
      ) : (
        <ul className="border-y border-ligne bg-surface">
          {conversations.map((c) => (
            <li key={c.id} className="flex items-stretch border-b border-ligne last:border-b-0">
              <button
                onClick={() => onOuvrir(c.id)}
                aria-current={c.id === idCourant ? "true" : undefined}
                className={`min-h-[56px] min-w-0 flex-1 px-4 py-2 text-left hover:bg-fond ${c.id === idCourant ? "bg-accent-clair" : ""}`}
              >
                <span className="line-clamp-2 block font-medium">{c.titre || "…"}</span>
                <span className="block text-[13px] text-texte-2">{date(c.maj)}</span>
              </button>
              <button
                onClick={() => onSupprimer(c.id)}
                aria-label={`${t.supprimerConversation} : ${c.titre}`}
                title={t.supprimerConversation}
                className="grid min-h-[44px] w-12 shrink-0 place-items-center text-texte-2 hover:bg-fond hover:text-erreur"
              >
                <Icone nom="corbeille" taille={18} />
              </button>
            </li>
          ))}
        </ul>
      )}
      {conversations.length > 0 && (
        <div className="px-4 py-3">
          <button
            onClick={() => {
              if (confirme) {
                setConfirme(false);
                onToutEffacer();
              } else setConfirme(true);
            }}
            onBlur={() => setConfirme(false)}
            className={`min-h-[44px] border px-4 font-medium ${confirme ? "border-erreur bg-erreur-clair text-erreur" : "border-ligne-forte hover:bg-fond"}`}
          >
            {confirme ? t.confirmerEffacement : t.toutEffacer}
          </button>
        </div>
      )}
    </div>
  );
}
