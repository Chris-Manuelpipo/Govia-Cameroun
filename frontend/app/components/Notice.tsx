"use client";
import { Langue, TEXTES } from "../i18n";
import { Notice as TypeNotice } from "../types";
import { Icone } from "./icones";

const RUBRIQUES = ["responsable", "finalite", "donnees", "destinataires", "conservation", "transfert", "droits", "limites"] as const;

export function Notice({
  notice,
  erreur,
  langue,
  consent,
  enAttente,
  onAccepter,
  onRefuser,
  onRetirer,
}: {
  notice: TypeNotice | null;
  erreur: boolean;
  langue: Langue;
  consent: boolean;
  enAttente: string | null;
  onAccepter: () => void;
  onRefuser: () => void;
  onRetirer: () => void;
}) {
  const t = TEXTES[langue];

  if (erreur) {
    return (
      <p role="alert" className="border-l-4 border-erreur bg-erreur-clair px-3 py-2 text-erreur">
        {t.consentementErreur}
      </p>
    );
  }
  if (!notice) return <p className="text-texte-2">{t.consentementChargement}</p>;

  return (
    <div className="border border-ligne bg-surface">
      <div className="px-4 pb-1 pt-5 sm:px-6">
        <h1 className="text-[26px] font-bold leading-tight text-titre">{notice.titre}</h1>

        {/* Statut du consentement : visible avant toute lecture */}
        {consent ? (
          <div className="mt-3 flex flex-wrap items-center justify-between gap-3 border-l-4 border-ok bg-ok-clair px-3 py-2.5">
            <div className="flex items-start gap-2.5">
              <Icone nom="coche-cercle" taille={20} className="mt-0.5 text-ok" />
              <div>
                <p className="font-semibold text-texte">{t.accordDonne}</p>
                <p className="text-[14px] text-texte-2">{t.retraitTexte}</p>
              </div>
            </div>
            <button onClick={onRetirer} className="min-h-[44px] border border-ligne-forte bg-surface px-4 font-medium hover:bg-fond">
              {t.retirer}
            </button>
          </div>
        ) : (
          <div className="mt-3 flex items-start gap-2.5 border-l-4 border-attention-vif bg-attention-clair px-3 py-2.5">
            <Icone nom="cadenas" taille={20} className="mt-0.5 text-attention-vif" />
            <div>
              <p className="font-semibold text-texte">{t.accordAbsent}</p>
              <p className="text-[14px] text-texte-2">{enAttente ? t.enAttente(enAttente) : t.accordAbsentTexte}</p>
            </div>
          </div>
        )}
      </div>

      <dl className="mt-3 border-t border-ligne">
        {RUBRIQUES.map((r) => (
          <div key={r} className={`border-b border-ligne px-4 py-3 sm:grid sm:grid-cols-[190px_minmax(0,1fr)] sm:gap-4 sm:px-6 ${r === "limites" ? "bg-attention-clair" : ""}`}>
            <dt className="font-semibold">{t.rubriques[r]}</dt>
            <dd className={r === "limites" ? "text-texte" : "text-texte-2"}>{notice[r]}</dd>
          </div>
        ))}
      </dl>
      <p className="px-4 py-3 text-[13px] text-texte-2 sm:px-6">{t.cadreLegal}</p>

      {!consent && (
        <div className="sticky bottom-0 z-10 border-t border-ligne bg-surface px-4 py-3 sm:px-6">
          <div className="flex flex-wrap gap-2">
            <button onClick={onAccepter} className="min-h-[44px] bg-bouton px-4 font-semibold text-white hover:bg-bouton-fonce">
              {notice.action}
            </button>
            <button onClick={onRefuser} className="min-h-[44px] border border-ligne-forte px-4 font-medium hover:bg-fond">
              {t.refuser}
            </button>
          </div>
          <p className="mt-1.5 text-[13px] text-texte-2">{t.refusTexte}</p>
        </div>
      )}
    </div>
  );
}
