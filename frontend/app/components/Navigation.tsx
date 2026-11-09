"use client";
import { Textes } from "../i18n";
import { Vue } from "../types";
import { Icone, NomIcone } from "./icones";

const ONGLETS: { id: Vue; icone: NomIcone }[] = [
  { id: "demarches", icone: "liste" },
  { id: "assistant", icone: "dialogue" },
  { id: "sources", icone: "document" },
  { id: "donnees", icone: "bouclier" },
];

/** Quatre onglets de même poids. Le libellé complet apparaît dès la tablette ; un libellé court sur mobile. */
export function Navigation({ vue, t, onVue }: { vue: Vue; t: Textes; onVue: (v: Vue) => void }) {
  return (
    <nav aria-label={t.navigation} className="sticky top-0 z-30 shrink-0 border-b border-ligne bg-surface">
      <ul className="mx-auto flex max-w-[1280px] px-1 sm:px-4 lg:px-6">
        {ONGLETS.map(({ id, icone }) => {
          const actif = vue === id;
          return (
            <li key={id} className="flex-1 sm:flex-none">
              <button
                onClick={() => onVue(id)}
                aria-current={actif ? "page" : undefined}
                className={`flex min-h-[54px] w-full flex-col items-center justify-center gap-0.5 border-b-[3px] px-1 text-[13px] sm:min-h-[48px] sm:flex-row sm:gap-2 sm:px-5 sm:text-[15px] ${
                  actif ? "border-accent font-semibold text-marine" : "border-transparent text-texte-2 hover:bg-fond hover:text-texte"
                }`}
              >
                <Icone nom={icone} taille={18} />
                <span className="sm:hidden">{t.vues[id]}</span>
                <span className="hidden sm:inline">{t.vuesLongues[id]}</span>
              </button>
            </li>
          );
        })}
        {/* La réserve d'usage reste visible sur grand écran, sans prendre de hauteur. */}
        <li className="ml-auto hidden max-w-[400px] items-center gap-2 pl-6 text-[12px] leading-snug text-texte-2 xl:flex">
          <Icone nom="info" taille={16} className="shrink-0" />
          {t.prototypeTexte}
        </li>
      </ul>
    </nav>
  );
}
