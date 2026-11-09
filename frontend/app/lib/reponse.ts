/**
 * Découpe le texte de l'agent pour l'afficher par blocs : pièces, étapes, coût, durée, extraits.
 * Le texte n'est jamais reformulé. Une ligne non reconnue, par exemple dans une rédaction du
 * LLM, reste un paragraphe : l'affichage se dégrade sans rien perdre.
 */
export type Genre = "etapes" | "pieces" | "cout" | "duree" | "extraits" | "sources" | "liste";

export interface Section {
  genre: Genre;
  titre: string;
  items: string[];
}

export interface Analyse {
  titre: string | null;
  cas: string | null;
  alertes: string[];
  paragraphes: string[];
  sections: Section[];
  notes: string[];
}

export interface Groupe {
  nom: string | null;
  items: string[];
}

const sansAccent = (texte: string) =>
  texte
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase();

function genreDe(titre: string): Genre {
  const t = sansAccent(titre);
  if (/^(etapes|steps)/.test(t)) return "etapes";
  if (/^(pieces|documents required)/.test(t)) return "pieces";
  if (/^(cout|cost)/.test(t)) return "cout";
  if (/^(duree|estimated total)/.test(t)) return "duree";
  if (/^(ce que disent|what the texts)/.test(t)) return "extraits";
  if (/^(textes et sources|texts and sources)/.test(t)) return "sources";
  return "liste";
}

export function analyser(contenu: string): Analyse {
  const analyse: Analyse = { titre: null, cas: null, alertes: [], paragraphes: [], sections: [], notes: [] };
  let section: Section | null = null;

  for (const brute of contenu.split("\n")) {
    const ligne = brute.trim();
    if (!ligne) continue;

    const enSection = /^\*\*(.+?)\s*:\s*\*\*$/.exec(ligne);
    if (enSection) {
      section = { genre: genreDe(enSection[1]), titre: enSection[1], items: [] };
      analyse.sections.push(section);
      continue;
    }

    const seul = /^\*\*([^*]+)\*\*$/.exec(ligne);
    if (seul && !analyse.titre) {
      analyse.titre = seul[1].replace(/^(Démarche|Procedure)\s*:\s*/, "");
      continue;
    }

    const cas = /^(?:Votre cas|Your situation)\s*:\s*(.+)$/.exec(ligne);
    if (cas) {
      analyse.cas = cas[1];
      continue;
    }

    if (/^(Attention|Warning)\s*:/.test(ligne)) {
      analyse.alertes.push(ligne);
      continue;
    }

    const item = /^(?:-|\d+\.)\s+(.*)$/.exec(ligne);
    if (item) {
      if (!section) {
        section = { genre: "liste", titre: "", items: [] };
        analyse.sections.push(section);
      }
      section.items.push(item[1]);
      continue;
    }

    // Un paragraphe referme la section : après une liste, c'est une note de fin.
    (analyse.sections.length ? analyse.notes : analyse.paragraphes).push(ligne);
    section = null;
  }
  return analyse;
}

/** Regroupe « Fiche : élément » quand une réponse réunit plusieurs fiches (permis de construire...). */
export function grouper(items: string[]): Groupe[] {
  const prefixe = (item: string) => {
    const position = item.indexOf(" : ");
    return position > 0 ? item.slice(0, position) : null;
  };
  const compte = new Map<string, number>();
  items.forEach((item) => {
    const p = prefixe(item);
    if (p) compte.set(p, (compte.get(p) || 0) + 1);
  });

  const groupes: Groupe[] = [];
  items.forEach((item) => {
    const p = prefixe(item);
    const partage = p !== null && (compte.get(p) || 0) > 1;
    const nom = partage ? p : null;
    const texte = partage ? item.slice((p as string).length + 3) : item;
    const dernier = groupes[groupes.length - 1];
    if (dernier && dernier.nom === nom) dernier.items.push(texte);
    else groupes.push({ nom, items: [texte] });
  });
  return groupes;
}

/** Sépare la référence du contenu d'un extrait : « Article 6 : texte ». */
export function separerExtrait(item: string): { reference: string | null; texte: string } {
  const position = item.indexOf(" : ");
  return position > 0 && position < 90
    ? { reference: item.slice(0, position), texte: item.slice(position + 3) }
    : { reference: null, texte: item };
}
