"use client";
import { Langue, TEXTES } from "../i18n";
import { DemarcheCatalogue, DocumentSource, Notice as TypeNotice, Statut, Stats } from "../types";
import { Etat } from "./icones";
import { Notice } from "./Notice";
import { chiffres, Statistiques } from "./Statistiques";

const TONS: Record<Statut, "ok" | "attention" | "erreur"> = { couvert: "ok", partiel: "attention", lacune: "erreur" };

/** Vue « Données et consentement » : la notice d'information et, à côté, les chiffres de la base de connaissances. */
export function Donnees({
  notice,
  erreur,
  langue,
  consent,
  enAttente,
  stats,
  documents,
  catalogue,
  onAccepter,
  onRefuser,
  onRetirer,
}: {
  notice: TypeNotice | null;
  erreur: boolean;
  langue: Langue;
  consent: boolean;
  enAttente: string | null;
  stats: Stats | null;
  documents: DocumentSource[];
  catalogue: DemarcheCatalogue[];
  onAccepter: () => void;
  onRefuser: () => void;
  onRetirer: () => void;
}) {
  const t = TEXTES[langue];
  const base = chiffres(stats, documents);
  const parStatut = (statut: Statut) => stats?.demarches[statut] ?? catalogue.filter((d) => d.statut === statut).length;

  return (
    <div className="mx-auto max-w-[1280px] px-4 py-6 lg:px-6">
      <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
        <Notice notice={notice} erreur={erreur} langue={langue} consent={consent} enAttente={enAttente} onAccepter={onAccepter} onRefuser={onRefuser} onRetirer={onRetirer} />

        <aside aria-labelledby="stats-titre" className="border border-ligne bg-surface px-4 py-4 sm:px-5 lg:sticky lg:top-16">
          <h2 id="stats-titre" className="text-[17px] font-bold text-titre">
            {t.statsTitre}
          </h2>
          {base ? (
            <div className="mt-3">
              <Statistiques chiffres={base} t={t} compact />
            </div>
          ) : (
            <p className="mt-2 text-texte-2">{t.sourcesIndisponibles}</p>
          )}

          {catalogue.length > 0 && (
            <div className="mt-5 border-t border-ligne pt-3">
              <h3 className="text-[15px] font-semibold">{t.statsDemarches}</h3>
              <p className="text-[13px] text-texte-2">{t.demarchesTotal(catalogue.length)}</p>
              <ul className="mt-2 divide-y divide-ligne text-sm">
                {(["couvert", "partiel", "lacune"] as Statut[]).map((s) => (
                  <li key={s} className="flex items-center justify-between py-1.5">
                    <Etat ton={TONS[s]} icone={s === "lacune" ? "document-barre" : undefined}>
                      {t.statuts[s]}
                    </Etat>
                    <span className="font-semibold tabular-nums">{parStatut(s)}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}
