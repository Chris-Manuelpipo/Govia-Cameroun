"""Masquage des données personnelles avant tout envoi au modèle.

Au sens de l'article 5 de la Loi n° 2024/017, ce traitement relève de la
pseudonymisation : il remplace les identifiants directs repérables par des marqueurs.
Il n'équivaut pas à une anonymisation et ne garantit pas de tout détecter, par exemple
un nom cité sans libellé dans une phrase libre. D'où trois règles complémentaires :
le modèle reste local par défaut, rien n'est conservé, et l'interface demande de ne
pas transmettre de vraies pièces sur ce prototype.
"""
from __future__ import annotations

import re

MOIS = (
    "janvier|fevrier|février|mars|avril|mai|juin|juillet|aout|août|septembre|octobre|novembre|decembre|décembre|"
    "january|february|march|april|may|june|july|august|september|october|november|december"
)

# Fin de valeur : fin de ligne, ponctuation forte ou libellé suivant.
_LIBELLES_IDENTITE = (
    r"nom(?:\s+de\s+jeune\s+fille)?|noms?\s+et\s+pr[ée]noms?|pr[ée]noms?|surname|given\s+names?|first\s+name|last\s+name|"
    r"name|p[èe]re|m[èe]re|father|mother|d[ée]clarant|titulaire|requ[ée]rant"
)

_REGLES: list[tuple[re.Pattern[str], str]] = [
    # Courriel
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "[EMAIL]"),
    # Présentation spontanée : « je m'appelle Jean Mballa »
    (
        re.compile(
            r"\b((?i:je\s+m['’]appelle|mon\s+nom\s+est|my\s+name\s+is|i\s+am\s+called))\s+"
            r"((?:[A-ZÀ-Ý][\w'’-]*\s*){1,5})"
        ),
        r"\1 [NOM] ",
    ),
    # Valeurs introduites par un libellé d'identité
    (
        re.compile(rf"(?i)\b({_LIBELLES_IDENTITE})\s*[:=]\s*[^\n,;:]+"),
        r"\1 : [NOM]",
    ),
    # Adresse et lieu introduits par un libellé
    (re.compile(r"(?i)\b(adresse|address|domicile|r[ée]sidence|quartier)\s*[:=]\s*[^\n;]+"), r"\1 : [ADRESSE]"),
    (re.compile(r"(?i)\b(lieu\s+de\s+naissance|place\s+of\s+birth)\s*[:=]\s*[^\n,;]+"), r"\1 : [LIEU]"),
    (re.compile(r"(?i)\b(n[ée]e?\s+[àa]|born\s+(?:in|at))\s+[A-ZÀ-Ý][\w'’-]*(?:[\s-][A-ZÀ-Ý][\w'’-]*)*"), r"\1 [LIEU]"),
    # Numéro de contribuable : lettre, 12 chiffres, lettre
    (re.compile(r"\b[A-Z]\d{12}[A-Z]\b"), "[NIU]"),
    # Téléphone camerounais : 9 chiffres commençant par 2 ou 6, avec ou sans +237
    (re.compile(r"(?<![\d])(?:\+?237[\s.-]*)?[26]\d{2}(?:[\s.-]*\d){6}(?![\d])"), "[TELEPHONE]"),
    # Dates numériques et en toutes lettres
    (re.compile(r"\b\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}\b"), "[DATE]"),
    (re.compile(rf"(?i)\b\d{{1,2}}(?:er)?\s+(?:{MOIS})\s+\d{{4}}\b"), "[DATE]"),
    (re.compile(rf"(?i)\b(?:{MOIS})\s+\d{{1,2}},?\s+\d{{4}}\b"), "[DATE]"),
    # Identifiants : au moins 6 chiffres (hors montants) ou code mêlant lettres et chiffres
    (re.compile(r"(?i)\b\d{6,}\b(?!\s*(?:f\s?cfa|cfa|xaf|francs?))"), "[ID]"),
    (re.compile(r"\b(?=[A-Z0-9-]*\d)(?=[A-Z0-9-]*[A-Z])[A-Z0-9-]{6,20}\b"), "[ID]"),
]


_MARQUEUR = re.compile(r"\s*\[(?:NOM|EMAIL|ADRESSE|LIEU|NIU|TELEPHONE|DATE|ID)\]", re.I)


def retirer_marqueurs(texte: str) -> str:
    """Retire les marqueurs de masquage qu'un modèle aurait recopiés (« Bonjour [NOM], » devient « Bonjour, »)."""
    return re.sub(r"[ \t]{2,}", " ", _MARQUEUR.sub("", texte)).strip()


def masquer(texte: str) -> str:
    """Remplace les identifiants directs repérables par des marqueurs."""
    for motif, remplacement in _REGLES:
        texte = motif.sub(remplacement, texte)
    return re.sub(r"[ \t]{2,}", " ", texte).strip()


_CHAMPS = {
    "nom": r"(?:noms?|surname|last\s+name)",
    "prenoms": r"(?:pr[ée]noms?|given\s+names?|first\s+name)",
    "date_naissance": r"(?:date\s+de\s+naissance|date\s+of\s+birth|n[ée]e?\s+le)",
    "lieu_naissance": r"(?:lieu\s+de\s+naissance|place\s+of\s+birth|n[ée]e?\s+[àa])",
    "profession": r"(?:profession|occupation)",
    "adresse": r"(?:adresse|address|domicile)",
}


def extraire_champs(texte: str) -> dict[str, str]:
    """Repère les champs d'un document pour pré-remplir le formulaire du citoyen.

    Le résultat n'est renvoyé qu'à la personne concernée, pour qu'elle le vérifie : il
    n'est ni journalisé, ni conservé, ni transmis au modèle.
    """
    champs = {}
    for nom, libelle in _CHAMPS.items():
        motif = re.search(rf"(?im)^\s*{libelle}\s*[:=]?\s*(?P<valeur>[^\n:]+)$", texte)
        if motif and motif.group("valeur").strip():
            champs[nom] = motif.group("valeur").strip()
    return champs
