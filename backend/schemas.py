"""Modèles de données de l'API GOVIA."""
from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    messages: List[Message] = Field(min_length=1, max_length=20)
    consentement: bool = Field(
        default=False,
        description="Consentement préalable, libre, éclairé, spécifique et univoque (Loi n° 2024/017, art. 9).",
    )
    language: Literal["FR", "EN"] = "FR"
    version: Literal["A", "B"] = Field(
        default="B",
        description="B : version gouvernée. A : sans gouvernance, pour la comparaison du rapport (désactivée par défaut).",
    )


class Citation(BaseModel):
    id: str
    doc: str
    procedure_id: str
    article: str
    texte: str
    titre: str
    autorite: str
    source_url: str
    type_source: str
    statut_verification: str
    note: str = ""
    score: float = 0.0


class ElementTrace(BaseModel):
    """Pièce ou étape, toujours reliée au chunk dont elle est extraite."""

    texte: str
    chunk: str


class OptionClarification(BaseModel):
    libelle: str
    message: str


class AgentResponse(BaseModel):
    type_reponse: Literal["reponse", "clarification", "lacune", "hors_perimetre", "conversation", "refus", "non_gouvernee"]
    reponse: str
    procedure_id: Optional[str] = None
    procedure_identifiee: Optional[str] = None
    statut_demarche: Optional[str] = None
    cas: Optional[str] = None
    options: List[OptionClarification] = []
    pieces_requises: List[ElementTrace] = []
    etapes: List[ElementTrace] = []
    citations: List[Citation] = []
    formulaire_prerempli: Optional[dict] = None
    mode_generation: str
    audit_log: List[dict] = []


class ControleAudit(BaseModel):
    nom: str
    resultat: Literal["ok", "reserve", "echec"]
    detail: str


class AuditResult(BaseModel):
    verdict: Literal["conforme", "partiel", "non_conforme"]
    decision: Literal["publier", "publier_avec_reserve", "bloquer"]
    controles: List[ControleAudit] = []
    details: List[str] = []
    gaps: List[str] = []


class ChatResponse(BaseModel):
    version: Literal["A", "B"]
    agent: AgentResponse
    audit: AuditResult
