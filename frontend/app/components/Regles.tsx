"use client";
import { Textes } from "../i18n";

/**
 * Les trois règles d'or, présentes sur chaque écran. Le titre de chaque règle est toujours visible ;
 * sa phrase d'explication apparaît dès que la fenêtre est assez grande et assez haute pour ne pas
 * prendre la place de la conversation (postes de cybercafé en 1366 x 768).
 */
export function Regles({ t }: { t: Textes }) {
  return (
    <section aria-labelledby="regles-titre" className="shrink-0 border-b border-ligne bg-surface">
      <div className="mx-auto flex max-w-[1280px] flex-col gap-x-6 gap-y-1 px-4 py-2 lg:flex-row lg:items-start lg:px-6">
        <p id="regles-titre" className="shrink-0 text-[12px] font-bold uppercase leading-[18px] tracking-wider text-marine">
          {t.reglesTitre}
        </p>
        <ol className="flex flex-1 flex-wrap gap-x-8 gap-y-0.5 sm:[@media(min-height:820px)]:grid sm:[@media(min-height:820px)]:grid-cols-3 sm:[@media(min-height:820px)]:gap-x-6">
          {t.regles.map((regle, i) => (
            <li key={regle.titre} title={regle.texte} className="flex items-start gap-2 text-[13px] leading-[18px]">
              <span aria-hidden="true" className="inline-flex h-[18px] w-[18px] shrink-0 items-center justify-center bg-marine text-[11px] font-bold leading-none text-white">
                {i + 1}
              </span>
              <span>
                <strong className="font-semibold text-texte">{regle.titre}.</strong>
                <span className="hidden text-texte-2 sm:[@media(min-height:820px)]:inline"> {regle.texte}</span>
              </span>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
