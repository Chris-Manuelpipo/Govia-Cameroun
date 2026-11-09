"""Agent d'analyse : comprend la demande du citoyen et classe la procédure concernée.

Il ne cherche aucun texte et ne rédige rien. Il rend une seule issue :
- « conversation » : salutation, remerciement, demande d'aide ou question générale, sans démarche ;
- « refus » : la demande vise à contourner une procédure ou à falsifier un document ;
- « clarification_demarche » : plusieurs démarches correspondent, on demande laquelle ;
- « hors_perimetre » : aucune démarche du catalogue ne correspond ;
- « lacune » : la démarche est connue mais aucune source ouverte fiable ne la détaille ;
- « clarification_cas » : la démarche exige de préciser le cas (perte, renouvellement...) ;
- « demarche » : démarche, et cas s'il y a lieu, identifiés.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Literal, Optional

from catalogue import Catalogue
from conversation import Sujet, reconnaitre

Issue = Literal["refus", "clarification_demarche", "conversation", "hors_perimetre", "lacune", "clarification_cas", "demarche"]


@dataclass
class Analyse:
    issue: Issue
    demarche: Optional[dict] = None
    cas: Optional[dict] = None
    candidats: List[dict] = field(default_factory=list)
    sujet: Optional[Sujet] = None


class AgentAnalyse:
    def __init__(self, catalogue: Optional[Catalogue] = None):
        self.catalogue = catalogue or Catalogue()

    def analyser(self, query: str, historique: Optional[List[str]] = None, langue: str = "FR") -> Analyse:
        historique = historique or []
        detection = self.catalogue.detecter(query, historique)
        if detection.illicite:
            return Analyse("refus")
        if detection.demarche is None:
            if detection.ambigu:
                return Analyse("clarification_demarche", candidats=detection.candidats)
            # Aucune démarche : est-ce de la conversation (« bonjour », « que peux-tu faire ? ») ou un autre sujet ?
            sujet = reconnaitre(query, langue, deja_salue=any(
                (ancien := reconnaitre(h, langue)) is not None and ancien.nom in ("salutation", "etat") for h in (historique or [])
            ))
            return Analyse("conversation", sujet=sujet) if sujet else Analyse("hors_perimetre")

        demarche = detection.demarche
        if demarche["statut"] == "lacune":
            return Analyse("lacune", demarche=demarche)

        cas = self.catalogue.detecter_cas(demarche, self._textes_du_cas(query, historique, demarche))
        if demarche.get("cas_mode") == "choix" and cas is None:
            return Analyse("clarification_cas", demarche=demarche)
        return Analyse("demarche", demarche=demarche, cas=cas)

    def _textes_du_cas(self, query: str, historique: List[str], demarche: dict) -> List[str]:
        """Messages où chercher le cas : le message courant, puis le précédent s'il s'y rapporte.

        Remonter plus loin ferait resservir un cas périmé, et un message sur une autre démarche
        (« j'ai perdu mon passeport ») ne dit rien du cas de celle-ci.
        """
        textes = [query]
        if historique:
            citees = self.catalogue.demarches_citees(historique[-1])
            if not citees or demarche in citees:
                textes.append(historique[-1])
        return textes
