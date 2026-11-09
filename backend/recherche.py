"""Agent de recherche : recherche documentaire et extraction des informations pertinentes (RAG).

À partir de la démarche et du cas fixés par l'agent d'analyse, il réunit pièces, étapes,
coûts, durées et citations : d'abord le catalogue, dont chaque élément renvoie au passage
dont il est extrait, puis la recherche sémantique, limitée aux textes de cette démarche.
Il ne rédige rien et ne juge pas la conformité : c'est le rôle de l'agent de validation.
"""
from __future__ import annotations

from typing import List, Optional

from rag import KnowledgeBase, citation_de, kb as kb_par_defaut

MAX_CITATIONS_RAG = 3


class AgentRecherche:
    def __init__(self, base: Optional[KnowledgeBase] = None):
        self.kb = base or kb_par_defaut

    @property
    def mode(self) -> str:
        return self.kb.mode

    def orienter(self, query: str, n_k: int = 3) -> List[dict]:
        """Passages proches d'une demande qu'aucune démarche du catalogue ne couvre."""
        return self.kb.retrieve(query, n_k=n_k)

    @staticmethod
    def _fiches_retenues(demarche: dict, cas: Optional[dict]) -> List[dict]:
        if cas and cas.get("fiche"):
            return [f for f in demarche["fiches"] if f["fiche"] == cas["fiche"]]
        return demarche["fiches"]

    def rassembler(self, query: str, demarche: dict, cas: Optional[dict]) -> dict:
        """Réunit pièces, étapes, coûts et citations d'après le catalogue, puis le RAG."""
        kb = self.kb
        fiches = self._fiches_retenues(demarche, cas)
        pieces: List[dict] = list(demarche.get("pieces", []))
        etapes: List[dict] = list(demarche.get("etapes", []))
        identifiants: List[str] = []
        if cas:
            pieces = list(cas.get("pieces", [])) + pieces
            if cas.get("chunk"):
                identifiants.append(cas["chunk"])

        couts, durees = [], []
        for fiche in fiches:
            prefixe = f"{fiche['libelle']} : " if len(fiches) > 1 else ""
            source = {c.rsplit("::", 1)[1]: c for c in fiche["chunks"]}
            etapes += [{"texte": prefixe + e, "chunk": source["etapes"]} for e in fiche["etapes"]]
            if "documents" in source:
                pieces += [{"texte": prefixe + p, "chunk": source["documents"]} for p in fiche["pieces"]]
            if fiche["cout"]:
                couts.append(prefixe + " ; ".join(fiche["cout"]))
            if fiche["duree_totale"]:
                durees.append(prefixe + fiche["duree_totale"])
            identifiants += fiche["chunks"]

        identifiants += [x["chunk"] for x in pieces + etapes]
        identifiants += demarche.get("chunks_complementaires", [])
        vus = list(dict.fromkeys(identifiants))
        citations = [citation_de(kb.par_id[i], 1.0) for i in vus if i in kb.par_id]

        # Le RAG complète par des passages de la même démarche, jamais d'une autre.
        admis = set(vus)
        fiches_ecartees = {
            i for f in demarche["fiches"] if f not in fiches for i in f["chunks"]
        }
        supplements = [
            c for c in kb.retrieve(query, n_k=MAX_CITATIONS_RAG + len(vus) + 1, procedure_ids=[demarche["id"]])
            if c["id"] not in admis and c["id"] not in fiches_ecartees
        ]
        supplements = supplements[:MAX_CITATIONS_RAG]
        citations += supplements

        # Une démarche sans pièces ni étapes (protection des données, signature...) reste
        # fondée sur ses textes : à défaut de passage proche, on cite ses premiers articles.
        if not citations:
            supplements = [citation_de(kb.par_id[i], 0.0) for i in demarche["chunks"][:MAX_CITATIONS_RAG]]
            citations = list(supplements)

        complements = [i for i in demarche.get("chunks_complementaires", []) if i in kb.par_id]
        extraits = [c for c in citations if c["id"] in complements or c in supplements]
        return {
            "pieces": pieces, "etapes": etapes, "couts": couts, "durees": durees,
            "citations": citations, "extraits": extraits,
        }
