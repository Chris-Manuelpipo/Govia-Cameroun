/**
 * Indicateur de confiance d'une réponse et panneau qu'elle ouvre.
 * Une seule règle pour la bulle, la fiche et les états spéciaux : ils ne peuvent pas se contredire.
 */
import { Citation, Message } from "../types";

export type Niveau = "verifie" | "a_verifier" | "aucun";
export type Raison = "sources" | "partiel" | "proches" | "retenue" | "sans_source";

export interface Confiance {
  niveau: Niveau;
  /** Précise pourquoi une réponse est « À vérifier » ; absent pour les deux autres niveaux. */
  raison?: Raison;
}

/** Niveau de confiance d'une réponse de l'agent, ou null quand la notion ne s'applique pas (précision, refus). */
export function confiance(m: Message): Confiance | null {
  if (m.chargement || m.erreur) return null;
  const citations = m.citations || [];

  if (m.type === "lacune") return { niveau: "aucun" };
  if (m.type === "hors_perimetre") return citations.length ? { niveau: "a_verifier", raison: "proches" } : { niveau: "aucun" };
  // Précision, refus, modèle seul : la notion de confiance ne s'applique pas. Tout autre type est jugé sur ses sources,
  // comme panneauDe() qui ouvre une fiche dès qu'il y a des citations : les deux ne peuvent pas se contredire.
  if (m.type === "clarification" || m.type === "refus" || m.type === "non_gouvernee") return null;
  if (m.type !== "reponse" && !citations.length) return null;

  if (m.statut === "lacune") return { niveau: "aucun" };
  // Une réponse retenue par l'auditeur n'a rien de vérifié, même si ses sources le sont.
  if (m.audit?.decision === "bloquer") return { niveau: "a_verifier", raison: "retenue" };
  if (!citations.length) return { niveau: "a_verifier", raison: "sans_source" };
  if (m.statut === "partiel") return { niveau: "a_verifier", raison: "partiel" };
  if (citations.some((c) => c.statut_verification !== "verifie")) return { niveau: "a_verifier", raison: "sources" };
  return { niveau: "verifie" };
}

export type Panneau = "fiche" | "precision" | "aucun";

/** Ce que la réponse ouvre dans le panneau de droite ; null pour un refus ou une erreur, qui restent dans le fil. */
export function panneauDe(m: Message): Panneau | null {
  if (m.chargement || m.erreur) return null;
  if (m.type === "clarification") return "precision";
  if (m.type === "lacune" || (m.type === "hors_perimetre" && !m.citations?.length)) return "aucun";
  if (m.type === "reponse" || m.citations?.length) return "fiche";
  return null;
}

export interface DocumentCite {
  cle: string;
  titre: string;
  url: string;
  type: Citation["type_source"];
  verifie: boolean;
  articles: string[];
}

/** Regroupe les extraits cités par document : un document n'apparaît qu'une fois, vérifié seulement si tous ses extraits cités le sont. */
export function documentsCites(citations: Citation[]): DocumentCite[] {
  const documents = new Map<string, DocumentCite>();
  for (const c of citations) {
    const cle = c.doc || `${c.titre}|${c.source_url}`;
    const document = documents.get(cle) || { cle, titre: c.titre, url: c.source_url, type: c.type_source, verifie: true, articles: [] };
    document.verifie = document.verifie && c.statut_verification === "verifie";
    if (c.article && !document.articles.includes(c.article)) document.articles.push(c.article);
    documents.set(cle, document);
  }
  return Array.from(documents.values());
}
