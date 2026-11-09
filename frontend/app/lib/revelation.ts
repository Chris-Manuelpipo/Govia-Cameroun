"use client";
import { useEffect, useRef, useState } from "react";

/**
 * Révèle progressivement `total` éléments (mots, blocs) d'un contenu déjà validé par l'auditeur.
 * Rend le nombre d'éléments à montrer. Sans animation (réponse déjà lue, ou « réduire les animations »),
 * tout est montré d'emblée ; `onFini` est appelé une fois la révélation terminée.
 */
export function useRevelation(total: number, anime: boolean, onFini: () => void, dureeMs: number, intervalleMs = 30): number {
  const [n, setN] = useState(0);
  const fin = useRef(onFini);
  fin.current = onFini;

  useEffect(() => {
    if (!anime) return;
    if (total === 0 || window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      fin.current();
      return;
    }
    const pas = Math.max(1, Math.ceil(total / (dureeMs / intervalleMs)));
    let i = 0;
    const id = setInterval(() => {
      i = Math.min(total, i + pas);
      setN(i);
      if (i >= total) {
        clearInterval(id);
        fin.current();
      }
    }, intervalleMs);
    return () => clearInterval(id);
  }, [anime, total, dureeMs, intervalleMs]);

  return anime ? n : total;
}

/** Durée d'affichage d'un texte : proportionnelle à sa longueur, bornée à 2,6 s. */
export const dureeTexte = (jetons: number) => Math.min(2600, Math.max(500, (jetons / 2) * 35));
