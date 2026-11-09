#!/usr/bin/env python3
"""Mesure le seuil GOVIA_MIN_SCORE sur des questions étiquetées et écrit docs/calibration_seuil.md.

Le seuil décide si une question sans démarche identifiée reçoit des passages proches ou le message
« je n'ai pas trouvé ». L'API doit tourner avec GOVIA_MIN_SCORE=0, sinon les scores bas sont filtrés :

    docker run -d -p 127.0.0.1:18000:8000 -e GOVIA_USE_LLM=0 -e GOVIA_MIN_SCORE=0 govia-fastapi:latest
    python scripts/calibrer_seuil.py http://127.0.0.1:18000

Ce jeu de questions est court : il sert à choisir un seuil raisonnable, pas à mesurer la qualité.
"""
import json
import sys
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

API = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://127.0.0.1:18000"
SORTIE = Path(__file__).resolve().parent.parent / "docs" / "calibration_seuil.md"

HORS_SUJET = [
    "Quel est le prix du pain au marché ?",
    "Quelle heure est-il ?",
    "Qui a gagné la coupe du monde ?",
    "Comment faire un gâteau au chocolat ?",
    "Quel temps fait-il à Douala ?",
    "Comment réparer mon téléphone ?",
    "Quelle est la meilleure équipe de football du Cameroun ?",
    "Comment soigner le paludisme ?",
    "Donne-moi une recette de ndolé",
    "Raconte-moi une blague",
    "What is the capital of France?",
    "Recommend me a good movie",
    "How do I learn to play guitar?",
    "What is the weather like today?",
]

# Formulations volontairement éloignées des mots-clés du catalogue.
DANS_LE_PERIMETRE = [
    ("Quelles sanctions si j'envoie des données à l'étranger sans autorisation ?", {"protection_donnees"}),
    ("Ai-je le droit de refuser une décision prise par une machine ?", {"protection_donnees"}),
    ("À partir de quel âge peut-on avoir une pièce d'identité ?", {"cni"}),
    ("Combien de temps ma carte d'identité reste-t-elle valable ?", {"cni"}),
    ("Que faire si on m'a volé mes papiers ?", {"cni", "passeport"}),
    ("Mon employeur doit-il me donner un contrat écrit ?", {"contrat_travail"}),
    ("Comment devenir propriétaire légal d'un terrain ?", {"titre_foncier"}),
    ("Je vends au marché, quel impôt dois-je payer ?", {"impot_liberatoire", "patente"}),
    ("Ma mère âgée peut-elle toucher une retraite ?", {"cnps_pension_vieillesse"}),
    ("Mon mari est mort, ai-je droit à une pension ?", {"cnps_pension_survivant"}),
    ("Combien de temps pour déclarer un nouveau-né ?", {"acte_naissance"}),
    ("Qui célèbre un mariage à la mairie ?", {"acte_mariage"}),
    ("Je veux ouvrir une boutique", {"commercant_individuel", "creation_societe"}),
    ("Quels papiers pour bâtir une maison ?", {"permis_construire", "permis_implanter"}),
    ("Comment faire venir des marchandises de l'étranger ?", {"fichier_importateurs"}),
    ("How long is a passport valid?", {"passeport"}),
    ("What can a passport application be refused for?", {"passeport"}),
    ("Is an electronic signature legally valid?", {"signature_electronique"}),
    ("Can personal data be sent abroad?", {"protection_donnees"}),
    ("Who may ask for a nationality certificate?", {"certificat_nationalite"}),
]


def chercher(question: str, n: int = 5) -> list[dict]:
    url = f"{API}/kb/search?q={urllib.parse.quote(question)}&n={n}"
    with urllib.request.urlopen(url, timeout=60) as reponse:
        return json.load(reponse)["results"]


def score_max(passages: list[dict]) -> float:
    return max((p["score"] for p in passages), default=0.0)


# Garde-fous : un mauvais réglage ou une faute d'identifiant ne doit pas produire un faux tableau.
with urllib.request.urlopen(f"{API}/", timeout=60) as reponse:
    etat = json.load(reponse)
if etat["recherche"] != "vectoriel":
    sys.exit(f"Recherche « {etat['recherche']} » : la calibration n'a de sens qu'avec ChromaDB.")
with urllib.request.urlopen(f"{API}/kb/catalogue", timeout=60) as reponse:
    connues = {d["id"] for d in json.load(reponse)}
inconnues = set().union(*(attendues for _, attendues in DANS_LE_PERIMETRE)) - connues
if inconnues:
    sys.exit(f"Démarches inconnues dans le jeu de questions : {sorted(inconnues)}")
if not chercher(HORS_SUJET[0]):
    sys.exit("Aucun passage renvoyé : lancez l'API avec GOVIA_MIN_SCORE=0.")

hors = [(q, score_max(chercher(q))) for q in HORS_SUJET]
dedans = []
for question, attendues in DANS_LE_PERIMETRE:
    passages = chercher(question)
    dedans.append(
        {
            "question": question,
            "score": score_max(passages),
            "trouve_top1": bool(passages) and passages[0]["procedure_id"] in attendues,
            "trouve_top3": any(p["procedure_id"] in attendues for p in passages[:3]),
            "proposee": passages[0]["procedure_id"] if passages else "aucune",
        }
    )

lignes_seuils = []
meilleur = None
for centieme in range(20, 71, 5):
    seuil = centieme / 100
    faux_positifs = sum(score >= seuil for _, score in hors)
    rappel = sum(d["score"] >= seuil and d["trouve_top3"] for d in dedans)
    lignes_seuils.append(f"| {seuil:.2f} | {faux_positifs}/{len(hors)} | {rappel}/{len(dedans)} |")
    # Une question hors sujet qui reçoit des passages sonne faux : à égalité, le seuil le plus strict gagne.
    note = (rappel - 2 * faux_positifs, seuil)
    if meilleur is None or note >= meilleur[0]:
        meilleur = (note, seuil, faux_positifs, rappel)

_, seuil_retenu, fp, rappel = meilleur
top1 = sum(d["trouve_top1"] for d in dedans)
top3 = sum(d["trouve_top3"] for d in dedans)

texte = f"""# Calibration du seuil de recherche

Générée le {date.today().isoformat()} par `scripts/calibrer_seuil.py`, avec le modèle `paraphrase-multilingual-MiniLM-L12-v2` et ChromaDB dans l'image Docker du backend.

Le seuil `GOVIA_MIN_SCORE` ne joue que pour une question sans démarche identifiée : il décide entre proposer des passages proches et répondre qu'aucune démarche n'a été trouvée. Une recherche restreinte à une démarche n'y est pas soumise.

**Seuil le mieux noté : {seuil_retenu:.2f}**, avec {fp} question(s) hors sujet sur {len(hors)} qui reçoivent des passages et {rappel} question(s) du périmètre sur {len(dedans)} qui reçoivent un passage de la bonne démarche.

Sans seuil, le bon passage arrive en tête pour {top1} questions sur {len(dedans)}, et dans les trois premiers pour {top3} sur {len(dedans)}.

Ce jeu de {len(hors) + len(dedans)} questions, écrit par l'équipe, permet de choisir un seuil. Il ne mesure pas la qualité de la recherche en conditions réelles.

| Seuil | Hors sujet avec passages | Périmètre avec le bon passage |
|---|---|---|
{chr(10).join(lignes_seuils)}

## Questions hors sujet

| Question | Meilleur score |
|---|---|
{chr(10).join(f"| {q} | {s:.3f} |" for q, s in sorted(hors, key=lambda x: -x[1]))}

## Questions du périmètre

| Question | Meilleur score | Démarche en tête | Bonne démarche dans le top 3 |
|---|---|---|---|
{chr(10).join(f"| {d['question']} | {d['score']:.3f} | {d['proposee']} | {'oui' if d['trouve_top3'] else 'non'} |" for d in sorted(dedans, key=lambda x: -x['score']))}
"""
SORTIE.write_text(texte, encoding="utf-8")
print(texte)
