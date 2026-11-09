"""Agent orchestrateur : coordonne les trois autres agents et gère le flux de travail.

GOVIA repose sur quatre agents :
- l'orchestrateur (ce module) enchaîne les étapes et compose la réponse au citoyen ;
- l'agent d'analyse (`analyse.py`) comprend la demande et classe la procédure ;
- l'agent de recherche (`recherche.py`) extrait pièces, étapes et citations (RAG) ;
- l'agent de validation (`auditor.py`) vérifie les informations, la conformité et les sources.

Déroulé de la version gouvernée (B) :
1. analyse : refuser une demande illicite, identifier la démarche et le cas, ou demander
   une précision au lieu de deviner, ou signaler une lacune sans inventer ;
2. recherche : rassembler pièces, étapes et citations depuis le catalogue et le RAG ;
3. rédaction : le LLM local rédige sur la seule base de ces sources, données masquées ;
4. validation : l'auditeur contrôle le brouillon ; un texte rejeté est remplacé par une
   réponse composée uniquement des extraits sourcés. La réponse finale est contrôlée
   une seconde fois avant publication (voir `main.py`).

La version A (sans gouvernance) interroge le LLM seul, pour la comparaison du rapport.
Aucun agent ne soumet rien à la place du citoyen.
"""
from __future__ import annotations

import os
from typing import List, Optional

from analyse import AgentAnalyse, Analyse
from auditor import AgentValidation
from catalogue import Catalogue
from privacy import masquer
from recherche import AgentRecherche

TEXTES = {
    "FR": {
        "demarche": "Démarche",
        "cas": "Votre cas",
        "etapes": "Étapes",
        "pieces": "Pièces à fournir",
        "cout": "Coût",
        "duree": "Durée totale estimée",
        "extraits": "Ce que disent les textes",
        "sources": "Textes et sources",
        "partiel": "Attention : cette démarche s'appuie sur une reproduction ancienne ou incomplète. Faites-la confirmer par l'administration.",
        "a_verifier": "Attention : certaines informations viennent de sources que nous n'avons pas encore pu vérifier.",
        "responsable": "Vous restez responsable des informations que vous validez et soumettez : l'administration compétente et le texte officiel font foi.",
        "clarifier": "Plusieurs démarches correspondent à votre demande. Laquelle vous concerne ?",
        "hors": "Je n'ai pas trouvé de démarche correspondant à votre demande dans ma base. Pouvez-vous préciser la démarche ou l'administration concernée ?",
        "proches": "Je n'ai pas identifié de démarche précise, mais ces textes pourraient vous aider :",
        "refus": "Je ne peux pas aider à contourner une procédure ni à falsifier un document. Je peux en revanche vous expliquer la démarche officielle.",
        "lacune": "Je connais cette démarche, mais je n'ai pas de source ouverte fiable pour en détailler les étapes. Je préfère vous le dire plutôt que d'inventer une procédure.",
        "autorite": "Administration à contacter",
        "orientation": "Guide pratique non officiel, à vérifier",
        "formulaire": "Je peux préparer le formulaire pour que vous le complétiez et le vérifiiez. Vous seul le soumettez sur le site officiel.",
        "ecarte": "Le texte rédigé par le modèle a été écarté par l'auditeur ; voici les seuls éléments tirés des sources.",
    },
    "EN": {
        "demarche": "Procedure",
        "cas": "Your situation",
        "etapes": "Steps (as published, in French)",
        "pieces": "Documents required (as published, in French)",
        "cout": "Cost",
        "duree": "Estimated total duration",
        "extraits": "What the texts say (as published)",
        "sources": "Texts and sources",
        "partiel": "Warning: this procedure relies on an old or incomplete reproduction. Please have it confirmed by the administration.",
        "a_verifier": "Warning: some information comes from sources we have not yet been able to verify.",
        "responsable": "You remain responsible for the information you validate and submit: the competent administration and the official text prevail.",
        "clarifier": "Several procedures match your request. Which one applies to you?",
        "hors": "I could not find a procedure matching your request in my knowledge base. Could you specify the procedure or the administration concerned?",
        "proches": "I did not identify a specific procedure, but these texts may help:",
        "refus": "I cannot help bypass a procedure or falsify a document. I can, however, explain the official procedure.",
        "lacune": "I know this procedure, but I have no reliable open source to detail its steps. I prefer to tell you rather than invent a procedure.",
        "autorite": "Administration to contact",
        "orientation": "Unofficial practical guide, to be verified",
        "formulaire": "I can prepare the form for you to complete and check. Only you submit it on the official website.",
        "ecarte": "The text drafted by the model was rejected by the auditor; here are only the elements taken from the sources.",
    },
}

CHAMPS_FORMULAIRE = ["nom", "prenoms", "date_naissance", "lieu_naissance", "profession", "adresse"]
FORMULAIRES = {
    "cni": {"plateforme": "idcam.cm", "champs_supplementaires": ["numero_ancienne_cni", "centre_enrolement"]},
    "passeport": {"plateforme": "passcam.cm", "champs_supplementaires": ["numero_cni", "centre_enrolement"]},
}


def _nom(demarche: dict, langue: str) -> str:
    return demarche["nom_en"] if langue == "EN" else demarche["nom"]


def _libelle(cas: dict, langue: str) -> str:
    return cas["libelle_en"] if langue == "EN" else cas["libelle"]


def prefill_form(procedure_id: str, champs: Optional[dict] = None) -> Optional[dict]:
    """Prépare le formulaire de pré-enrôlement avec les seules valeurs fournies par le citoyen.

    Il n'existe pas d'API publique IDCAM ou PassCam : ce formulaire aide à préparer la
    saisie sur le site officiel, et rien n'est soumis.
    """
    modele = FORMULAIRES.get(procedure_id)
    if modele is None:
        return None
    champs = champs or {}
    noms = CHAMPS_FORMULAIRE + modele["champs_supplementaires"]
    return {
        "procedure_id": procedure_id,
        "plateforme": modele["plateforme"],
        "champs": [{"nom": n, "valeur": champs.get(n, "")} for n in noms],
        "soumis": False,
    }


def _llm_cloud_autorise() -> bool:
    return bool(os.getenv("GROQ_API_KEY")) and os.getenv("GOVIA_ALLOW_CLOUD_LLM", "0") == "1"


def appeler_llm(prompt: str) -> str:
    """Appelle le LLM local (Ollama), ou le cloud si c'est explicitement autorisé.

    Le cloud implique un transfert à l'étranger soumis à autorisation préalable (Loi
    n° 2024/017, art. 32) : il reste désactivé sauf GOVIA_ALLOW_CLOUD_LLM=1.
    """
    import requests

    delai = float(os.getenv("LLM_TIMEOUT", "180"))
    if _llm_cloud_autorise():
        reponse = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {os.environ['GROQ_API_KEY']}"},
            json={
                "model": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
            },
            timeout=delai,
        )
        reponse.raise_for_status()
        return reponse.json()["choices"][0]["message"]["content"]

    reponse = requests.post(
        os.getenv("LLM_URL", "http://ollama:11434/api/generate"),
        json={"model": os.getenv("LLM_MODEL", "mistral:7b"), "prompt": prompt, "stream": False},
        timeout=delai,
    )
    reponse.raise_for_status()
    return reponse.json()["response"]


def construire_prompt(question_masquee: str, demarche: dict, cas: Optional[dict], citations: List[dict], langue: str) -> str:
    contexte = "\n\n".join(f"[{c['article']} — {c['titre']}]\n{c['texte']}" for c in citations)
    langue_reponse = "anglais" if langue == "EN" else "français"
    precision = f"\nCas du citoyen : {cas['libelle']}" if cas else ""
    return f"""Tu es GOVIA, assistant pour les démarches administratives au Cameroun.
Démarche concernée : {demarche['nom']}{precision}
Question du citoyen : «{question_masquee}»

Sources autorisées :
{contexte}

Règles impératives :
1. Utilise uniquement les sources ci-dessus. N'ajoute aucune pièce, étape, administration ou condition absente des sources.
2. N'annonce aucun montant, délai ou numéro d'article absent des sources.
3. Cite la source de chaque exigence entre crochets, par exemple [Article 6].
4. Si une information manque, dis-le : ne la déduis pas.
5. Rappelle que le citoyen reste responsable des informations qu'il valide et soumet.
Les marqueurs comme [NOM] ou [DATE] remplacent des données masquées : ne cherche pas à les deviner.

Réponds en {langue_reponse}, de manière claire et concise."""


class AgentOrchestrateur:
    def __init__(
        self,
        use_llm: bool = True,
        catalogue: Optional[Catalogue] = None,
        analyse: Optional[AgentAnalyse] = None,
        recherche: Optional[AgentRecherche] = None,
        validation: Optional[AgentValidation] = None,
    ):
        self.use_llm = use_llm
        self.analyse = analyse or AgentAnalyse(catalogue)
        self.recherche = recherche or AgentRecherche()
        self.validation = validation or AgentValidation(base=self.recherche.kb.par_id)

    @property
    def catalogue(self) -> Catalogue:
        return self.analyse.catalogue

    # ---------------------------------------------------------------- Version B
    def respond(self, query: str, historique: Optional[List[str]] = None, langue: str = "FR", champs: Optional[dict] = None) -> dict:
        analyse = self.analyse.analyser(query, historique)
        if analyse.issue == "refus":
            return self._simple("refus", TEXTES[langue]["refus"], "detection_illicite")
        if analyse.issue == "clarification_demarche":
            return self._clarifier_demarches(analyse, langue)
        if analyse.issue == "hors_perimetre":
            return self._hors_perimetre(query, langue)
        if analyse.issue == "lacune":
            return self._lacune(analyse.demarche, langue)
        if analyse.issue == "clarification_cas":
            return self._clarifier_cas(analyse.demarche, langue)
        return self._repondre(query, analyse.demarche, analyse.cas, langue, champs)

    def _simple(self, type_reponse: str, texte: str, etape: str, **extra) -> dict:
        return {
            "type_reponse": type_reponse,
            "reponse": texte,
            "procedure_id": extra.pop("procedure_id", None),
            "procedure_identifiee": extra.pop("procedure_identifiee", None),
            "statut_demarche": extra.pop("statut_demarche", None),
            "cas": None,
            "options": extra.pop("options", []),
            "pieces_requises": [],
            "etapes": [],
            "citations": extra.pop("citations", []),
            "formulaire_prerempli": None,
            "mode_generation": "regles",
            "audit_log": [{"agent": extra.pop("agent", "analyse"), "etape": etape}],
            **extra,
        }

    def _clarifier_demarches(self, analyse: Analyse, langue: str) -> dict:
        options = [{"libelle": _nom(d, langue), "message": _nom(d, langue)} for d in analyse.candidats]
        return self._simple(
            "clarification", TEXTES[langue]["clarifier"], "clarification_demarche", options=options
        )

    def _clarifier_cas(self, demarche: dict, langue: str) -> dict:
        options = [{"libelle": _libelle(c, langue), "message": f"{_nom(demarche, langue)} : {_libelle(c, langue)}"} for c in demarche["cas"]]
        question = demarche.get("question_cas_en" if langue == "EN" else "question_cas") or TEXTES[langue]["clarifier"]
        return self._simple(
            "clarification", question, "clarification_cas",
            options=options,
            procedure_id=demarche["id"],
            procedure_identifiee=_nom(demarche, langue),
            statut_demarche=demarche["statut"],
        )

    def _hors_perimetre(self, query: str, langue: str) -> dict:
        passages = self.recherche.orienter(query)
        if not passages:
            return self._simple("hors_perimetre", TEXTES[langue]["hors"], "hors_perimetre")
        lignes = [TEXTES[langue]["proches"]] + [f"- {p['article']} — {p['titre']}" for p in passages]
        return self._simple("hors_perimetre", "\n".join(lignes), "orientation_rag", citations=passages, agent="recherche")

    def _lacune(self, demarche: dict, langue: str) -> dict:
        textes = TEXTES[langue]
        note = demarche["note_lacune_en"] if langue == "EN" else demarche["note_lacune"]
        lignes = [f"**{_nom(demarche, langue)}**", "", textes["lacune"], "", note, "", f"{textes['autorite']} : {demarche['autorite']}."]
        if demarche.get("orientation_url"):
            lignes.append(f"{textes['orientation']} : {demarche['orientation_url']}")
        return self._simple(
            "lacune", "\n".join(lignes), "lacune_documentee",
            procedure_id=demarche["id"],
            procedure_identifiee=_nom(demarche, langue),
            statut_demarche="lacune",
        )

    # --------------------------------------------------------------- Réponse sourcée
    def _composer(self, demarche: dict, cas: Optional[dict], elements: dict, langue: str, formulaire: bool) -> str:
        """Réponse composée uniquement d'extraits sourcés : pas de reformulation possible."""
        textes = TEXTES[langue]
        lignes = [f"**{textes['demarche']} : {_nom(demarche, langue)}**"]
        if cas:
            lignes.append(f"{textes['cas']} : {_libelle(cas, langue)}")
        if demarche["statut"] == "partiel":
            lignes += ["", textes["partiel"]]
        if any(c["statut_verification"] != "verifie" for c in elements["citations"]):
            lignes += ["", textes["a_verifier"]]

        if elements["etapes"]:
            lignes += ["", f"**{textes['etapes']} :**"] + [f"{i}. {e['texte']}" for i, e in enumerate(elements["etapes"], 1)]
        if elements["pieces"]:
            # Une même pièce peut servir à plusieurs étapes de la fiche : elle n'est listée qu'une fois.
            pieces = dict.fromkeys(p["texte"] for p in elements["pieces"])
            lignes += ["", f"**{textes['pieces']} :**"] + [f"- {p}" for p in pieces]
        if elements["couts"]:
            lignes += ["", f"**{textes['cout']} :**"] + [f"- {c}" for c in elements["couts"]]
        if elements["durees"]:
            lignes += ["", f"**{textes['duree']} :**"] + [f"- {d}" for d in elements["durees"]]
        if elements["extraits"]:
            lignes += ["", f"**{textes['extraits']} :**"] + [f"- {c['article']} : {c['texte']}" for c in elements["extraits"]]

        lignes += ["", f"**{textes['sources']} :**"]
        documents = {}
        for citation in elements["citations"]:
            documents.setdefault(citation["titre"], []).append(citation["article"])
        lignes += [f"- {titre} ({', '.join(dict.fromkeys(articles))})" for titre, articles in documents.items()]

        notes = list(dict.fromkeys(c["note"] for c in elements["citations"] if c.get("note")))
        if notes:
            lignes += [""] + notes
        if formulaire:
            lignes += ["", textes["formulaire"]]
        lignes += ["", textes["responsable"]]
        return "\n".join(lignes)

    def _repondre(self, query: str, demarche: dict, cas: Optional[dict], langue: str, champs: Optional[dict]) -> dict:
        elements = self.recherche.rassembler(query, demarche, cas)
        formulaire = prefill_form(demarche["id"], champs)
        secours = self._composer(demarche, cas, elements, langue, formulaire is not None)

        reponse, mode, journal = secours, "extraits_sources", []
        if self.use_llm:
            try:
                brouillon = appeler_llm(construire_prompt(masquer(query), demarche, cas, elements["citations"], langue))
            except Exception as erreur:  # service indisponible, délai dépassé, réponse invalide
                mode = "extraits_sources_llm_indisponible"
                journal.append({"agent": "orchestrateur", "etape": "llm_indisponible", "erreur": type(erreur).__name__})
            else:
                controle = self.validation.controler_brouillon(brouillon, demarche, elements["citations"])
                if controle.decision == "bloquer":
                    reponse = f"{TEXTES[langue]['ecarte']}\n\n{secours}"
                    mode = "extraits_sources_apres_rejet_llm"
                    journal.append({"agent": "validation", "etape": "rejet_llm", "motifs": controle.gaps})
                else:
                    reponse, mode = brouillon, "llm"
                    journal.append({"agent": "validation", "etape": "brouillon_accepte", "verdict": controle.verdict})

        return {
            "type_reponse": "reponse",
            "reponse": reponse,
            "procedure_id": demarche["id"],
            "procedure_identifiee": _nom(demarche, langue),
            "statut_demarche": demarche["statut"],
            "cas": cas["id"] if cas else None,
            "options": [],
            "pieces_requises": elements["pieces"],
            "etapes": elements["etapes"],
            "citations": elements["citations"],
            "formulaire_prerempli": formulaire,
            "mode_generation": mode,
            "audit_log": [
                {"agent": "analyse", "etape": "detection", "procedure_id": demarche["id"], "cas": cas["id"] if cas else None},
                {"agent": "recherche", "etape": "sources", "recherche": self.recherche.mode, "nb_citations": len(elements["citations"])},
                {"agent": "orchestrateur", "etape": "generation", "mode": mode},
                *journal,
            ],
        }

    # ---------------------------------------------------------------- Version A
    def respond_ungoverned(self, query: str, langue: str = "FR") -> dict:
        """Version A : LLM seul, sans base, sans masquage, sans contrôle bloquant.

        Elle sert uniquement à mesurer l'apport de la gouvernance. Si le cloud est
        configuré, elle reste indisponible : des données non masquées en sortiraient.
        """
        if _llm_cloud_autorise():
            raise RuntimeError("La version A n'est disponible qu'avec le LLM local.")
        consigne = "Réponds en anglais." if langue == "EN" else "Réponds en français."
        texte = appeler_llm(f"Tu aides les citoyens du Cameroun dans leurs démarches administratives. {consigne}\n\nQuestion : {query}")
        return {
            "type_reponse": "non_gouvernee",
            "reponse": texte,
            "procedure_id": None,
            "procedure_identifiee": None,
            "statut_demarche": None,
            "cas": None,
            "options": [],
            "pieces_requises": [],
            "etapes": [],
            "citations": [],
            "formulaire_prerempli": None,
            "mode_generation": "llm_sans_gouvernance",
            "audit_log": [{"agent": "orchestrateur", "etape": "generation", "mode": "llm_sans_gouvernance"}],
        }


# Nom historique, conservé pour main.py, les scripts et les tests.
AgentAssistant = AgentOrchestrateur
