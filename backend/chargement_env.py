"""Lecture du fichier .env à la racine du dépôt, pour un lancement sans Docker.

Les variables déjà définies dans l'environnement priment, et une valeur vide est ignorée.
GOVIA_SANS_DOTENV=1 désactive la lecture (c'est le cas des tests, qui ne doivent jamais appeler un vrai modèle).
"""
from __future__ import annotations

import os
from pathlib import Path


def charger(chemin: Path | None = None) -> None:
    if os.getenv("GOVIA_SANS_DOTENV") == "1":
        return
    chemin = chemin or Path(__file__).resolve().parent.parent / ".env"
    if not chemin.is_file():
        return
    for ligne in chemin.read_text(encoding="utf-8").splitlines():
        ligne = ligne.strip()
        if not ligne or ligne.startswith("#") or "=" not in ligne:
            continue
        cle, valeur = ligne.split("=", 1)
        valeur = valeur.strip().strip("\"'")
        if cle.strip() and valeur:
            os.environ.setdefault(cle.strip(), valeur)


charger()
