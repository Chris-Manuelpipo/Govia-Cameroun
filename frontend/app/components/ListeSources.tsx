"use client";
import { useState } from "react";
import { Langue, TEXTES } from "../i18n";
import { DocumentSource, Stats } from "../types";
import { Etat, Icone } from "./icones";
import { chiffres, Statistiques } from "./Statistiques";

const ORDRE: DocumentSource["type_source"][] = ["texte_officiel", "reproduction", "portail_institutionnel"];
type Verification = "tous" | "verifie" | "a_verifier";

const estLien = (url: string) => /^https?:\/\//i.test(url);

/** Adresse lisible : domaine et chemin, sans protocole. */
function adresse(url: string) {
  try {
    const { host, pathname } = new URL(url);
    return host.replace(/^www\./, "") + (pathname === "/" ? "" : pathname);
  } catch {
    return url;
  }
}

const normaliser = (texte: string) =>
  texte
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase();

export function ListeSources({ documents, stats, erreur, langue }: { documents: DocumentSource[]; stats: Stats | null; erreur: boolean; langue: Langue }) {
  const t = TEXTES[langue];
  const [requete, setRequete] = useState("");
  const [type, setType] = useState<"tous" | DocumentSource["type_source"]>("tous");
  const [verification, setVerification] = useState<Verification>("tous");

  const chiffresBase = chiffres(stats, documents);
  const par = (type_source: DocumentSource["type_source"]) => documents.filter((d) => d.type_source === type_source).length;

  const recherche = normaliser(requete.trim());
  const visibles = [...documents]
    .sort((a, b) => ORDRE.indexOf(a.type_source) - ORDRE.indexOf(b.type_source))
    .filter((d) => (type === "tous" || d.type_source === type) && (verification === "tous" || (verification === "verifie") === (d.statut_verification === "verifie")))
    .filter((d) => !recherche || normaliser(`${d.titre} ${adresse(d.source_url)}`).includes(recherche));

  return (
    <div className="mx-auto max-w-[1280px] px-4 py-6 lg:px-6">
      <h1 className="text-[26px] font-bold leading-tight text-marine">{t.sourcesPageTitre}</h1>
      <p className="mt-1 max-w-[760px] text-texte-2">{t.sourcesIntro}</p>

      {erreur && (
        <p role="alert" className="mt-4 border-l-4 border-erreur bg-erreur-clair px-3 py-2 text-erreur">
          {t.sourcesIndisponibles}
        </p>
      )}

      {chiffresBase && (
        <div className="mt-5">
          <Statistiques chiffres={chiffresBase} t={t} />
        </div>
      )}

      {documents.length > 0 && (
        <>
          <div className="mt-6 grid gap-3 md:grid-cols-[minmax(0,1fr)_220px_200px]">
            <label className="block">
              <span className="mb-1 block text-sm font-semibold">{t.filtreTitre}</span>
              <span className="relative block">
                <Icone nom="loupe" taille={18} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-texte-2" />
                <input type="search" value={requete} onChange={(e) => setRequete(e.target.value)} className="h-11 w-full border border-ligne-forte bg-surface pl-10 pr-3" />
              </span>
            </label>
            <label className="block">
              <span className="mb-1 block text-sm font-semibold">{t.filtreType}</span>
              <select value={type} onChange={(e) => setType(e.target.value as typeof type)} className="h-11 w-full border border-ligne-forte bg-surface px-2.5">
                <option value="tous">
                  {t.tousTypes} ({documents.length})
                </option>
                {ORDRE.map((o) => (
                  <option key={o} value={o}>
                    {t.typesPluriel[o]} ({par(o)})
                  </option>
                ))}
              </select>
            </label>
            <label className="block">
              <span className="mb-1 block text-sm font-semibold">{t.filtreVerification}</span>
              <select value={verification} onChange={(e) => setVerification(e.target.value as Verification)} className="h-11 w-full border border-ligne-forte bg-surface px-2.5">
                <option value="tous">{t.toutesVerifications}</option>
                <option value="verifie">{t.verifie}</option>
                <option value="a_verifier">{t.aVerifier}</option>
              </select>
            </label>
          </div>
          <p className="mt-3 text-sm text-texte-2" aria-live="polite">
            {t.documentsN(visibles.length)}
          </p>
          <p className="mt-0.5 text-[13px] text-texte-2">{t.typesAide}</p>
        </>
      )}

      {documents.length > 0 && (
        <div className="mt-2 overflow-x-auto border border-ligne bg-surface">
          <table className="w-full border-collapse">
            <caption className="sr-only">{t.sourcesPageTitre}</caption>
            <thead>
              <tr className="border-b-2 border-marine text-sm">
                <th scope="col" className="px-3 py-2.5">
                  {t.colonnesSources.document}
                </th>
                <th scope="col" className="hidden px-3 py-2.5 md:table-cell">
                  {t.colonnesSources.type}
                </th>
                <th scope="col" className="hidden px-3 py-2.5 text-right sm:table-cell">
                  {t.colonnesSources.extraits}
                </th>
                <th scope="col" className="px-3 py-2.5">
                  {t.colonnesSources.verification}
                </th>
              </tr>
            </thead>
            <tbody>
              {visibles.map((d) => {
                const verifie = d.statut_verification === "verifie";
                return (
                  <tr key={d.doc} className="border-b border-ligne align-top last:border-b-0 hover:bg-fond">
                    <td className="min-w-[250px] px-3 py-2">
                      {estLien(d.source_url) ? (
                        <a
                          href={d.source_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex min-h-[44px] items-start gap-1 py-1.5 font-medium text-accent underline-offset-2 hover:underline"
                        >
                          <span>
                            {d.titre}
                            <span className="sr-only"> ({t.ouvrirSource})</span>
                          </span>
                          <Icone nom="externe" taille={13} className="mt-1.5" />
                        </a>
                      ) : (
                        <p className="py-1.5 font-medium">{d.titre}</p>
                      )}
                      <p title={d.source_url} className="-mt-1 max-w-[560px] truncate text-[13px] text-texte-2">
                        {adresse(d.source_url)}
                      </p>
                      <p className="mt-1 text-[13px] text-texte-2 md:hidden">{t.typesSource[d.type_source]}</p>
                    </td>
                    <td className="hidden whitespace-nowrap px-3 py-3 text-sm text-texte-2 md:table-cell">{t.typesSource[d.type_source]}</td>
                    <td className="hidden px-3 py-3 text-right text-sm tabular-nums sm:table-cell">{d.chunks}</td>
                    <td className="px-3 py-3 text-sm">
                      <span className="whitespace-nowrap">
                        <Etat ton={verifie ? "ok" : "attention"}>{verifie ? t.verifie : t.aVerifier}</Etat>
                      </span>
                      {!verifie && d.methode_verification && <p className="mt-1 max-w-[320px] text-[13px] text-texte-2">{d.methode_verification}</p>}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          {visibles.length === 0 && <p className="px-3 py-4 text-texte-2">{t.aucunDocument}</p>}
        </div>
      )}
    </div>
  );
}
