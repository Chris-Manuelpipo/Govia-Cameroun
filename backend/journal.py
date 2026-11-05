"""Journal d'audit persistant (registre des traitements, Loi n° 2024/017, art. 29).

Chaque ligne trace une décision de l'agent sans contenir ni la question, ni la réponse,
ni aucune donnée personnelle : seuls figurent la démarche, les sources citées et le
verdict. Une demande peut ainsi être expliquée a posteriori sans conserver de données.
"""
from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path

CHEMIN = Path(os.getenv("GOVIA_AUDIT_LOG", Path(__file__).resolve().parent.parent / "logs" / "audit.jsonl"))
_verrou = threading.Lock()


def consigner(*, version: str, langue: str, agent: dict, audit: dict) -> None:
    entree = {
        "horodatage": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "version": version,
        "langue": langue,
        "type_reponse": agent["type_reponse"],
        "procedure_id": agent.get("procedure_id"),
        "cas": agent.get("cas"),
        "mode_generation": agent["mode_generation"],
        "citations": [c["id"] for c in agent.get("citations", [])],
        "verdict": audit["verdict"],
        "decision": audit["decision"],
        "controles": [{"nom": c["nom"], "resultat": c["resultat"]} for c in audit.get("controles", [])],
    }
    try:
        with _verrou:
            CHEMIN.parent.mkdir(parents=True, exist_ok=True)
            with open(CHEMIN, "a", encoding="utf-8") as fichier:
                fichier.write(json.dumps(entree, ensure_ascii=False) + "\n")
    except OSError as erreur:
        # La réponse au citoyen ne dépend pas du journal, mais l'échec doit se voir.
        print(f"[Journal] Écriture impossible : {erreur}")
