#!/usr/bin/env python3
"""Extrait les fiches de procédures du portail eRegulations Yaoundé.

Le portail (MINPMEESA, appui PNUD/CNUCED) publie étape par étape des démarches
administratives : création d'entreprise, CNPS, impôts, permis de construire,
foncier, commerce extérieur. Pour chaque fiche, on conserve mot pour mot :
étapes, résultats, documents nécessaires, coût, durée et base légale.

Les noms et téléphones d'agents publiés sur les pages d'étapes ne sont jamais
récupérés : seule la page de synthèse de la procédure est lue.

Usage :
    python scripts/fetch_eregulations.py                # télécharge et extrait
    python scripts/fetch_eregulations.py --from-dir D   # relit des pages déjà
                                                        # enregistrées (D/<id>_<menu>.html)
Sortie : scripts/kb_data/eregulations_yaounde.json
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
import urllib.request
from datetime import date
from pathlib import Path

BASE = "https://yaounde.eregulations.org"
OUT = Path(__file__).parent / "kb_data" / "eregulations_yaounde.json"

# (procedure_id du catalogue GOVIA, identifiant portail, identifiant de menu, libellé)
FICHES = [
    # Création d'entreprise
    ("commercant_individuel", 180, 135, "S'enregistrer comme commerçant individuel — dossier au CFCE"),
    ("commercant_individuel", 181, 136, "S'enregistrer comme commerçant individuel — dossier en ligne"),
    ("creation_societe", 186, 141, "Créer une société — statuts notariés, dossier au CFCE"),
    ("creation_societe", 184, 139, "Créer une société — statuts sous seing privé, dossier au CFCE"),
    ("creation_societe", 185, 140, "Créer une société — statuts sous seing privé, dossier en ligne"),
    ("creation_succursale", 158, 127, "Créer une succursale"),
    # Protection sociale
    ("cnps_immatriculation", 93, 53, "Immatriculation de l'entreprise et des salariés à la CNPS"),
    ("cnps_cotisations", 94, 7, "Paiement des cotisations sociales à la CNPS"),
    ("cnps_allocations_familiales", 95, 49, "Allocations familiales"),
    ("cnps_allocations_familiales", 96, 50, "Allocations prénatales"),
    ("cnps_maternite", 97, 51, "Indemnités journalières de congé de maternité"),
    ("cnps_maternite", 98, 52, "Allocations de maternité"),
    ("cnps_risques_professionnels", 102, 11, "Couverture des risques et maladies professionnels"),
    ("cnps_pension_vieillesse", 100, 54, "Pension vieillesse et invalidité"),
    ("cnps_pension_survivant", 101, 55, "Pension de survivant"),
    # Impôts
    ("impot_liberatoire", 20, 13, "Impôt libératoire"),
    ("impot_tva", 33, 114, "Taxe sur la valeur ajoutée (TVA)"),
    ("impot_irpp", 31, 116, "Impôt sur le revenu des personnes physiques (IRPP)"),
    ("impot_societes", 32, 117, "Impôt sur les sociétés (IS)"),
    ("patente", 36, 120, "La patente"),
    ("taxe_fonciere", 37, 121, "Taxe sur la propriété foncière (TPF)"),
    # Construire
    ("permis_construire", 169, 129, "Obtention du plan de masse et de situation"),
    ("permis_construire", 170, 130, "Obtention du certificat d'urbanisme et d'accessibilité"),
    ("permis_construire", 171, 131, "Obtention du certificat de propriété"),
    ("permis_construire", 172, 132, "Dépôt du dossier et paiement des frais de permis de construire"),
    ("permis_implanter", 108, 79, "Permis d'implanter"),
    # Foncier
    ("titre_foncier", 40, 22, "Obtention de la propriété par voie de concession (domaine national)"),
    ("titre_foncier", 44, 23, "Obtention de la propriété par vente de gré à gré (domaine privé de l'État)"),
    ("titre_foncier", 46, 26, "Obtention du titre foncier suite à une mutation"),
    ("titre_foncier", 47, 25, "Obtention du titre foncier suite à un morcellement"),
    # Commerce extérieur
    ("fichier_importateurs", 135, 89, "Inscription au fichier des importateurs"),
    ("fichier_exportateurs", 130, 91, "Inscription au fichier des exportateurs"),
]

# Lignes d'interface du portail, jamais du contenu réglementaire.
_BRUIT = {
    "Nouveau ticket", "Commentaires", "Aperçu et impression", "Calculer les coûts", "dont :",
    "min", "max", "XAF", "or", "x",
}
_SECTIONS = {
    "resultats": r"^Résultats de la procédure",
    "documents": r"^Documents nécessaires",
    "cout": r"^Combien ça coûte",
    "duree": r"^Durée$",
    "base_legale": r"^Base légale$",
}


def page_en_lignes(page: str) -> list[str]:
    """Convertit une page HTML en lignes de texte significatives."""
    page = re.sub(r"(?is)<(script|style|nav|footer).*?</\1>", " ", page)
    page = re.sub(r"(?i)<(br|/p|/li|/tr|/h\d|/div)[^>]*>", "\n", page)
    page = re.sub(r"<[^>]+>", " ", page)
    page = html.unescape(page)
    lignes = [re.sub(r"\s+", " ", ligne).strip() for ligne in page.split("\n")]
    return [ligne for ligne in lignes if ligne]


def _est_bruit(ligne: str) -> bool:
    return (
        ligne in _BRUIT
        or ligne.startswith("Commentaires sur")
        or re.fullmatch(r"\d{1,2}", ligne) is not None
    )


def _section(lignes: list[str], debut: str, fins: list[str]) -> list[str]:
    i = next((k for k, x in enumerate(lignes) if re.search(debut, x)), None)
    if i is None:
        return []
    bloc = []
    for ligne in lignes[i + 1:]:
        if any(re.search(fin, ligne) for fin in fins):
            break
        if not _est_bruit(ligne):
            bloc.append(ligne)
    return bloc


def _etapes(lignes: list[str]) -> list[str]:
    """Étapes dans l'ordre publié ; les alternatives (« or ») sont préfixées par « ou : »."""
    i = next((k for k, x in reversed(list(enumerate(lignes))) if x == "Liste des étapes"), None)
    if i is None:
        return []
    etapes, alternative = [], False
    bloc = []
    for ligne in lignes[i + 1:]:
        if ligne.startswith(("Propriétés", "Imprimer", "Commentaires")) or ligne == "Aperçu et impression":
            break
        bloc.append(ligne)
    for k, ligne in enumerate(bloc):
        suivante = bloc[k + 1] if k + 1 < len(bloc) else ""
        if ligne == "or":
            alternative = True
            continue
        if (
            ligne.startswith("(Nombre total")
            or re.fullmatch(r"\d+ ?\)|\(\d+\)|[A-Z]|\d+", ligne)
            or re.fullmatch(r"\(\d+\)", suivante)  # intitulé de rubrique, pas une étape
        ):
            continue
        etapes.append(f"ou : {ligne}" if alternative else ligne)
        alternative = False
    return etapes


def _cout(lignes: list[str]) -> list[str]:
    """Reconstitue le coût total et le détail : « 150 XAF pour ... », « 1 % du coût ... »."""
    i = next((k for k, x in enumerate(lignes) if x.startswith("Combien ça coûte")), None)
    if i is None:
        return []
    bloc = []
    for ligne in lignes[i + 1:]:
        if ligne == "Durée" or ligne.startswith("Commentaires sur les coûts"):
            break
        if ligne != "Nouveau ticket" and not ligne.startswith(("changer les valeurs", "Calculer les coûts")):
            bloc.append(ligne)
    if "Détails du coût" in bloc:
        k = bloc.index("Détails du coût")
        total, details = bloc[:k], bloc[k + 1:]
    else:
        total, details = bloc, []
    sortie = [" ".join(total)] if total else []
    nombre = r"[\d][\d,. ]*"
    k = 0
    while k < len(details):
        jeton = details[k]
        suivant = details[k + 1] if k + 1 < len(details) else ""
        if re.fullmatch(nombre, jeton) and suivant == "%":
            libelle = next((x for x in details[k + 2:] if re.match(r"[^\W\d]", x) and x not in ("XAF", "CFA")), "")
            sortie.append(f"{jeton} % {libelle}".strip())
            k = details.index(libelle, k) + 2 if libelle else k + 2
        elif jeton == "XAF" and re.fullmatch(nombre, suivant):
            libelle = details[k + 2] if k + 2 < len(details) else ""
            sortie.append(f"{suivant} XAF {libelle}".strip())
            k += 3
        else:
            k += 1
    return [re.sub(r"\s+", " ", x).strip() for x in sortie]


def _ou_aller(lignes: list[str]) -> list[str]:
    bloc = _section(lignes, r"^Où aller", [r"^Résultats de la procédure", r"^Documents nécessaires"])
    return [
        x for x in bloc
        if not x.startswith("Voici les institutions") and not re.fullmatch(r"\(x \d+\)", x)
    ]


def extraire_fiche(page: str) -> dict:
    """Extrait les rubriques d'une fiche, sans interprétation."""
    lignes = page_en_lignes(page)
    titre = max((k for k, x in enumerate(lignes) if x == "Liste des étapes"), default=0)
    fins = list(_SECTIONS.values()) + [r"^eRegulations ", r"^Powered by"]

    resultats = [
        x for x in _section(lignes, _SECTIONS["resultats"], fins)
        if not x.startswith("L'objectif de la procédure")
    ]
    documents = [
        x for x in _section(lignes, _SECTIONS["documents"], fins)
        if not x.startswith("Les documents avec un bandeau")
        and not re.fullmatch(r"\(x \d+\)|[a-zA-Z]", x)
    ]
    duree_brut = _section(lignes, _SECTIONS["duree"], fins)
    duree_totale = ""
    if "Durée totale:" in duree_brut:
        k = duree_brut.index("Durée totale:")
        duree_totale = " à ".join(duree_brut[k + 1:k + 3])
    base_legale = [
        x for x in _section(lignes, _SECTIONS["base_legale"], fins)
        if not x.startswith("Ces textes de loi")
    ]
    return {
        "en_revision": any("REVISION" in x.upper() for x in lignes[max(0, titre - 3):titre]),
        "etapes": _etapes(lignes),
        "ou_aller": _ou_aller(lignes),
        "resultats": resultats,
        "documents": documents,
        "cout": _cout(lignes),
        "duree_totale": duree_totale,
        "base_legale": base_legale,
    }


def telecharger(url: str, essais: int = 3) -> str:
    requete = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (GOVIA KB builder)"})
    for essai in range(essais):
        try:
            with urllib.request.urlopen(requete, timeout=60) as reponse:
                return reponse.read().decode("utf-8", errors="ignore")
        except OSError as erreur:
            if essai == essais - 1:
                raise
            print(f"  nouvel essai après erreur : {erreur}", file=sys.stderr)
            time.sleep(3)
    raise RuntimeError("inaccessible")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from-dir", type=Path, help="relire les pages déjà enregistrées")
    args = parser.parse_args()

    fiches, echecs = [], []
    for procedure_id, pid, menu, libelle in FICHES:
        url = f"{BASE}/procedure/{pid}/{menu}?l=fr"
        fichier = args.from_dir / f"{pid}_{menu}.html" if args.from_dir else None
        try:
            if fichier and fichier.exists():
                page = fichier.read_text(encoding="utf-8", errors="ignore")
            else:
                page = telecharger(url)
                if fichier:
                    fichier.write_text(page, encoding="utf-8")
        except OSError as erreur:
            echecs.append(f"{pid}/{menu} ({erreur})")
            continue
        fiche = extraire_fiche(page)
        if not fiche["etapes"]:
            echecs.append(f"{pid}/{menu} (aucune étape extraite)")
            continue
        fiches.append(
            {"procedure_id": procedure_id, "fiche": f"{pid}_{menu}", "libelle": libelle, "source_url": url, **fiche}
        )
        print(f"ok {pid}/{menu} : {libelle}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {"portail": BASE, "date_extraction": date.today().isoformat(), "fiches": fiches},
            ensure_ascii=False,
            indent=1,
        ),
        encoding="utf-8",
    )
    print(f"{len(fiches)} fiches écrites dans {OUT}")
    if echecs:
        print("ÉCHECS :", *echecs, sep="\n  ", file=sys.stderr)
    return 1 if echecs else 0


if __name__ == "__main__":
    sys.exit(main())
