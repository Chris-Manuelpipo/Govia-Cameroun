"use client";
import { Fragment, ReactNode, useMemo } from "react";
import { dureeTexte, useRevelation } from "../lib/revelation";

const SAUT = "\u0001";

/** Nettoie ce que les modèles ajoutent volontiers : HTML, émojis, repères exotiques. Rien n'est jamais interprété comme HTML. */
function nettoyer(texte: string): string {
  return texte
    .replace(/<br\s*\/?>/gi, SAUT)
    .replace(/<\/?[a-z][^>]*>/gi, "")
    .replace(/([0-9])️?⃣/g, "$1.")
    .replace(/[#*]️?⃣/g, "")
    .replace(/\p{Extended_Pictographic}|️|‍/gu, "")
    .replace(/【([^】]*)】/g, "[$1]")
    .replace(/\r/g, "");
}

/** Gras et repères de source entre crochets (en retrait visuel). */
function enLigne(texte: string): ReactNode[] {
  return texte.split(SAUT).flatMap((ligne, k) => {
    const morceaux = ligne.split(/(\*\*[^*\n]+\*\*|\[[^\]\n]{2,90}\])/g).map((m, i) => {
      if (m.startsWith("**") && m.endsWith("**") && m.length > 4) return <strong key={i}>{m.slice(2, -2)}</strong>;
      if (m.startsWith("[") && m.endsWith("]")) return <span key={i} className="text-[0.88em] text-texte-2">{m}</span>;
      return <Fragment key={i}>{m}</Fragment>;
    });
    return k === 0 ? morceaux : [<br key={`br${k}`} />, ...morceaux];
  });
}

const estLigneTableau = (l: string) => /^\s*\|.*\|\s*$/.test(l);
const estSeparateur = (l: string) => /^\s*\|?[\s:|-]+\|?\s*$/.test(l) && l.includes("-");
const cellules = (l: string) => l.trim().replace(/^\||\|$/g, "").split("|").map((c) => c.trim());

/** Rendu markdown minimal et sûr : titres, listes, tableaux, gras. Tolère un texte coupé en cours de route. */
export function Markdown({ texte }: { texte: string }) {
  const blocs = useMemo(() => {
    const lignes = nettoyer(texte).split("\n");
    const sortie: ReactNode[] = [];
    let i = 0;
    let cle = 0;
    while (i < lignes.length) {
      const l = lignes[i];
      if (!l.trim() || /^\s*([-*_])\1{2,}\s*$/.test(l)) {
        i++;
      } else if (/^\s*#{1,6}\s+/.test(l)) {
        sortie.push(<h3 key={cle++} className="pt-1 text-[16px] font-bold text-titre">{enLigne(l.replace(/^\s*#{1,6}\s+/, ""))}</h3>);
        i++;
      } else if (estLigneTableau(l)) {
        const lot: string[] = [];
        while (i < lignes.length && estLigneTableau(lignes[i])) lot.push(lignes[i++]);
        const sansSeparateur = lot.filter((x) => !estSeparateur(x));
        const [entete, ...corps] = sansSeparateur;
        sortie.push(
          <div key={cle++} className="overflow-x-auto border border-ligne">
            <table className="w-full border-collapse text-[14px]">
              <thead>
                <tr className="bg-fond">
                  {cellules(entete).map((c, j) => (
                    <th key={j} className="border-b border-ligne px-3 py-2 align-top">{enLigne(c)}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {corps.map((r, k) => (
                  <tr key={k} className="border-b border-ligne last:border-b-0">
                    {cellules(r).map((c, j) => (
                      <td key={j} className={`px-3 py-2 align-top ${j === 0 ? "font-semibold" : ""}`}>{enLigne(c)}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>,
        );
      } else if (/^\s*([-*•])\s+/.test(l) || /^\s*\d+[.)]\s+/.test(l)) {
        const ordonnee = /^\s*\d+[.)]\s+/.test(l);
        const motif = ordonnee ? /^\s*\d+[.)]\s+/ : /^\s*[-*•]\s+/;
        const items: string[] = [];
        while (i < lignes.length && motif.test(lignes[i])) items.push(lignes[i++].replace(motif, ""));
        const Liste = ordonnee ? "ol" : "ul";
        sortie.push(
          <Liste key={cle++} className={`space-y-1 pl-5 ${ordonnee ? "list-decimal" : "list-disc"}`}>
            {items.map((it, k) => <li key={k}>{enLigne(it)}</li>)}
          </Liste>,
        );
      } else {
        const lot: string[] = [];
        while (i < lignes.length && lignes[i].trim() && !estLigneTableau(lignes[i]) && !/^\s*(#{1,6}\s|[-*•]\s|\d+[.)]\s)/.test(lignes[i])) lot.push(lignes[i++]);
        sortie.push(<p key={cle++}>{enLigne(lot.join(SAUT))}</p>);
      }
    }
    return sortie;
  }, [texte]);

  return <div className="space-y-3">{blocs}</div>;
}

/** Texte du modèle : rendu en markdown et révélé progressivement (déjà validé par l'auditeur). */
export function MarkdownProgressif({ texte, anime, onFini }: { texte: string; anime: boolean; onFini: () => void }) {
  const jetons = useMemo(() => texte.split(/(\s+)/), [texte]);
  const n = useRevelation(jetons.length, anime, onFini, dureeTexte(jetons.length));
  return (
    <div data-progressif={anime ? "" : undefined}>
      <Markdown texte={anime ? jetons.slice(0, n).join("") : texte} />
    </div>
  );
}
