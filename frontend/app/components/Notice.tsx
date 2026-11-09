"use client";
import { Langue, TEXTES } from "../i18n";
import { Notice as TypeNotice } from "../types";

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
      <p role="alert" className="border-l-[3px] border-erreur bg-erreur-clair px-3 py-2 text-erreur">
        {t.consentementErreur}
      </p>
    );
  }
  if (!notice) return <p className="text-texte-2">{t.consentementChargement}</p>;

  return (
    <div className="max-w-[820px]">
      <h1 className="text-[26px] font-bold leading-tight">{notice.titre}</h1>

      {enAttente && !consent && <p className="mt-3 border-l-[3px] border-accent bg-accent-clair px-3 py-2">{t.enAttente(enAttente)}</p>}

      <dl className="mt-4 border-t border-ligne">
        {RUBRIQUES.map((r) => (
          <div key={r} className={`border-b border-ligne py-2.5 sm:grid sm:grid-cols-[190px_minmax(0,1fr)] sm:gap-4 ${r === "limites" ? "bg-attention-clair px-2 sm:-mx-2" : ""}`}>
            <dt className="font-semibold">{t.rubriques[r]}</dt>
            <dd className={r === "limites" ? "text-texte" : "text-texte-2"}>{notice[r]}</dd>
          </div>
        ))}
      </dl>

      {consent ? (
        <div className="mt-5">
          <p className="font-semibold text-ok">{t.accordDonne}</p>
          <p className="mt-1 text-texte-2">{t.retraitTexte}</p>
          <button onClick={onRetirer} className="mt-3 rounded border border-ligne-forte px-4 py-2 font-medium hover:bg-fond">
            {t.retirer}
          </button>
        </div>
      ) : (
        <div className="mt-5">
          <div className="flex flex-wrap gap-2">
            <button onClick={onAccepter} className="rounded bg-accent px-4 py-2 font-semibold text-white hover:bg-accent-fonce">
              {notice.action}
            </button>
            <button onClick={onRefuser} className="rounded border border-ligne-forte px-4 py-2 font-medium hover:bg-fond">
              {t.refuser}
            </button>
          </div>
          <p className="mt-2 text-sm text-texte-2">{t.refusTexte}</p>
        </div>
      )}
    </div>
  );
}
