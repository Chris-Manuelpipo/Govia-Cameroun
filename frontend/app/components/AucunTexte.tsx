"use client";
import { useId, useMemo, useState } from "react";
import { Textes } from "../i18n";
import { copierTexte } from "../lib/presse-papiers";
import { analyserLacune } from "../lib/reponse";
import { Message } from "../types";
import { Icone } from "./icones";

/** Plusieurs démarches du catalogue n'ont pas encore d'administration établie : la base dit « À identifier ». */
const NON_IDENTIFIEE = /^\s*[àa]\s+identifier/i;
const estLien = (url: string) => /^https?:\/\//i.test(url);

/**
 * État « Aucun texte ouvert trouvé ». GOVIA le dit plutôt que de donner une réponse approximative,
 * puis oriente : l'administration indiquée par la base quand elle existe, des services où se renseigner,
 * et les questions à poser. Aucune coordonnée n'est inventée.
 */
export function AucunTexte({ message, t, onAutreQuestion }: { message: Message; t: Textes; onAutreQuestion: () => void }) {
  const id = useId();
  const [contact, setContact] = useState(false);
  const [copie, setCopie] = useState(false);

  const lacune = message.type === "lacune";
  const analyse = useMemo(() => (lacune ? analyserLacune(message.content) : null), [lacune, message.content]);
  const demarche = message.procedure || analyse?.titre || null;
  const administration = analyse?.autorite && !NON_IDENTIFIEE.test(analyse.autorite) ? analyse.autorite : null;

  const etapes = [
    administration ? t.aucunTexte.etapeAdministration(administration) : t.aucunTexte.etapeIdentifier,
    t.aucunTexte.etapeOrienter,
    t.aucunTexte.etapeTexte,
  ];

  async function copier() {
    const lignes = [demarche ? `${t.aucunTexte.demarche} : ${demarche}` : "", ...t.aucunTexte.questions.map((q, i) => `${i + 1}. ${q}`)].filter(Boolean);
    if (await copierTexte(lignes.join("\n"))) {
      setCopie(true);
      setTimeout(() => setCopie(false), 1800);
    }
  }

  return (
    <div className="flex min-h-full items-center justify-center px-4 py-8 lg:px-8">
      <section aria-labelledby={`${id}-titre`} className="w-full max-w-[640px] border border-ligne bg-surface">
        <div className="px-6 pb-6 pt-12 text-center">
          <span className="mx-auto grid h-24 w-24 place-items-center rounded-full border border-ligne bg-fond text-texte-2">
            <Icone nom="document" taille={46} epaisseur={1.5} />
          </span>
          <h1 id={`${id}-titre`} className="mt-6 text-balance text-[24px] font-bold leading-tight text-titre">
            {t.aucunTexte.titre}
          </h1>
        </div>

        {/* Encadré de transparence */}
        <div className="px-6 pb-6">
          <div className="border-2 border-ok bg-ok-clair px-4 py-3">
            <h2 className="flex items-center gap-2 font-bold text-ok-fonce">
              <Icone nom="bouclier" taille={18} />
              {t.aucunTexte.transparenceTitre}
            </h2>
            <p className="mt-1 text-texte">{t.aucunTexte.transparence}</p>
          </div>
        </div>

        {analyse?.guide && (
          <p className="flex items-start gap-2 border-t border-ligne px-6 py-3 text-[14px]">
            <Icone nom="alerte" taille={16} className="mt-1 shrink-0 text-attention-vif" />
            {estLien(analyse.guide) ? (
              <a href={analyse.guide} target="_blank" rel="noopener noreferrer" className="text-accent underline underline-offset-2">
                {t.aucunTexte.guide}
                <Icone nom="externe" taille={13} className="ml-1 align-[-1px]" />
              </a>
            ) : (
              <span>{t.aucunTexte.guide}</span>
            )}
          </p>
        )}

        <div className="border-t border-ligne px-6 py-4">
          <h2 className="font-semibold">{t.aucunTexte.etapesTitre}</h2>
          <ol className="mt-2 space-y-2">
            {etapes.map((etape, i) => (
              <li key={etape} className="grid grid-cols-[1.75rem_minmax(0,1fr)]">
                <span className="font-semibold tabular-nums text-texte-2">{i + 1}.</span>
                <span>{etape}</span>
              </li>
            ))}
          </ol>
        </div>

        <div className="flex flex-wrap gap-3 border-t border-ligne px-6 py-4">
          <button onClick={onAutreQuestion} className="min-h-[44px] bg-bouton px-5 font-semibold text-white hover:bg-bouton-fonce">
            {t.aucunTexte.autreQuestion}
          </button>
          <button
            onClick={() => setContact((ouvert) => !ouvert)}
            aria-expanded={contact}
            aria-controls={`${id}-contact`}
            className="inline-flex min-h-[44px] items-center gap-2 border border-ligne-forte px-5 font-medium hover:bg-fond"
          >
            {t.aucunTexte.contacter}
            <Icone nom="chevron-bas" taille={16} className={contact ? "rotate-180" : ""} />
          </button>
        </div>

        {contact && (
          <div id={`${id}-contact`} className="border-t border-ligne bg-fond px-6 py-4">
            <h2 className="flex items-center gap-2 font-semibold">
              <Icone nom="batiment" taille={18} className="text-titre" />
              {t.aucunTexte.contactTitre}
            </h2>
            <ol className="mt-2 list-decimal space-y-1 pl-5">
              {t.aucunTexte.questions.map((question) => (
                <li key={question}>{question}</li>
              ))}
            </ol>
            <p className="mt-2 text-[13px] text-texte-2">{t.aucunTexte.contactNote}</p>
            <button onClick={copier} className="mt-3 inline-flex min-h-[44px] items-center gap-2 border border-ligne-forte bg-surface px-4 font-medium hover:bg-fond">
              <Icone nom="copier" taille={16} />
              {copie ? t.aucunTexte.copie : t.aucunTexte.copier}
            </button>
          </div>
        )}

      </section>
    </div>
  );
}
