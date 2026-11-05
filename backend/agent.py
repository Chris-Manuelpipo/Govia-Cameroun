"""GOVIA-Assistant : guide le citoyen dans ses démarches à partir de sources vérifiées.

Déroulé de la version gouvernée (B) :
1. refuser une demande illicite ;
2. identifier la démarche et le cas, ou demander une précision au lieu de deviner ;
3. signaler une lacune quand aucune source ouverte n'existe, sans inventer ;
4. rassembler pièces, étapes et citations depuis le catalogue et le RAG ;
5. rédiger avec le LLM local sur la seule base de ces sources, données masquées ;
6. faire contrôler le texte par l'auditeur ; un texte rejeté est remplacé par une
   réponse composée uniquement des extraits sourcés.

La version A (sans gouvernance) interroge le LLM seul, pour la comparaison du rapport.
L'agent ne soumet jamais rien à la place du citoyen.
"""
from __future__ import annotations

import os
from typing import List, Optional

from auditor import audit
from catalogue import Catalogue, Detection
from privacy import masquer
from rag import citation_de, kb

MAX_CITATIONS_RAG = 3

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


class AgentAssistant:
    def __init__(self, use_llm: bool = True, catalogue: Optional[Catalogue] = None):
        self.use_llm = use_llm
        self.catalogue = catalogue or Catalogue()

    # ---------------------------------------------------------------- Version B
    def respond(self, query: str, historique: Optional[List[str]] = None, langue: str = "FR", champs: Optional[dict] = None) -> dict:
        historique = historique or []
        detection = self.catalogue.detecter(query, historique)
        if detection.illicite:
            return self._simple("refus", TEXTES[langue]["refus"], "detection_illicite")
        if detection.demarche is None:
            if detection.ambigu:
                return self._clarifier_demarches(detection, langue)
            return self._hors_perimetre(query, langue)

        demarche = detection.demarche
        if demarche["statut"] == "lacune":
            return self._lacune(demarche, langue)

        cas = self.catalogue.detecter_cas(demarche, self._textes_du_cas(query, historique, demarche))
        if demarche.get("cas_mode") == "choix" and cas is None:
            return self._clarifier_cas(demarche, langue)
        return self._repondre(query, demarche, cas, langue, champs)

    def _textes_du_cas(self, query: str, historique: List[str], demarche: dict) -> List[str]:
        """Messages où chercher le cas : le message courant, puis le précédent s'il s'y rapporte.

        Remonter plus loin ferait resservir un cas périmé, et un message sur une autre démarche
        (« j'ai perdu mon passeport ») ne dit rien du cas de celle-ci.
        """
        textes = [query]
        if historique:
            citees = self.catalogue.demarches_citees(historique[-1])
            if not citees or demarche in citees:
                textes.append(historique[-1])
        return textes

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
            "audit_log": [{"etape": etape}],
            **extra,
        }

    def _clarifier_demarches(self, detection: Detection, langue: str) -> dict:
        options = [{"libelle": _nom(d, langue), "message": _nom(d, langue)} for d in detection.candidats]
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
        passages = kb.retrieve(query, n_k=3)
        if not passages:
            return self._simple("hors_perimetre", TEXTES[langue]["hors"], "hors_perimetre")
        lignes = [TEXTES[langue]["proches"]] + [f"- {p['article']} — {p['titre']}" for p in passages]
        return self._simple("hors_perimetre", "\n".join(lignes), "orientation_rag", citations=passages)

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
    def _fiches_retenues(self, demarche: dict, cas: Optional[dict]) -> List[dict]:
        if cas and cas.get("fiche"):
            return [f for f in demarche["fiches"] if f["fiche"] == cas["fiche"]]
        return demarche["fiches"]

    def _rassembler(self, query: str, demarche: dict, cas: Optional[dict]) -> dict:
        """Réunit pièces, étapes, coûts et citations d'après le catalogue, puis le RAG."""
        fiches = self._fiches_retenues(demarche, cas)
        pieces: List[dict] = list(demarche.get("pieces", []))
        etapes: List[dict] = list(demarche.get("etapes", []))
        identifiants: List[str] = []
        if cas:
            pieces = list(cas.get("pieces", [])) + pieces
            if cas.get("chunk"):
                identifiants.append(cas["chunk"])

        couts, durees = [], []
        for fiche in fiches:
            prefixe = f"{fiche['libelle']} : " if len(fiches) > 1 else ""
            source = {c.rsplit("::", 1)[1]: c for c in fiche["chunks"]}
            etapes += [{"texte": prefixe + e, "chunk": source["etapes"]} for e in fiche["etapes"]]
            if "documents" in source:
                pieces += [{"texte": prefixe + p, "chunk": source["documents"]} for p in fiche["pieces"]]
            if fiche["cout"]:
                couts.append(prefixe + " ; ".join(fiche["cout"]))
            if fiche["duree_totale"]:
                durees.append(prefixe + fiche["duree_totale"])
            identifiants += fiche["chunks"]

        identifiants += [x["chunk"] for x in pieces + etapes]
        identifiants += demarche.get("chunks_complementaires", [])
        vus = list(dict.fromkeys(identifiants))
        citations = [citation_de(kb.par_id[i], 1.0) for i in vus if i in kb.par_id]

        # Le RAG complète par des passages de la même démarche, jamais d'une autre.
        admis = set(vus)
        fiches_ecartees = {
            i for f in demarche["fiches"] if f not in fiches for i in f["chunks"]
        }
        supplements = [
            c for c in kb.retrieve(query, n_k=MAX_CITATIONS_RAG + len(vus) + 1, procedure_ids=[demarche["id"]])
            if c["id"] not in admis and c["id"] not in fiches_ecartees
        ]
        supplements = supplements[:MAX_CITATIONS_RAG]
        citations += supplements

        # Une démarche sans pièces ni étapes (protection des données, signature...) reste
        # fondée sur ses textes : à défaut de passage proche, on cite ses premiers articles.
        if not citations:
            supplements = [citation_de(kb.par_id[i], 0.0) for i in demarche["chunks"][:MAX_CITATIONS_RAG]]
            citations = list(supplements)

        complements = [i for i in demarche.get("chunks_complementaires", []) if i in kb.par_id]
        extraits = [c for c in citations if c["id"] in complements or c in supplements]
        return {
            "pieces": pieces, "etapes": etapes, "couts": couts, "durees": durees,
            "citations": citations, "extraits": extraits,
        }

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
            lignes += ["", f"**{textes['pieces']} :**"] + [f"- {p['texte']}" for p in elements["pieces"]]
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
        elements = self._rassembler(query, demarche, cas)
        formulaire = prefill_form(demarche["id"], champs)
        secours = self._composer(demarche, cas, elements, langue, formulaire is not None)

        reponse, mode, journal = secours, "extraits_sources", []
        if self.use_llm:
            try:
                brouillon = appeler_llm(construire_prompt(masquer(query), demarche, cas, elements["citations"], langue))
                controle = audit(
                    brouillon, elements["citations"], base=kb.par_id, procedure_id=demarche["id"],
                    procedures_admises=[demarche["id"], *demarche.get("procedures_liees", [])],
                    type_reponse="reponse", statut_demarche=demarche["statut"],
                )
                if controle.decision == "bloquer":
                    reponse = f"{TEXTES[langue]['ecarte']}\n\n{secours}"
                    mode = "extraits_sources_apres_rejet_llm"
                    journal.append({"etape": "rejet_llm", "motifs": controle.gaps})
                else:
                    reponse, mode = brouillon, "llm"
            except Exception as erreur:  # service indisponible, délai dépassé, réponse invalide
                mode = "extraits_sources_llm_indisponible"
                journal.append({"etape": "llm_indisponible", "erreur": type(erreur).__name__})

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
                {"etape": "detection", "procedure_id": demarche["id"], "cas": cas["id"] if cas else None},
                {"etape": "sources", "recherche": kb.mode, "nb_citations": len(elements["citations"])},
                {"etape": "generation", "mode": mode},
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
            "audit_log": [{"etape": "generation", "mode": "llm_sans_gouvernance"}],
        }
