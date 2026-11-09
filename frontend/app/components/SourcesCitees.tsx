"use client";
import { DocumentCite } from "../lib/confiance";
import { Textes } from "../i18n";
import { Etat, Icone } from "./icones";

const estLien = (url: string) => /^https?:\/\//i.test(url);

/**
 * Pied « Sources » d'une réponse : chaque document cité, son lien, son type et son état de vérification.
 * Texte de 14 px et cibles de 44 px : ce n'est pas une note de bas de page.
 */
export function SourcesCitees({
  documents,
  t,
  max,
  onTout,
  className = "",
}: {
  documents: DocumentCite[];
  t: Textes;
  /** Au-delà, le bloc se limite aux premiers documents et propose d'ouvrir la fiche. */
  max?: number;
  onTout?: () => void;
  className?: string;
}) {
  if (!documents.length) return null;
  const montres = max ? documents.slice(0, max) : documents;
  const reste = documents.length - montres.length;

  return (
    <section aria-label={t.sourcesCitees(documents.length)} className={`border-t border-ligne bg-fond ${className}`}>
      <div className="flex items-center gap-1.5 px-3 pb-1 pt-2.5 text-[12px] font-bold uppercase tracking-wider text-texte-2">
        <Icone nom="document" taille={14} />
        {t.sourcesCitees(documents.length)}
      </div>
      <ul className="divide-y divide-ligne">
        {montres.map((d) => (
          <li key={d.cle} className="px-3 py-1">
            {estLien(d.url) ? (
              <a
                href={d.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex min-h-[44px] items-start gap-1.5 py-1.5 font-medium text-accent underline-offset-2 hover:underline"
              >
                <span className="line-clamp-2 text-[14px] leading-snug">
                  {d.titre}
                  <span className="sr-only"> ({t.ouvrirSource})</span>
                </span>
                <Icone nom="externe" taille={13} className="mt-1" />
              </a>
            ) : (
              <p className="py-1.5 text-[14px] font-medium leading-snug">{d.titre}</p>
            )}
            <p className="flex flex-wrap items-center gap-x-3 pb-1.5 text-[13px] text-texte-2">
              <span>
                {t.typesSource[d.type]}
                {d.articles.length > 0 && <span className="extrait-exact"> · {d.articles.slice(0, 2).join(" ; ")}{d.articles.length > 2 ? "…" : ""}</span>}
              </span>
              <span className="text-texte">
                <Etat ton={d.verifie ? "ok" : "attention"} taille={14}>
                  {d.verifie ? t.verifie : t.aVerifier}
                </Etat>
              </span>
            </p>
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
