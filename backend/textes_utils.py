"""Outils de comparaison de texte partagés par le catalogue, le RAG et l'auditeur."""
from __future__ import annotations

import re
import unicodedata


def normaliser(texte: str) -> str:
    """Minuscules, sans accents, ponctuation réduite à des espaces."""
    texte = texte.replace("’", "'").replace("ʼ", "'").lower()
    texte = "".join(c for c in unicodedata.normalize("NFD", texte) if unicodedata.category(c) != "Mn")
    texte = re.sub(r"[^\w%]+", " ", texte)
    return re.sub(r"\s+", " ", texte).strip()


def contient_mot(texte_normalise: str, expression: str) -> bool:
    """Cherche une expression sur des mots entiers : « cni » ne matche pas « technique »."""
    return re.search(rf"(?<!\w){re.escape(normaliser(expression))}(?!\w)", texte_normalise) is not None
