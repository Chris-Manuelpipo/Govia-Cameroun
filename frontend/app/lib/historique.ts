import { Message } from "../types";

/**
 * Historique des conversations, gardé dans le navigateur de la personne (localStorage) : il n'est jamais envoyé
 * au serveur. La notice de consentement le dit, et le retrait de l'accord l'efface.
 */
export interface Conversation {
  id: string;
  titre: string;
  /** Date de la dernière modification, ISO 8601. */
  maj: string;
  messages: Message[];
}

const CLE = "govia-historique";
const MAX_CONVERSATIONS = 30;
const MAX_MESSAGES = 60;

const valide = (c: unknown): c is Conversation =>
  !!c && typeof (c as Conversation).id === "string" && Array.isArray((c as Conversation).messages) && typeof (c as Conversation).maj === "string";

export function lire(): Conversation[] {
  try {
    const brut = localStorage.getItem(CLE);
    const donnees = brut ? JSON.parse(brut) : [];
    return Array.isArray(donnees) ? donnees.filter(valide) : [];
  } catch {
    return [];
  }
}

/** Écrit la liste ; si le navigateur refuse (quota), les conversations les plus anciennes sont abandonnées. */
function ecrire(liste: Conversation[]): void {
  let reste = liste.slice(0, MAX_CONVERSATIONS);
  for (;;) {
    try {
      localStorage.setItem(CLE, JSON.stringify(reste));
      return;
    } catch {
      if (reste.length <= 1) return;
      reste = reste.slice(0, -1);
    }
  }
}

export const nouvelId = () => `${Date.now().toString(36)}${Math.random().toString(36).slice(2, 8)}`;

export function titreDe(messages: Message[]): string {
  const premiere = messages.find((m) => m.role === "user")?.content.replace(/\s+/g, " ").trim() || "";
  return premiere.length > 70 ? `${premiere.slice(0, 67)}...` : premiere;
}

/** Ce qui est gardé : les échanges terminés, sans l'état d'affichage. */
export function pourStockage(messages: Message[]): Message[] {
  return messages
    .filter((m) => !m.chargement && !m.erreur)
    .slice(-MAX_MESSAGES)
    .map(({ nouveau, ...reste }) => reste);
}

export function enregistrer(liste: Conversation[], conversation: Conversation): Conversation[] {
  const suivante = [conversation, ...liste.filter((c) => c.id !== conversation.id)].sort((a, b) => b.maj.localeCompare(a.maj));
  ecrire(suivante);
  return suivante.slice(0, MAX_CONVERSATIONS);
}

export function supprimer(liste: Conversation[], id: string): Conversation[] {
  const suivante = liste.filter((c) => c.id !== id);
  ecrire(suivante);
  return suivante;
}

export function toutEffacer(): void {
  try {
    localStorage.removeItem(CLE);
  } catch {
    // Stockage inaccessible : il n'y a rien à effacer.
  }
}
