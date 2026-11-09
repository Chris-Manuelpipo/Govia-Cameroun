"use client";
import { useId, useState } from "react";
import { Textes } from "../i18n";
import { Message } from "../types";
import { Icone } from "./icones";

/** La partie avant le premier « : » (le motif de la question) est mise en gras. */
function Motif({ texte }: { texte: string }) {
  const coupe = texte.indexOf(" : ");
  if (coupe < 0) return <>{texte}</>;
  return (
    <>
      <strong className="font-semibold text-texte">{texte.slice(0, coupe)} :</strong>
      {texte.slice(coupe + 2)}
    </>
  );
}

/**
 * État « Précision requise » : l'agent ne devine pas. Une carte sobre, centrée, des options à choisir,
 * et un bouton « Continuer » inactif tant qu'aucune option n'est retenue.
 * Une précision déjà apportée reste affichée, en lecture seule, avec le choix qui a été fait.
 */
export function Precision({
  message,
  reponduePar,
  occupe,
  t,
  onChoisir,
  onReformuler,
}: {
  message: Message;
  /** Texte envoyé en réponse à cette question, s'il existe déjà. */
  reponduePar: string | null;
  occupe: boolean;
  t: Textes;
  onChoisir: (texte: string) => void;
  onReformuler: () => void;
}) {
  const id = useId();
  const [choix, setChoix] = useState<string | null>(null);
  const options = message.options || [];
  const fige = reponduePar !== null;
  const selection = fige ? options.find((o) => o.message === reponduePar)?.message ?? null : choix;
  const peutContinuer = !!selection && !fige && !occupe;

  return (
    <div className="flex min-h-full items-center justify-center px-4 py-8 lg:px-8">
      <section aria-labelledby={`${id}-titre`} className="w-full max-w-[580px] border border-ligne bg-surface">
        <div className="px-6 pb-4 pt-6 text-center">
          <span className="mx-auto grid h-14 w-14 place-items-center rounded-full bg-jaune text-marine">
            <Icone nom="interrogation" taille={30} epaisseur={2.4} />
          </span>
          <p className="mt-2.5 text-[12px] font-bold uppercase tracking-wider text-texte-2">{t.precision.surtitre}</p>
          <h1 id={`${id}-titre`} className="mt-1 text-balance text-[22px] font-bold leading-snug text-marine">
            {t.precision.titre}
          </h1>
          {message.procedure && <p className="mt-1.5 text-texte-2">{message.procedure}</p>}
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (peutContinuer && selection) onChoisir(selection);
          }}
        >
          <div className="border-t border-ligne px-6 py-3.5">
            <fieldset disabled={fige || occupe}>
              <legend className="mb-2.5 font-semibold">{message.content || t.precision.choisir}</legend>
              <div className={`grid gap-2 ${options.length > 4 ? "sm:grid-cols-2" : ""}`}>
                {options.map((o) => {
                  const actif = selection === o.message;
                  return (
                    <label key={o.message} className="relative block">
                      <input type="radio" name={`${id}-option`} value={o.message} checked={actif} onChange={() => setChoix(o.message)} className="peer sr-only" />
                      <span
                        className={`flex min-h-[48px] cursor-pointer items-center justify-between gap-3 border px-3.5 py-2 font-medium peer-focus-visible:outline peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-accent peer-disabled:cursor-not-allowed ${
                          actif ? "border-accent bg-accent-clair text-accent-fonce outline outline-1 outline-accent" : "border-ligne-forte bg-surface hover:bg-fond"
                        }`}
                      >
                        {o.libelle}
                        <span aria-hidden="true" className={`grid h-5 w-5 shrink-0 place-items-center rounded-full border-2 ${actif ? "border-accent bg-accent text-white" : "border-ligne-forte"}`}>
                          {actif && <Icone nom="coche" taille={12} epaisseur={3.5} />}
                        </span>
                      </span>
                    </label>
                  );
                })}
              </div>
            </fieldset>
          </div>

          <div className="sticky bottom-0 z-10 flex flex-wrap items-center gap-x-4 gap-y-1 border-t border-ligne bg-surface px-6 py-3">
            <button
              type="submit"
              disabled={!peutContinuer}
              aria-describedby={!selection && !fige ? `${id}-aide` : undefined}
              className="inline-flex min-h-[44px] min-w-[150px] items-center justify-center gap-2 bg-accent px-5 font-semibold text-white hover:bg-accent-fonce disabled:cursor-not-allowed disabled:bg-[#e3e6ea] disabled:text-[#55606d] disabled:hover:bg-[#e3e6ea]"
            >
              {occupe && <span className="indicateur-chargement" aria-hidden="true" />}
              {t.precision.continuer}
            </button>
            {fige ? (
              // Si la réponse a été saisie à la main plutôt que choisie ici, on ne prétend pas qu'elle correspond à une option.
              selection && <span className="text-[14px] font-medium text-ok-fonce">{t.precision.repondue}</span>
            ) : (
              <>
                {!selection && (
                  <span id={`${id}-aide`} className="text-[14px] text-texte-2">
                    {t.precision.aide}
                  </span>
                )}
                <button type="button" onClick={onReformuler} className="ml-auto min-h-[44px] text-accent underline underline-offset-2">
                  {t.precision.reformuler}
                </button>
              </>
            )}
          </div>
        </form>

        <div className="border-t border-ligne bg-fond px-6 py-4 text-[14px]">
          <h2 className="font-semibold text-texte">{t.precision.pourquoiTitre}</h2>
          <ul className="mt-1.5 space-y-1.5 text-texte-2">
            {t.precision.pourquoi.map((raison) => (
              <li key={raison}>
                <Motif texte={raison} />
              </li>
            ))}
          </ul>
        </div>
        <p className="border-t border-ligne px-6 py-2.5 text-[13px] text-texte-2">
          <span className="font-semibold text-marine">
            {t.regleN(2)} · {t.regles[1].titre}.
          </span>{" "}
          {t.regles[1].texte}
        </p>
      </section>
    </div>
  );
}
