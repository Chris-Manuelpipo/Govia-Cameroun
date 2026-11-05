"""Base de connaissances et recherche de passages (RAG).

- Index vectoriel ChromaDB avec un modèle d'embeddings multilingue, car la base mêle
  français et anglais. L'index est reconstruit dès que le contenu de la base change.
- Sans ChromaDB, recherche par mots entiers : même contrat, moins de finesse.
- Aucune recherche ne renvoie de passage en dessous du seuil de pertinence : mieux vaut
  signaler une absence de texte que citer un passage sans rapport.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Iterable, List, Optional

from catalogue import KB_DIR
from textes_utils import contient_mot, normaliser

COLLECTION = "govia_policies"
CHROMA_DIR = Path(os.getenv("GOVIA_CHROMA_DIR", KB_DIR.parent / "chroma_db"))
MODELE_EMBEDDINGS = os.getenv("GOVIA_EMBED_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")
SEUIL_VECTORIEL = float(os.getenv("GOVIA_MIN_SCORE", "0.35"))
SEUIL_MOTS = float(os.getenv("GOVIA_MIN_KEYWORD_SCORE", "0.5"))

MOTS_VIDES = set(
    "le la les un une des du de d l au aux et ou en a à dans sur pour par avec sans ce cette ces mon ma mes ton ta tes "
    "son sa ses notre votre leur leurs je tu il elle on nous vous ils elles que qui quoi dont est sont suis etre avoir "
    "ai as veux voudrais souhaite comment quel quelle quels quelles faire obtenir demander besoin peut peuvent "
    "doit doivent the an of to in on "
    "for and or is are am i my me you your how what which want need get do does can with at by from".split()
)


def load_all_chunks(kb_dir: Path = KB_DIR) -> List[dict]:
    """Charge tous les chunks JSONL de la base."""
    chunks: List[dict] = []
    for fichier in sorted(kb_dir.glob("*.jsonl")):
        with open(fichier, encoding="utf-8") as lignes:
            chunks.extend(json.loads(ligne) for ligne in lignes if ligne.strip())
    return chunks


def citation_de(chunk: dict, score: float) -> dict:
    """Forme publique d'un chunk cité."""
    return {
        "id": chunk["id"],
        "doc": chunk["doc"],
        "procedure_id": chunk["procedure_id"],
        "article": chunk["article"],
        "texte": chunk["texte"],
        "titre": chunk["titre"],
        "autorite": chunk["autorite"],
        "source_url": chunk["source_url"],
        "type_source": chunk["type_source"],
        "statut_verification": chunk["statut_verification"],
        "note": chunk.get("note", ""),
        "score": round(float(score), 4),
    }


class KnowledgeBase:
    def __init__(self, kb_dir: Path = KB_DIR):
        self.chunks = load_all_chunks(kb_dir)
        self.par_id = {c["id"]: c for c in self.chunks}
        self._collection = None
        if self.chunks and os.getenv("GOVIA_DISABLE_CHROMA", "0") != "1":
            self._init_chroma()

    @property
    def mode(self) -> str:
        return "vectoriel" if self._collection is not None else "mots_cles"

    def _empreinte(self) -> str:
        contenu = "\n".join(f"{c['id']}|{c['texte']}" for c in self.chunks) + MODELE_EMBEDDINGS
        return hashlib.sha256(contenu.encode("utf-8")).hexdigest()

    def _init_chroma(self) -> None:
        try:
            import chromadb
            from chromadb.config import Settings
            from chromadb.utils import embedding_functions

            # Télémétrie coupée : aucune information d'usage ne doit quitter le serveur.
            client = chromadb.PersistentClient(path=str(CHROMA_DIR), settings=Settings(anonymized_telemetry=False))
            fonction = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=MODELE_EMBEDDINGS)
            empreinte = self._empreinte()
            collection = client.get_or_create_collection(
                name=COLLECTION,
                embedding_function=fonction,
                metadata={"hnsw:space": "cosine", "empreinte": empreinte},
            )
            if (collection.metadata or {}).get("empreinte") != empreinte or collection.count() != len(self.chunks):
                client.delete_collection(COLLECTION)
                collection = client.create_collection(
                    name=COLLECTION,
                    embedding_function=fonction,
                    metadata={"hnsw:space": "cosine", "empreinte": empreinte},
                )
                collection.add(
                    ids=[c["id"] for c in self.chunks],
                    documents=[f"{c['titre']} — {c['article']} : {c['texte']}" for c in self.chunks],
                    metadatas=[{"procedure_id": c["procedure_id"], "doc": c["doc"]} for c in self.chunks],
                )
            self._collection = collection
        except Exception as erreur:  # dépendance absente, modèle indisponible hors ligne, etc.
            self._collection = None
            print(f"[RAG] ChromaDB indisponible ({type(erreur).__name__}) : recherche par mots.")

    def retrieve(
        self,
        query: str,
        n_k: int = 5,
        procedure_ids: Optional[Iterable[str]] = None,
    ) -> List[dict]:
        """Passages les plus pertinents, éventuellement limités à certaines démarches."""
        n_k = max(1, min(n_k, 50))
        ids = list(procedure_ids) if procedure_ids else None
        if self._collection is not None:
            return self._retrieve_vectoriel(query, n_k, ids)
        return self._retrieve_mots(query, n_k, ids)

    def _retrieve_vectoriel(self, query: str, n_k: int, ids: Optional[List[str]]) -> List[dict]:
        filtre = {"procedure_id": {"$in": ids}} if ids else None
        resultat = self._collection.query(query_texts=[query], n_results=n_k, where=filtre)
        sortie = []
        for identifiant, distance in zip(resultat["ids"][0], resultat["distances"][0]):
            score = 1.0 - distance
            # Limiter à une démarche identifiée suffit à garantir le sujet : le seuil ne
            # s'applique qu'à la recherche sur toute la base.
            if ids or score >= SEUIL_VECTORIEL:
                sortie.append(citation_de(self.par_id[identifiant], score))
        return sortie

    def _retrieve_mots(self, query: str, n_k: int, ids: Optional[List[str]]) -> List[dict]:
        mots = [m for m in normaliser(query).split() if m not in MOTS_VIDES and len(m) > 2]
        if not mots:
            return []
        scores = []
        for chunk in self.chunks:
            if ids and chunk["procedure_id"] not in ids:
                continue
            texte = normaliser(f"{chunk['titre']} {chunk['article']} {chunk['texte']}")
            score = sum(contient_mot(texte, m) for m in mots) / len(mots)
            if score > 0 and (ids or score >= SEUIL_MOTS):
                scores.append((score, chunk))
        # À score égal, le passage le plus court est le plus ciblé.
        scores.sort(key=lambda x: (-x[0], len(x[1]["texte"])))
        return [citation_de(c, s) for s, c in scores[:n_k]]


kb = KnowledgeBase()
