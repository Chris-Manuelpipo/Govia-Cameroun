export interface Citation {
  id: string;
  doc?: string;
  article: string;
  texte: string;
  titre: string;
  autorite?: string;
  source_url: string;
  type_source: "texte_officiel" | "reproduction" | "portail_institutionnel";
  statut_verification: string;
  note: string;
}

export interface Controle {
  nom: string;
  resultat: "ok" | "reserve" | "echec";
  detail: string;
}

export interface Audit {
  verdict: "conforme" | "partiel" | "non_conforme";
  decision: "publier" | "publier_avec_reserve" | "bloquer";
  controles: Controle[];
  gaps: string[];
}

export interface Formulaire {
  procedure_id: string;
  plateforme: string;
  champs: { nom: string; valeur: string }[];
}

export interface Option {
  libelle: string;
  message: string;
}

/** Pièce ou étape renvoyée par l'agent, toujours rattachée à l'extrait dont elle vient. */
export interface ElementTrace {
  texte: string;
  chunk: string;
}

export interface Message {
  role: "user" | "agent";
  content: string;
  type?: string;
  procedureId?: string | null;
  procedure?: string | null;
  statut?: "couvert" | "partiel" | "lacune" | null;
  mode?: string;
  options?: Option[];
  citations?: Citation[];
  etapes?: ElementTrace[];
  pieces?: ElementTrace[];
  audit?: Audit;
  formulaire?: Formulaire | null;
  chargement?: boolean;
  erreur?: boolean;
  /** Réponse qui vient d'arriver : son texte s'affiche progressivement, une seule fois. */
  nouveau?: boolean;
}

export type Statut = "couvert" | "partiel" | "lacune";

export interface DemarcheCatalogue {
  id: string;
  nom: string;
  nom_en: string;
  domaine: string;
  statut: Statut;
  autorite: string;
}

export interface Stats {
  total_chunks: number;
  total_documents: number;
  par_statut_verification: Partial<Record<"verifie" | "a_verifier", number>>;
  demarches: Partial<Record<Statut, number>>;
}

export interface DocumentSource {
  doc: string;
  titre: string;
  source_url: string;
  type_source: Citation["type_source"];
  statut_verification: string;
  chunks: number;
  methode_verification?: string;
}

export type Notice = Record<string, string>;

export type Vue = "demarches" | "assistant" | "sources" | "donnees";
