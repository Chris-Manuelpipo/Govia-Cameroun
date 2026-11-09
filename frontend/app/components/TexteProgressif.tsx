"use client";
import { useMemo } from "react";
import { dureeTexte, useRevelation } from "../lib/revelation";

/**
 * Affiche un texte déjà validé mot à mot, comme les assistants qui répondent en direct.
 * L'auditeur contrôle la réponse entière avant tout affichage : on ne montre jamais de texte brut du modèle.
 */
export function TexteProgressif({ texte, anime, onFini }: { texte: string; anime: boolean; onFini: () => void }) {
  const jetons = useMemo(() => texte.split(/(\s+)/), [texte]);
  const n = useRevelation(jetons.length, anime, onFini, dureeTexte(jetons.length));
  // L'annonce vocale de la réponse passe par la zone d'état de l'assistant : le texte partiel est masqué aux lecteurs d'écran.
  return (
    <span aria-hidden={anime ? true : undefined} data-progressif={anime ? "" : undefined}>
      {anime ? jetons.slice(0, n).join("") : texte}
    </span>
  );
}
