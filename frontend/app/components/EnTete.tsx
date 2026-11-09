"use client";
import { Langue, Textes } from "../i18n";
import { Etoile, Marque } from "./icones";

/** Bande aux couleurs nationales : vert, rouge, jaune, avec l'étoile au centre de la bande rouge. */
function BandeTricolore() {
  return (
    <div className="relative flex h-2.5" aria-hidden="true">
      <span className="flex-1 bg-vert" />
      <span className="flex-1 bg-rouge" />
      <span className="flex-1 bg-jaune" />
      <Etoile className="absolute left-1/2 top-0 h-[17px] w-[17px] -translate-x-1/2 text-jaune" />
    </div>
  );
}

function Prototype({ t, className = "" }: { t: Textes; className?: string }) {
  return (
    <span className={`h-6 items-center border border-jaune px-2 text-[11px] font-bold uppercase tracking-wider text-jaune ${className}`}>{t.prototype}</span>
  );
}

const LANGUES: { code: Langue; nom: string }[] = [
  { code: "FR", nom: "Français" },
  { code: "EN", nom: "English" },
];

export function EnTete({ langue, t, onLangue }: { langue: Langue; t: Textes; onLangue: (l: Langue) => void }) {
  return (
    <header className="sur-marine shrink-0">
      <BandeTricolore />
      <div className="bg-marine text-white">
        <div className="mx-auto grid max-w-[1280px] grid-cols-[1fr_auto_1fr] items-center gap-x-2 gap-y-1.5 px-3 py-2 sm:gap-x-4 sm:px-4 lg:px-6 lg:py-2.5">
          {/* Mention de prototype : à gauche du logo sur mobile, près du sélecteur sur grand écran. */}
          <div className="lg:hidden">
            <Prototype t={t} className="inline-flex" />
          </div>

          {/* Devises, dans les deux langues quelle que soit la langue choisie. Sous le logo sur mobile. */}
          <div className="order-last col-span-3 text-center text-[11.5px] leading-[1.35] lg:order-none lg:col-span-1 lg:col-start-1 lg:row-start-1 lg:text-left lg:text-[12px]">
            <p lang="fr">
              <span className="font-bold uppercase tracking-wide">République du Cameroun</span>
              <span aria-hidden="true" className="mx-1.5 text-sur-marine">
                —
              </span>
              <span className="italic text-sur-marine">Paix – Travail – Patrie</span>
            </p>
            <p lang="en">
              <span className="font-bold uppercase tracking-wide">Republic of Cameroon</span>
              <span aria-hidden="true" className="mx-1.5 text-sur-marine">
                —
              </span>
              <span className="italic text-sur-marine">Peace – Work – Fatherland</span>
            </p>
          </div>

          {/* Logo centré */}
          <div className="flex items-center gap-2.5 lg:col-start-2 lg:row-start-1">
            <Marque taille={36} />
            <div className="leading-none">
              <p className="text-[17px] font-bold uppercase tracking-wide sm:text-[20px]">
                GOVIA <span className="font-medium normal-case tracking-normal">Cameroun</span>
              </p>
              <p className="mt-1 hidden text-[12px] text-sur-marine sm:block">{t.sousTitre}</p>
            </div>
          </div>

          {/* Sélecteur de langue, en haut à droite : visible partout, jamais imposé */}
          <div className="flex items-center justify-end gap-3 lg:col-start-3 lg:row-start-1">
            <Prototype t={t} className="hidden lg:inline-flex" />
            <div role="group" aria-label={t.langue} className="flex border border-white/50">
              {LANGUES.map(({ code, nom }) => (
                <button
                  key={code}
                  lang={code.toLowerCase()}
                  aria-label={nom}
                  aria-pressed={langue === code}
                  onClick={() => onLangue(code)}
                  className={`h-11 min-w-[44px] px-2 text-[14px] ${langue === code ? "bg-white font-bold text-marine" : "text-white hover:bg-white/15"}`}
                >
                  {code}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
