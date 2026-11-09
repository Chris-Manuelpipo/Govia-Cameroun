"use client";
import { useEffect, useState } from "react";
import { Langue, Textes } from "../i18n";
import { Etoile, Icone, Marque } from "./icones";

/** Bande aux couleurs nationales : vert, rouge, jaune, avec l'étoile au centre de la bande rouge. */
function BandeTricolore() {
  return (
    <div className="relative flex h-4" aria-hidden="true">
      <span className="flex-1 bg-vert" />
      <span className="flex-1 bg-rouge" />
      <span className="flex-1 bg-jaune" />
      <Etoile className="absolute left-1/2 top-1/2 h-3 w-3 -translate-x-1/2 -translate-y-1/2 text-jaune" />
    </div>
  );
}

/** Clair ou sombre : le choix de l'utilisateur est gardé sur cet appareil ; sans choix, le réglage du système prévaut. */
function BasculeTheme({ t }: { t: Textes }) {
  const [sombre, setSombre] = useState(false);
  useEffect(() => setSombre(document.documentElement.dataset.theme === "dark"), []);

  function basculer() {
    const suivant = sombre ? "light" : "dark";
    document.documentElement.dataset.theme = suivant;
    setSombre(!sombre);
    try {
      localStorage.setItem("govia-theme", suivant);
    } catch {
      // Stockage refusé : le thème vaut pour cette page seulement.
    }
  }

  const libelle = sombre ? t.passerClair : t.passerSombre;
  return (
    <button onClick={basculer} aria-label={libelle} title={libelle} className="grid h-11 w-11 place-items-center border border-white/50 text-white hover:bg-white/15">
      <Icone nom={sombre ? "soleil" : "lune"} taille={19} />
    </button>
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
        <div className="mx-auto grid max-w-[1280px] grid-cols-[1fr_auto] items-center lg:grid-cols-[1fr_auto_1fr] gap-x-2 gap-y-1.5 px-3 py-2 sm:gap-x-4 sm:px-4 lg:px-6 lg:py-2.5">
          {/* Devises, dans les deux langues quelle que soit la langue choisie. Sous le logo sur mobile. */}
          <div className="order-last col-span-2 text-left text-[11.5px] leading-[1.35] lg:order-none lg:col-span-1 lg:col-start-1 lg:row-start-1 lg:text-left lg:text-[12px]">
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
            <p className="text-[17px] font-bold uppercase leading-none tracking-wide sm:text-[20px]">
              GOVIA <span className="font-medium normal-case tracking-normal">Cameroun</span>
            </p>
          </div>

          {/* Sélecteur de langue, en haut à droite : visible partout, jamais imposé */}
          <div className="flex items-center justify-end gap-2 lg:col-start-3 lg:row-start-1">
            <BasculeTheme t={t} />
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
