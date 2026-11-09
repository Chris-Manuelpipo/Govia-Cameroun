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
                className={`flex min-h-[48px] w-full items-center justify-center border-b-[3px] px-1 text-[14px] sm:px-5 sm:text-[15px] ${
                  actif ? "border-accent font-semibold text-titre" : "border-transparent text-texte-2 hover:bg-fond hover:text-texte"
                }`}
              >
                <span className="sm:hidden">{t.vues[id]}</span>
                <span className="hidden sm:inline">{t.vuesLongues[id]}</span>
              </button>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
