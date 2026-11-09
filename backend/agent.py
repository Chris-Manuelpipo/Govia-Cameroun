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
from auditor import AgentValidation, audit
from conversation import Sujet, contient_salutation
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

# Exemples proposés en boutons quand l'agent n'a pas de démarche à détailler : ils aboutissent tous.
EXEMPLES = {
    "FR": [
        ("Renouveler ma CNI", "Ma CNI est périmée, je veux la renouveler"),
        ("Créer une société", "Je veux créer une société"),
        ("Permis de construire", "Je veux un permis de construire"),
        ("Déclarer mes salariés à la CNPS", "Comment déclarer mes salariés à la CNPS ?"),
    ],
    "EN": [
        ("Renew my identity card", "My national identity card has expired, I want to renew it"),
        ("Create a company", "I want to create a company"),
        ("Building permit", "I need a building permit"),
        ("Register employees with CNPS", "How do I register my employees with CNPS?"),
    ],
}
AIDE_BOUTON = {"FR": ("Que savez-vous faire ?", "Que peux-tu faire ?"), "EN": ("What can you do?", "What can you do?")}
DOMAINES_EN = {
    "Identité et état civil": "identity and civil status", "Protection sociale": "social security", "Impôts et taxes": "taxes",
    "Création d'entreprise": "company creation", "Urbanisme et foncier": "building and land", "Véhicules": "vehicles",
    "Commerce extérieur": "foreign trade", "Numérique et données": "digital and data", "Justice": "justice",
    "Travail": "employment", "Vie associative": "associations", "Étrangers": "foreign nationals", "Éducation": "education",
    "Vie locale": "local life", "Vie citoyenne": "civic life", "Emploi public": "public employment",
}
CONVERSATION = {
    "FR": {
        "salut": "Bonjour",
        "salutation_repetee": "Oui, je vous écoute. Quelle démarche vous intéresse ?",
        "etat": "Je vais bien, merci de demander. Quelle démarche puis-je vous aider à préparer ?",
        "createur": "J'ai été conçu par l'équipe GOVIA Cameroun pour le hackathon ITU AI for Good Lab. Je prépare vos démarches en citant les textes, mais je ne remplace ni les textes officiels ni l'administration. Quelle démarche vous intéresse ?",
        "salutation": "Bonjour, je suis GOVIA. Je vous aide à préparer vos démarches administratives au Cameroun : je vous indique les pièces à fournir et les étapes, avec les textes qui les fondent, et je vous dis clairement quand je n'ai pas de texte ouvert. Quelle démarche vous intéresse ?",
        "remerciement": "Avec plaisir. Si une autre démarche vous préoccupe, dites-moi laquelle.",
        "accord": "D'accord. Dites-moi quelle démarche vous intéresse, ou choisissez un exemple :",
        "identite": "Je suis GOVIA, un assistant automatique : je ne suis pas une personne. Je comprends le français et l'anglais, et je réponds dans la langue de votre message. Dites-moi la démarche qui vous intéresse :",
        "au_revoir": "Au revoir. Avant de vous déplacer, vérifiez toujours auprès de l'administration compétente.",
        "aide": "Je repère votre démarche à partir de votre situation, je liste les pièces à fournir et les étapes avec le texte qui les fonde, je vous demande une précision quand plusieurs cas existent, et je vous dis quand aucun texte ouvert n'existe. Je ne soumets rien à votre place et je ne conserve aucune pièce d'identité. Par exemple :",
        "apercu": "Je vous aide à préparer vos démarches administratives au Cameroun. J'en connais {total}, dont {couvertes} s'appuient sur un texte ouvert : {domaines}. Pour {lacunes} autres, je n'ai aucun texte ouvert, et je vous le dirai plutôt que d'inventer. Dites-moi ce que vous voulez faire, par exemple :",
        "hors": "Je ne suis pas sûr d'avoir compris. Je vous aide pour les démarches administratives au Cameroun : pouvez-vous nommer la démarche ou l'administration concernée ? Par exemple :",
        "et_autres": "et d'autres",
    },
    "EN": {
        "salut": "Hello",
        "salutation_repetee": "Yes, I'm listening. Which procedure interests you?",
        "etat": "I'm fine, thank you for asking. Which procedure can I help you prepare?",
        "createur": "I was designed by the GOVIA Cameroon team for the ITU AI for Good Lab hackathon. I prepare your procedures by citing the texts, but I replace neither the official texts nor the administration. Which procedure interests you?",
        "salutation": "Hello, I'm GOVIA. I help you prepare administrative procedures in Cameroon: I list the documents and the steps, with the texts they rest on, and I tell you clearly when I have no open text. Which procedure are you interested in?",
        "remerciement": "You're welcome. If another procedure is on your mind, tell me which one.",
        "accord": "All right. Tell me which procedure interests you, or pick an example:",
        "identite": "I'm GOVIA, an automated assistant: I'm not a person. I understand French and English, and I reply in the language of your message. Tell me which procedure interests you:",
        "au_revoir": "Goodbye. Before you go anywhere, always check with the competent administration.",
        "aide": "I identify your procedure from your situation, list the documents and the steps with the text they rest on, ask you to clarify when several cases exist, and tell you when no open text exists. I submit nothing on your behalf and I keep no identity document. For example:",
        "apercu": "I help you prepare administrative procedures in Cameroon. I know {total}, of which {couvertes} rest on an open text: {domaines}. For {lacunes} others I have no open text, and I will say so rather than invent anything. Tell me what you want to do, for example:",
        "hors": "I'm not sure I understood. I help with administrative procedures in Cameroon: could you name the procedure or the administration concerned? For example:",
        "et_autres": "and more",
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
                "model": os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
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


# Sujets de conversation confiés au modèle quand il est actif : le ton y gagne. L'aide, l'aperçu des démarches et
# les questions sur GOVIA restent des textes fixes (chiffres du catalogue, faits sur le projet) qu'un modèle pourrait déformer.
SUJETS_LLM = {"salutation", "etat", "remerciement", "au_revoir", "accord"}


def construire_prompt_conversation(message_masque: str, precedents: List[str], demarches: str) -> str:
    echanges = "\n".join(f"- {m}" for m in precedents) or "(aucun)"
    return f"""Tu es GOVIA, assistant d'orientation pour les démarches administratives au Cameroun. Tu converses poliment et brièvement (deux à quatre phrases) dans la langue du message de l'utilisateur (français ou anglais).
Règles impératives :
1. Tu réponds chaleureusement et en une phrase aux politesses (salutation, « comment vas-tu », remerciement), puis tu reviens aux démarches. Pour le reste, tu ne parles que des démarches administratives camerounaises et de GOVIA. Pour tout autre sujet, dis poliment que tu ne peux pas aider là-dessus et propose de parler d'une démarche.
2. Tu ne donnes AUCUN montant, délai, pièce à fournir, étape, article de loi, administration ou lien : ces informations viennent des textes sources, que tu n'as pas ici. Si l'utilisateur veut un détail, invite-le à nommer la démarche.
3. Tu ne prétends pas soumettre, payer ou conserver quoi que ce soit : le citoyen soumet lui-même.
4. Tu es un assistant automatique, pas une personne. Tu n'inventes rien sur toi : tu as été conçu par l'équipe GOVIA Cameroun pour le hackathon ITU AI for Good Lab.
5. Pas d'émoji, pas de liste, pas de gras. Les marqueurs comme [NOM] remplacent des données masquées.
Démarches connues (noms seulement) : {demarches}
Messages précédents de l'utilisateur :
{echanges}
Message de l'utilisateur : «{message_masque}»
Réponds uniquement par ta réponse."""


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
        analyse = self.analyse.analyser(query, historique, langue)
        if analyse.issue == "refus":
            return self._simple("refus", TEXTES[langue]["refus"], "detection_illicite")
        if analyse.issue == "clarification_demarche":
            return self._clarifier_demarches(analyse, langue)
        if analyse.issue == "conversation":
            return self._conversation(analyse.sujet, query, historique)
        if analyse.issue == "hors_perimetre":
            return self._hors_perimetre(query, langue, historique)
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

    @staticmethod
    def _exemples(langue: str, avec_aide: bool = False) -> List[dict]:
        options = [{"libelle": libelle, "message": message} for libelle, message in EXEMPLES[langue]]
        if avec_aide:
            options.append({"libelle": AIDE_BOUTON[langue][0], "message": AIDE_BOUTON[langue][1]})
        return options

    def _apercu(self, langue: str) -> str:
        """Ce que GOVIA sait faire, chiffré d'après le catalogue : rien d'écrit en dur qui puisse devenir faux."""
        demarches = self.catalogue.demarches
        sourcees = [d for d in demarches if d["statut"] != "lacune"]
        effectifs: dict = {}
        for d in sourcees:
            effectifs[d["domaine"]] = effectifs.get(d["domaine"], 0) + 1
        domaines = [dom for dom, _ in sorted(effectifs.items(), key=lambda x: (-x[1], x[0]))]
        retenus = [DOMAINES_EN.get(dom, dom) if langue == "EN" else dom[0].lower() + dom[1:] for dom in domaines[:6]]
        liste = ", ".join(retenus) + (f" {CONVERSATION[langue]['et_autres']}" if len(domaines) > 6 else "")
        return CONVERSATION[langue]["apercu"].format(
            total=len(demarches), couvertes=len(sourcees), domaines=liste, lacunes=len(demarches) - len(sourcees)
        )

    def _converser_llm(self, query: str, historique: Optional[List[str]]) -> Optional[str]:
        """Réponse de conversation rédigée par le modèle, ou None : l'agent retombe alors sur ses textes fixes.

        Le message est masqué avant l'envoi, et la réponse passe par l'auditeur : un montant, un délai ou un article
        inventé la fait écarter, comme pour une réponse sur une démarche.
        """
        if not self.use_llm:
            return None
        noms = ", ".join(d["nom"] for d in self.catalogue.demarches if d["statut"] != "lacune")
        precedents = [masquer(m)[:300] for m in (historique or [])[-3:]]
        try:
            texte = appeler_llm(construire_prompt_conversation(masquer(query), precedents, noms)).strip()
        except Exception:  # service indisponible, clé absente, délai dépassé
            return None
        if not texte or len(texte) > 800 or "http" in texte.lower():
            return None
        if audit(texte, [], base=self.recherche.kb.par_id, type_reponse="conversation").decision == "bloquer":
            return None
        return texte

    def _conversation(self, sujet: Sujet, query: str = "", historique: Optional[List[str]] = None) -> dict:
        """Salutation, remerciement, adieu, aide ou question générale : une réponse directe, sans recherche de texte."""
        langue = sujet.langue
        if sujet.nom in SUJETS_LLM:
            redige = self._converser_llm(query, historique)
            if redige:
                return self._simple(
                    "conversation", redige, "conversation_llm", options=self._exemples(langue) if sujet.nom != "au_revoir" else [],
                    agent="orchestrateur", mode_generation="llm",
                )
        cle = "salutation_repetee" if sujet.nom == "salutation" and sujet.repete else sujet.nom
        texte = self._apercu(langue) if sujet.nom == "apercu" else CONVERSATION[langue][cle]
        if sujet.salutation and sujet.nom in ("aide", "apercu", "etat"):
            texte = f"{CONVERSATION[langue]['salut']}. {texte}"
        avec_exemples = sujet.nom in ("salutation", "etat", "aide", "apercu", "accord", "identite", "createur")
        return self._simple(
            "conversation", texte, "conversation", options=self._exemples(langue) if avec_exemples else []
        )

    def _hors_perimetre(self, query: str, langue: str, historique: Optional[List[str]] = None) -> dict:
        passages = self.recherche.orienter(query)
        if not passages:
            redige = self._converser_llm(query, historique)
            if redige:
                return self._simple(
                    "hors_perimetre", redige, "hors_perimetre_llm", options=self._exemples(langue, avec_aide=True),
                    agent="orchestrateur", mode_generation="llm",
                )
            texte = CONVERSATION[langue]["hors"]
            if contient_salutation(query):
                texte = f"{CONVERSATION[langue]['salut']}. {texte}"
            return self._simple("hors_perimetre", texte, "hors_perimetre", options=self._exemples(langue, avec_aide=True))
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
