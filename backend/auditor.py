"""Agent de validation (auditeur) : vérifie les informations, la conformité et les sources.

Il intervient deux fois, sous la conduite de l'orchestrateur : sur le brouillon du LLM,
qu'il peut faire écarter, puis sur la réponse finale avant publication.

Contrairement à un simple relevé de citations, l'auditeur vérifie :
1. l'intégrité : chaque citation existe dans la base, avec le texte exact ;
2. le fondement : une réponse sur une démarche doit citer au moins une source ;
3. la pertinence : les citations portent sur la démarche concernée ;
4. les faits : chaque montant, délai, pourcentage ou article annoncé figure dans les
   sources citées ;
5. la fiabilité : une source à vérifier ou une démarche partielle entraîne une réserve ;
6. le ton et la responsabilité : pas d'affirmation subjective, rappel du rôle du citoyen.

Un échec à l'un des quatre premiers contrôles bloque la réponse. Les nombres écrits en
toutes lettres ne sont pas contrôlés : c'est une limite connue de cette version.
"""
from __future__ import annotations

import re
from typing import Iterable, List, Optional

from schemas import AuditResult, ControleAudit
from textes_utils import normaliser

EXPRESSIONS_SUBJECTIVES = [
    "selon moi", "je pense", "a mon avis", "probablement", "il faudrait peut etre", "je suppose", "je dirais",
    "i think", "in my opinion", "probably", "i guess", "i suppose",
]
MOTS_RESPONSABILITE = ["responsable", "valider", "validez", "responsible", "validate", "verify"]
TRANSVERSAUX = {"protection_donnees", "signature_electronique", "etat_civil"}

_NOMBRE = r"\d[\d\s.,]*\d|\d"
_FAITS = re.compile(
    rf"(?P<montant>{_NOMBRE})\s*(?:f\s?cfa|cfa|xaf|francs?)\b"
    rf"|(?:f\s?cfa|cfa|xaf)\s*(?P<montant2>{_NOMBRE})"
    rf"|(?P<duree>{_NOMBRE})\s*(?:jours?|j|mois|ans?|annees?|heures?|h|semaines?|minutes?|mn|days?|months?|years?|hours?|weeks?)\b"
    rf"|(?P<pourcent>{_NOMBRE})\s*%"
)
_ARTICLES = re.compile(r"\b(?:articles?|art|sections?)\s*\.?\s*(\d+)", re.I)


def _valeur(nombre: str) -> str:
    """Valeur d'un nombre écrit « 10 000 », « 41,650 » ou « 05 »."""
    chiffres = re.sub(r"\D", "", nombre)
    return chiffres.lstrip("0") or "0"


def _faits(texte: str) -> set[str]:
    trouves = set()
    for motif in _FAITS.finditer(texte.lower()):
        brut = next(v for v in motif.groupdict().values() if v)
        trouves.add(_valeur(brut))
    return trouves


def _nombres(textes: Iterable[str]) -> set[str]:
    return {_valeur(n) for texte in textes for n in re.findall(_NOMBRE, texte)}


def audit(
    reponse: str,
    citations: List[dict],
    *,
    base: Optional[dict] = None,
    procedure_id: Optional[str] = None,
    procedures_admises: Optional[Iterable[str]] = None,
    type_reponse: str = "reponse",
    statut_demarche: Optional[str] = None,
    note_lacune: Optional[str] = None,
) -> AuditResult:
    """Audite une réponse. `base` associe l'identifiant de chaque chunk à son contenu."""
    controles: List[ControleAudit] = []

    def noter(nom: str, resultat: str, detail: str) -> None:
        controles.append(ControleAudit(nom=nom, resultat=resultat, detail=detail))

    # 1. Intégrité des citations
    if base is not None:
        inconnues = [c["id"] for c in citations if c["id"] not in base]
        modifiees = [
            c["id"] for c in citations
            if c["id"] in base and (c["texte"] != base[c["id"]]["texte"] or c["source_url"] != base[c["id"]]["source_url"])
        ]
        if inconnues or modifiees:
            noter("integrite", "echec", f"Citations absentes de la base : {', '.join(inconnues) or 'aucune'} ; texte modifié : {', '.join(modifiees) or 'aucun'}.")
        elif citations:
            noter("integrite", "ok", f"{len(citations)} citation(s) retrouvée(s) mot pour mot dans la base.")

    # 2. Fondement
    if type_reponse in ("reponse", "non_gouvernee") and not citations:
        noter("fondement", "echec", "Aucun texte de la base ne justifie cette réponse.")
    elif citations:
        noter("fondement", "ok", "La réponse s'appuie sur au moins une source.")

    # 3. Pertinence
    if procedure_id and citations:
        admises = set(procedures_admises or [procedure_id]) | TRANSVERSAUX
        hors_sujet = [c["id"] for c in citations if c.get("procedure_id") not in admises]
        if hors_sujet:
            noter("pertinence", "echec", f"Citations hors de cette démarche : {', '.join(hors_sujet)}.")
        else:
            noter("pertinence", "ok", "Toutes les citations concernent cette démarche.")

    # 4. Faits vérifiables
    corpus = [c["texte"] for c in citations]
    connus = _nombres(corpus)
    non_etayes = sorted(_faits(reponse) - connus)
    if non_etayes:
        noter("faits", "echec", f"Montants ou délais absents des sources citées : {', '.join(non_etayes)}.")
    elif citations:
        noter("faits", "ok", "Les montants et délais annoncés figurent dans les sources citées.")

    references = {c["article"].lower() for c in citations}
    corpus_norm = " ".join(corpus + list(references)).lower()
    articles_inconnus = sorted(
        {a for a in _ARTICLES.findall(reponse) if not re.search(rf"\b0*{a}\b", corpus_norm)},
        key=int,
    )
    if articles_inconnus:
        noter("references", "echec", f"Articles cités mais absents des sources : {', '.join(articles_inconnus)}.")

    # 5. Fiabilité des sources
    a_verifier = sorted({c.get("titre") or c["doc"] for c in citations if c.get("statut_verification") != "verifie"})
    if a_verifier:
        noter("fiabilite", "reserve", f"Sources non encore vérifiées : {' ; '.join(a_verifier)}.")
    if statut_demarche == "partiel":
        noter("fiabilite", "reserve", "Démarche appuyée sur une reproduction ancienne ou incomplète : à confirmer.")

    # 6. Ton et responsabilité
    texte_norm = normaliser(reponse)
    subjectif = [e for e in EXPRESSIONS_SUBJECTIVES if re.search(rf"(?<!\w){e}(?!\w)", texte_norm)]
    if subjectif:
        noter("ton", "reserve", f"Formulations subjectives : {', '.join(subjectif)}.")
    if type_reponse == "reponse" and not any(m in texte_norm for m in MOTS_RESPONSABILITE):
        noter("responsabilite", "reserve", "La réponse ne rappelle pas que le citoyen vérifie et reste responsable.")

    # Verdict et décision
    echecs = [c for c in controles if c.resultat == "echec"]
    reserves = [c for c in controles if c.resultat == "reserve"]
    if echecs:
        verdict, decision = "non_conforme", "bloquer"
    elif reserves:
        verdict, decision = "partiel", "publier_avec_reserve"
    else:
        verdict, decision = "conforme", "publier"

    gaps = [c.detail for c in echecs + reserves]
    if note_lacune:
        gaps.append(note_lacune)
    return AuditResult(
        verdict=verdict,
        decision=decision,
        controles=controles,
        details=[c.detail for c in controles if c.resultat == "ok"],
        gaps=gaps,
    )


def _procedures_admises(demarche: Optional[dict]) -> List[str]:
    if not demarche:
        return []
    return [demarche["id"], *demarche.get("procedures_liees", [])]


class AgentValidation:
    """Applique `audit` avec le contexte de la démarche fixé par l'agent d'analyse."""

    def __init__(self, base: Optional[dict] = None):
        self.base = base

    def controler_brouillon(self, brouillon: str, demarche: dict, citations: List[dict]) -> AuditResult:
        """Contrôle le texte rédigé par le LLM avant de l'accepter à la place des extraits."""
        return audit(
            brouillon, citations, base=self.base, procedure_id=demarche["id"],
            procedures_admises=_procedures_admises(demarche),
            type_reponse="reponse", statut_demarche=demarche["statut"],
        )

    def controler_reponse(self, reponse_agent: dict, demarche: Optional[dict]) -> AuditResult:
        """Contrôle la réponse finale, quel qu'en soit le type, avant publication."""
        return audit(
            reponse_agent["reponse"],
            reponse_agent["citations"],
            base=self.base,
            procedure_id=reponse_agent["procedure_id"] if reponse_agent["citations"] else None,
            procedures_admises=_procedures_admises(demarche),
            type_reponse=reponse_agent["type_reponse"],
            statut_demarche=reponse_agent["statut_demarche"],
            note_lacune=demarche.get("note_lacune") if demarche and demarche["statut"] == "lacune" else None,
        )

    def observer(self, reponse: str) -> AuditResult:
        """Version A : l'auditeur observe sans contexte ni blocage, pour la comparaison."""
        return audit(reponse, [], base=self.base, type_reponse="non_gouvernee")
