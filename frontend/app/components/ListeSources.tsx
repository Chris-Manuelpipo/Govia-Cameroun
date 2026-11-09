"use client";
import { Langue, TEXTES } from "../i18n";
import { DocumentSource, Stats } from "../types";
import { Etat, Icone } from "./icones";

const ORDRE: DocumentSource["type_source"][] = ["texte_officiel", "reproduction", "portail_institutionnel"];

export function ListeSources({ documents, stats, erreur, langue }: { documents: DocumentSource[]; stats: Stats | null; erreur: boolean; langue: Langue }) {
  const t = TEXTES[langue];
  const tries = [...documents].sort((a, b) => ORDRE.indexOf(a.type_source) - ORDRE.indexOf(b.type_source));

  return (
    <div className="max-w-[1180px] px-4 py-6 lg:px-6">
      <h1 className="text-[26px] font-bold leading-tight">{t.sourcesTitre}</h1>
      {stats && (
        <p className="mt-1 text-texte-2">
          {t.sourcesResume(stats.total_documents, stats.total_chunks, stats.par_statut_verification.verifie || 0, stats.par_statut_verification.a_verifier || 0)}
        </p>
      )}
      {erreur && (
        <p role="alert" className="mt-4 border-l-[3px] border-erreur bg-erreur-clair px-3 py-2 text-erreur">
          {t.sourcesIndisponibles}
        </p>
      )}
      {tries.length > 0 && (
        <div className="mt-5 overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="border-b-2 border-texte text-sm">
                <th className="py-2 pr-4">{t.colonnesSources.document}</th>
                <th className="py-2 pr-4">{t.colonnesSources.type}</th>
                <th className="py-2 pr-4 text-right">{t.colonnesSources.extraits}</th>
                <th className="py-2">{t.colonnesSources.verification}</th>
              </tr>
            </thead>
            <tbody>
              {tries.map((d) => (
                <tr key={d.doc} className="border-b border-ligne align-top hover:bg-fond">
                  <td className="min-w-[260px] py-2 pr-4">
                    <a href={d.source_url} target="_blank" rel="noopener noreferrer" className="font-medium text-accent underline-offset-2 hover:underline">
                      {d.titre}
                      <span className="sr-only"> ({t.ouvrirSource})</span>
                      <Icone nom="externe" taille={13} className="ml-1 align-[-1px]" />
                    </a>
                  </td>
                  <td className="whitespace-nowrap py-2 pr-4 text-sm text-texte-2">{t.typesSource[d.type_source]}</td>
                  <td className="py-2 pr-4 text-right text-sm tabular-nums">{d.chunks}</td>
                  <td className="py-2 text-sm">
                    <Etat ton={d.statut_verification === "verifie" ? "ok" : "attention"}>{d.statut_verification === "verifie" ? t.verifie : t.aVerifier}</Etat>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
