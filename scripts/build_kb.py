#!/usr/bin/env python3
"""Construit la base de connaissances GOVIA à partir de ses sources vérifiées.

Entrées :
  scripts/kb_data/textes.py                  textes réglementaires recopiés à la source
  scripts/kb_data/catalogue.py               démarches, mots-clés, statuts, lacunes
  scripts/kb_data/eregulations_yaounde.json  fiches extraites par fetch_eregulations.py

Sorties :
  knowledge_base/<doc>.jsonl     un chunk par ligne
  knowledge_base/index.json      inventaire des documents et de leur vérification
  knowledge_base/catalogue.json  catalogue utilisé par l'agent et l'auditeur
  docs/catalogue_demarches.md    couverture et lacunes, pour le rapport

La construction échoue si une pièce ou une étape du catalogue n'est pas un extrait
exact du chunk qu'elle cite : c'est ce contrôle qui empêche d'inventer une exigence.

Usage :
    python scripts/build_kb.py           # écrit les fichiers
    python scripts/build_kb.py --check   # vérifie que les fichiers sont à jour
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))

from kb_data.catalogue import AMBIGUS, DEMARCHES  # noqa: E402
from kb_data.textes import DATE_VERIFICATION, DOCUMENTS  # noqa: E402

RACINE = ICI.parent
KB_DIR = RACINE / "knowledge_base"
DOC_MD = RACINE / "docs" / "catalogue_demarches.md"
EREG_JSON = ICI / "kb_data" / "eregulations_yaounde.json"

NOTE_EREG = (
    "Fiche du portail eRegulations Yaoundé (MINPMEESA, appui PNUD/CNUCED). Les montants, "
    "délais et interlocuteurs sont ceux publiés sur le portail : à confirmer au guichet."
)


class ErreurKB(ValueError):
    """Incohérence qui interdit de publier la base."""


def normaliser(texte: str) -> str:
    """Minuscules, sans accents, apostrophes unifiées : pour comparer des extraits."""
    texte = texte.replace("’", "'").replace("ʼ", "'").lower()
    texte = "".join(c for c in unicodedata.normalize("NFD", texte) if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", texte).strip()


def chunk(doc: dict, cle: str, article: str, texte: str, procedure_id: str | None = None) -> dict:
    return {
        "id": f"{doc['doc']}::{cle}",
        "doc": doc["doc"],
        "procedure_id": procedure_id or doc["procedure_id"],
        "type": doc["type"],
        "type_source": doc["type_source"],
        "article": article,
        "texte": texte,
        "titre": doc["titre"],
        "autorite": doc["autorite"],
        "source_url": doc["source_url"],
        "date_publication": doc.get("date_publication", ""),
        "langue": doc.get("langue", "FR"),
        "statut_verification": doc["statut_verification"],
        "date_verification": DATE_VERIFICATION if doc["statut_verification"] == "verifie" else "",
        "note": doc.get("note", ""),
    }


def documents_textes() -> list[dict]:
    sortie = []
    for doc in DOCUMENTS:
        chunks = [
            chunk(doc, c[0], c[1], c[2], c[3] if len(c) > 3 else None)
            for c in doc["chunks"]
        ]
        sortie.append({**{k: v for k, v in doc.items() if k != "chunks"}, "chunks": chunks})
    return sortie


def documents_eregulations() -> tuple[list[dict], dict]:
    """Transforme chaque fiche en document : étapes, pièces, coût, durée, base légale."""
    donnees = json.loads(EREG_JSON.read_text(encoding="utf-8"))
    sortie, par_procedure = [], defaultdict(list)
    for fiche in donnees["fiches"]:
        note = NOTE_EREG
        if fiche["en_revision"]:
            note += " Le portail signale cette procédure comme en cours de révision."
        doc = {
            "doc": f"eregulations_{fiche['fiche']}",
            "titre": f"eRegulations Yaoundé — {fiche['libelle']}",
            "autorite": ", ".join(fiche["ou_aller"]) or "Voir la fiche du portail",
            "source_url": fiche["source_url"],
            "date_publication": "",
            "type": "procédure",
            "type_source": "portail_institutionnel",
            "statut_verification": "verifie",
            "methode": f"Extrait automatiquement du portail le {donnees['date_extraction']} (scripts/fetch_eregulations.py).",
            "note": note,
            "procedure_id": fiche["procedure_id"],
        }
        libelle = fiche["libelle"]
        etapes = fiche["etapes"]
        pieces = [x for x in fiche["documents"] if x != "*"]
        chunks = [
            chunk(doc, "etapes", "Étapes", f"{libelle} — étapes : " + " ; ".join(etapes) + "."),
        ]
        if pieces:
            chunks.append(chunk(doc, "documents", "Documents nécessaires", f"{libelle} — documents nécessaires : " + " ; ".join(pieces) + "."))
        if fiche["cout"]:
            chunks.append(chunk(doc, "cout", "Coût", f"{libelle} — coût : " + " ; ".join(fiche["cout"]) + "."))
        organismes = "Organismes : " + ", ".join(fiche["ou_aller"]) + "." if fiche["ou_aller"] else ""
        if fiche["duree_totale"] or organismes:
            chunks.append(chunk(doc, "duree", "Durée et organismes", f"{libelle} — durée totale estimée : {fiche['duree_totale']}. {organismes}".strip()))
        if fiche["base_legale"]:
            chunks.append(chunk(doc, "base_legale", "Base légale citée par le portail", f"{libelle} — base légale : " + " ; ".join(fiche["base_legale"]) + "."))
        sortie.append({**doc, "chunks": chunks})
        par_procedure[fiche["procedure_id"]].append(
            {
                "fiche": fiche["fiche"],
                "libelle": libelle,
                "etapes": etapes,
                "pieces": pieces,
                "cout": fiche["cout"],
                "duree_totale": fiche["duree_totale"],
                "en_revision": fiche["en_revision"],
                "chunks": [c["id"] for c in chunks],
            }
        )
    return sortie, par_procedure


def _extrait(entree: dict | str, chunk_defaut: str | None, chunks: dict, contexte: str) -> dict:
    """Vérifie qu'une pièce ou une étape est un extrait exact du chunk cité."""
    texte = entree if isinstance(entree, str) else entree["texte"]
    identifiant = chunk_defaut if isinstance(entree, str) else entree["chunk"]
    if identifiant not in chunks:
        raise ErreurKB(f"{contexte} : chunk inconnu {identifiant!r}")
    if normaliser(texte) not in normaliser(chunks[identifiant]["texte"]):
        raise ErreurKB(f"{contexte} : extrait absent de {identifiant} : {texte!r}")
    return {"texte": texte, "chunk": identifiant}


def construire_catalogue(chunks: dict, fiches: dict) -> list[dict]:
    identifiants = [d["id"] for d in DEMARCHES]
    if len(identifiants) != len(set(identifiants)):
        raise ErreurKB("identifiants de démarche dupliqués")
    for mot, cibles in AMBIGUS.items():
        for cible in cibles:
            if cible not in identifiants:
                raise ErreurKB(f"AMBIGUS[{mot!r}] vise une démarche inconnue : {cible}")

    par_procedure = defaultdict(list)
    for identifiant, c in chunks.items():
        par_procedure[c["procedure_id"]].append(identifiant)

    catalogue = []
    for demarche in DEMARCHES:
        cid = demarche["id"]
        entree = {k: v for k, v in demarche.items() if k not in ("pieces", "etapes", "cas")}
        entree["mots_cles"] = [normaliser(m) for m in demarche["mots_cles"]]
        entree["fiches"] = fiches.get(cid, [])
        entree["chunks"] = sorted(par_procedure.get(cid, []))
        entree["pieces"] = [_extrait(x, None, chunks, f"{cid}/pieces") for x in demarche.get("pieces", [])]
        entree["etapes"] = [_extrait(x, None, chunks, f"{cid}/etapes") for x in demarche.get("etapes", [])]

        cas_sortie = []
        fiches_connues = {f["fiche"] for f in entree["fiches"]}
        for cas in demarche.get("cas", []):
            sortie_cas = {k: v for k, v in cas.items() if k != "pieces"}
            sortie_cas["mots"] = [normaliser(m) for m in cas["mots"]] + [
                normaliser(cas["libelle"]),
                normaliser(cas["libelle_en"]),
            ]
            if "fiche" in cas and cas["fiche"] not in fiches_connues:
                raise ErreurKB(f"{cid}/{cas['id']} : fiche inconnue {cas['fiche']}")
            sortie_cas["pieces"] = [
                _extrait(p, cas.get("chunk"), chunks, f"{cid}/{cas['id']}") for p in cas.get("pieces", [])
            ]
            cas_sortie.append(sortie_cas)
        entree["cas"] = cas_sortie

        for identifiant in demarche.get("chunks_complementaires", []):
            if identifiant not in chunks:
                raise ErreurKB(f"{cid} : chunk complémentaire inconnu {identifiant}")

        if demarche["statut"] == "lacune":
            if entree["chunks"] or entree["fiches"]:
                raise ErreurKB(f"{cid} est une lacune mais possède des sources")
            if not demarche.get("note_lacune"):
                raise ErreurKB(f"{cid} : lacune sans explication")
        elif not entree["chunks"]:
            raise ErreurKB(f"{cid} : démarche sans aucune source")
        catalogue.append(entree)

    # references_internationales : textes étrangers pour l'analyse d'écarts, hors catalogue
    # citoyen, pour que l'agent ne les cite jamais comme droit camerounais.
    orphelins = set(par_procedure) - set(identifiants) - {"etat_civil", "references_internationales"}
    if orphelins:
        raise ErreurKB(f"chunks rattachés à une démarche inconnue : {sorted(orphelins)}")
    return catalogue


def controler_chunks(documents: list[dict]) -> dict:
    chunks = {}
    for doc in documents:
        if not doc["source_url"].startswith("https://"):
            raise ErreurKB(f"{doc['doc']} : source_url invalide")
        for c in doc["chunks"]:
            if c["id"] in chunks:
                raise ErreurKB(f"identifiant dupliqué : {c['id']}")
            if len(c["texte"].strip()) < 20:
                raise ErreurKB(f"{c['id']} : texte trop court")
            if c["statut_verification"] not in ("verifie", "a_verifier"):
                raise ErreurKB(f"{c['id']} : statut inconnu")
            chunks[c["id"]] = c
    return chunks


def table_catalogue(catalogue: list[dict]) -> str:
    libelles = {"couvert": "Couvert", "partiel": "Partiel", "lacune": "Lacune"}
    compteur = Counter(d["statut"] for d in catalogue)
    lignes = [
        "# Catalogue des démarches GOVIA",
        "",
        "Fichier généré par `scripts/build_kb.py`, ne pas modifier à la main.",
        "",
        f"{len(catalogue)} démarches : {compteur['couvert']} couvertes, {compteur['partiel']} partielles, "
        f"{compteur['lacune']} lacunes.",
        "",
        "- **Couvert** : appuyée sur un texte ou une fiche de portail relus à la source.",
        "- **Partiel** : appuyée sur une reproduction ancienne ou incomplète, à confirmer.",
        "- **Lacune** : aucune source ouverte retrouvée ; l'agent le dit et n'invente rien.",
        "",
        "| Domaine | Démarche | Statut | Autorité | Sources |",
        "|---|---|---|---|---|",
    ]
    for d in sorted(catalogue, key=lambda x: (x["domaine"], x["nom"])):
        lignes.append(
            f"| {d['domaine']} | {d['nom']} | {libelles[d['statut']]} | {d['autorite']} | {len(d['chunks'])} chunks |"
        )
    lignes += ["", "## Lacunes à documenter dans l'analyse d'écarts", ""]
    for d in catalogue:
        if d["statut"] == "lacune":
            lignes.append(f"- **{d['nom']}** : {d['note_lacune']}")
    return "\n".join(lignes) + "\n"


def generer() -> dict[Path, str]:
    documents_ereg, fiches = documents_eregulations()
    documents = documents_textes() + documents_ereg
    chunks = controler_chunks(documents)
    catalogue = construire_catalogue(chunks, fiches)

    fichiers: dict[Path, str] = {}
    for doc in documents:
        total = len(doc["chunks"])
        lignes = [
            json.dumps({**c, "chunk_index": i, "total_chunks": total}, ensure_ascii=False)
            for i, c in enumerate(doc["chunks"])
        ]
        fichiers[KB_DIR / f"{doc['doc']}.jsonl"] = "\n".join(lignes) + "\n"

    index = {
        "base": "GOVIA Cameroun — Base de connaissances",
        "descriptif": "Textes réglementaires et fiches de procédures camerounais, découpés en chunks machine-readable pour RAG. Chaque chunk indique sa source et son statut de vérification.",
        "langues": sorted({c["langue"] for c in chunks.values()}),
        "total_chunks": len(chunks),
        "total_documents": len(documents),
        "chunks_par_statut": dict(Counter(c["statut_verification"] for c in chunks.values())),
        "chunks_par_type_source": dict(Counter(c["type_source"] for c in chunks.values())),
        "demarches_par_statut": dict(Counter(d["statut"] for d in catalogue)),
        "documents": [
            {
                "doc": d["doc"],
                "titre": d["titre"],
                "autorite": d["autorite"],
                "source_url": d["source_url"],
                "date_publication": d.get("date_publication", ""),
                "type_source": d["type_source"],
                "statut_verification": d["statut_verification"],
                "methode_verification": d.get("methode", ""),
                "note": d.get("note", ""),
                "chunks": len(d["chunks"]),
                "fichier": f"{d['doc']}.jsonl",
            }
            for d in documents
        ],
        "note_legale": "Documents réels et ouverts uniquement. Une démarche sans source ouverte est documentée comme lacune dans catalogue.json. GOVIA ne fournit pas de conseil juridique : le texte officiel et l'administration compétente font foi.",
    }
    fichiers[KB_DIR / "index.json"] = json.dumps(index, ensure_ascii=False, indent=2) + "\n"
    fichiers[KB_DIR / "catalogue.json"] = (
        json.dumps({"ambigus": AMBIGUS, "demarches": catalogue}, ensure_ascii=False, indent=1) + "\n"
    )
    fichiers[DOC_MD] = table_catalogue(catalogue)
    return fichiers


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="vérifie sans écrire")
    args = parser.parse_args()

    try:
        fichiers = generer()
    except ErreurKB as erreur:
        print(f"BASE REFUSÉE : {erreur}", file=sys.stderr)
        return 1

    existants = set(KB_DIR.glob("*.jsonl")) | {KB_DIR / "index.json", KB_DIR / "catalogue.json", DOC_MD}
    obsoletes = sorted(p for p in existants if p not in fichiers and p.exists())

    if args.check:
        ecarts = [p for p, c in fichiers.items() if not p.exists() or p.read_text(encoding="utf-8") != c]
        if ecarts or obsoletes:
            print("Base non synchronisée :", *map(str, ecarts + obsoletes), sep="\n  ", file=sys.stderr)
            return 1
        print(f"Base à jour : {len(fichiers)} fichiers contrôlés.")
        return 0

    for chemin in obsoletes:
        chemin.unlink()
        print(f"retiré : {chemin.name}")
    KB_DIR.mkdir(exist_ok=True)
    for chemin, contenu in fichiers.items():
        chemin.parent.mkdir(parents=True, exist_ok=True)
        chemin.write_text(contenu, encoding="utf-8")
    index = json.loads(fichiers[KB_DIR / "index.json"])
    print(
        f"{index['total_chunks']} chunks, {index['total_documents']} documents ; "
        f"vérification : {index['chunks_par_statut']} ; démarches : {index['demarches_par_statut']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
