"use client";
import { DocumentCite } from "../lib/confiance";
import { Textes } from "../i18n";
import { Etat, Icone } from "./icones";

const estLien = (url: string) => /^https?:\/\//i.test(url);

/**
 * Pied « Sources » d'une réponse : chaque document cité, son lien et son état de vérification.
 * En version compacte (bulle du fil), une ligne par document ; sinon le type et les articles cités s'ajoutent.
 */
export function SourcesCitees({
  documents,
  t,
  max,
  compact = false,
  onTout,
  className = "",
}: {
  documents: DocumentCite[];
  t: Textes;
  /** Au-delà, le bloc se limite aux premiers documents et propose d'ouvrir la fiche. */
  max?: number;
  compact?: boolean;
  onTout?: () => void;
  className?: string;
}) {
  if (!documents.length) return null;
  const montres = max ? documents.slice(0, max) : documents;
  const reste = documents.length - montres.length;

  return (
    <section aria-label={t.sourcesCitees(documents.length)} className={`border-t border-ligne bg-fond ${className}`}>
      <p className="px-3 pb-0.5 pt-2 text-[12px] font-semibold text-texte-2">{t.sourcesCitees(documents.length)}</p>
      <ul className="divide-y divide-ligne">
        {montres.map((d) => (
          <li key={d.cle} className="px-3">
            <div className={`flex gap-2 ${compact ? "items-center" : "items-start"}`}>
              {estLien(d.url) ? (
                <a
                  href={d.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex min-h-[44px] min-w-0 flex-1 items-center gap-1.5 py-1.5 font-medium text-accent underline-offset-2 hover:underline"
                >
                  <span className={`text-[14px] leading-snug ${compact ? "line-clamp-2" : ""}`}>
                    {d.titre}
                    <span className="sr-only"> ({t.ouvrirSource})</span>
                  </span>
                  <Icone nom="externe" taille={13} className="shrink-0" />
                </a>
              ) : (
                <p className="min-w-0 flex-1 py-3 text-[14px] font-medium leading-snug">{d.titre}</p>
              )}
              {compact && (
                <span title={d.verifie ? t.verifie : t.aVerifier} className="shrink-0">
                  <Etat ton={d.verifie ? "ok" : "attention"} taille={16}>
                    <span className="sr-only">{d.verifie ? t.verifie : t.aVerifier}</span>
                  </Etat>
                </span>
              )}
            </div>
            {!compact && (
              <p className="flex flex-wrap items-center gap-x-3 pb-1.5 text-[13px] text-texte-2">
                <span>
                  {t.typesSource[d.type]}
                  {d.articles.length > 0 && (
                    <span>
                      {" "}
                      · {d.articles.slice(0, 2).join(" ; ")}
                      {d.articles.length > 2 ? "…" : ""}
                    </span>
                  )}
                </span>
                <span className="text-texte">
                  <Etat ton={d.verifie ? "ok" : "attention"} taille={14}>
                    {d.verifie ? t.verifie : t.aVerifier}
                  </Etat>
                </span>
              </p>
            )}
          </li>
        ))}
      </ul>
      {reste > 0 && onTout && (
        <button
          onClick={onTout}
          className="flex min-h-[44px] w-full items-center justify-between border-t border-ligne px-3 text-left text-[14px] font-medium text-accent hover:bg-surface"
        >
          {t.voirToutesSources(documents.length)}
          <Icone nom="envoyer" taille={15} />
        </button>
      )}
    </section>
  );
}
