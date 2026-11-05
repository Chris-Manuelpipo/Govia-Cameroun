"""Chargement du catalogue des démarches et détection de la démarche demandée.

La détection compare des expressions sur des mots entiers, sans accents. Elle ne devine
pas : un mot vague (« carte », « permis ») ou une égalité entre démarches produit une
demande de précision, conformément au scénario de démonstration de la version gouvernée.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from textes_utils import contient_mot, normaliser

KB_DIR = Path(os.getenv("GOVIA_KB_DIR", Path(__file__).resolve().parent.parent / "knowledge_base"))

# Demandes manifestement illicites : l'agent refuse au lieu de citer une procédure.
MOTS_ILLICITES = [
    "pirater", "hacker", "falsifier", "falsification", "faux papiers", "fausse cni", "faux passeport",
    "faux acte", "faux diplome", "contrefaire", "contrefacon", "corrompre", "pot de vin", "soudoyer",
    "contourner", "hack", "forge", "forged", "fake id", "fake passport", "bribe", "counterfeit", "bypass",
]


# Une relance comme « combien ça coûte ? » ne contient que ces mots : elle prolonge la
# démarche en cours. Si d'autres mots apparaissent (« le prix du pain »), c'est un autre sujet.
MOTS_DE_RELANCE = set(
    "combien cout coute coutent prix frais tarif delai delais duree temps piece pieces document documents "
    "etape etapes ou quand comment quel quelle quels quelles quoi faut il faire est sont ce ca c le la les un une "
    "des du de d l a au aux et pour moi je dois fournir apporter payer "
    "how much cost costs price fee fees long time where when what which document documents step steps "
    "do i need is it the a an to for and pay bring provide".split()
)


@dataclass
class Detection:
    """Résultat de la détection pour un message."""

    demarche: Optional[dict] = None
    candidats: list[dict] = field(default_factory=list)
    illicite: bool = False

    @property
    def ambigu(self) -> bool:
        return self.demarche is None and len(self.candidats) > 1


class Catalogue:
    def __init__(self, chemin: Path | None = None):
        donnees = json.loads((chemin or KB_DIR / "catalogue.json").read_text(encoding="utf-8"))
        self.demarches: list[dict] = donnees["demarches"]
        self.par_id: dict[str, dict] = {d["id"]: d for d in self.demarches}
        self.ambigus: dict[str, list[str]] = {normaliser(m): v for m, v in donnees["ambigus"].items()}
        # Du nom le plus long au plus court : « Permis de construire ... » avant « Permis ».
        self._noms = sorted(
            ((normaliser(n), d) for d in self.demarches for n in (d["nom"], d["nom_en"])),
            key=lambda x: len(x[0]),
            reverse=True,
        )

    def _par_nom(self, texte: str) -> Optional[dict]:
        """Un bouton de précision envoie le nom exact de la démarche : il prime sur les mots-clés."""
        for nom, demarche in self._noms:
            if texte == nom or texte.startswith(f"{nom} "):
                return demarche
        return None

    def _prolonge(self, texte: str, demarche: dict, vagues: list[dict]) -> bool:
        """Le message poursuit-il la démarche de l'échange, ou change-t-il de sujet ?"""
        if self.detecter_cas(demarche, [texte]) is not None:
            return True
        if vagues:
            return demarche in vagues
        mots = texte.split()
        return bool(mots) and all(m in MOTS_DE_RELANCE for m in mots)

    def _meilleures(self, texte: str) -> list[dict]:
        """Démarches dont un mot-clé précis figure dans le texte ; les plus longs l'emportent."""
        scores: dict[str, int] = {}
        for demarche in self.demarches:
            for mot in demarche["mots_cles"]:
                if contient_mot(texte, mot):
                    scores[demarche["id"]] = max(scores.get(demarche["id"], 0), len(mot.split()))
        if not scores:
            return []
        meilleur = max(scores.values())
        return [self.par_id[i] for i, s in scores.items() if s == meilleur]

    def demarches_citees(self, message: str) -> list[dict]:
        """Démarches nommées précisément dans un message."""
        texte = normaliser(message)
        par_nom = self._par_nom(texte)
        return [par_nom] if par_nom else self._meilleures(texte)

    def _vagues(self, texte: str) -> list[dict]:
        """Démarches évoquées par des mots vagues ; plusieurs mots réduisent les possibilités."""
        ensembles = [set(cibles) for mot, cibles in self.ambigus.items() if contient_mot(texte, mot)]
        if not ensembles:
            return []
        commun = set.intersection(*ensembles)
        retenus = commun or set.union(*ensembles)
        return [d for d in self.demarches if d["id"] in retenus]

    def detecter(self, message: str, historique: list[str] | None = None) -> Detection:
        """Détecte la démarche du dernier message, puis, à défaut, dans l'échange récent."""
        message_norm = normaliser(message)
        if any(contient_mot(message_norm, mot) for mot in MOTS_ILLICITES):
            return Detection(illicite=True)

        par_nom = self._par_nom(message_norm)
        if par_nom is not None:
            return Detection(demarche=par_nom)

        precises = self._meilleures(message_norm)
        if len(precises) == 1:
            return Detection(demarche=precises[0])
        if len(precises) > 1:
            return Detection(candidats=precises)

        vagues = self._vagues(message_norm)

        # Le message répond peut-être à une question de précision : on relit l'échange,
        # sans y rattacher une question qui change de sujet.
        for ancien in reversed(historique or []):
            precedentes = self._par_nom(normaliser(ancien))
            precedentes = [precedentes] if precedentes else self._meilleures(normaliser(ancien))
            if len(precedentes) == 1:
                if self._prolonge(message_norm, precedentes[0], vagues):
                    return Detection(demarche=precedentes[0])
                break

        if len(vagues) == 1:
            return Detection(demarche=vagues[0])
        return Detection(candidats=vagues)

    @staticmethod
    def detecter_cas(demarche: dict, textes: list[str]) -> Optional[dict]:
        """Repère le cas particulier : le message le plus récent prime, puis le mot-clé le plus long."""
        for texte in textes:
            texte_norm = normaliser(texte)
            meilleur, longueur = None, 0
            for cas in demarche.get("cas", []):
                for mot in cas["mots"]:
                    if contient_mot(texte_norm, mot) and len(mot.split()) > longueur:
                        meilleur, longueur = cas, len(mot.split())
            if meilleur:
                return meilleur
        return None
