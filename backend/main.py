"""API FastAPI de GOVIA Cameroun.

Endpoints :
- GET  /               état du service
- GET  /consentement   notice d'information (Loi n° 2024/017, art. 21)
- GET  /kb/stats       statistiques de la base
- GET  /kb/documents   documents et statut de vérification
- GET  /kb/catalogue   démarches couvertes, partielles et lacunes
- GET  /kb/search      recherche dans la base
- POST /chat           agent et auditeur
- POST /upload         lecture d'une pièce, données masquées, rien n'est conservé

L'agent ne soumet jamais rien à la place du citoyen.
"""
from __future__ import annotations

import chargement_env  # noqa: F401  (lit .env avant les modules qui lisent l'environnement)
import json
import os
from collections import Counter

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from agent import AgentAssistant, _llm_cloud_autorise, prefill_form
from catalogue import KB_DIR
from journal import consigner
from ocr import extract_text
from privacy import extraire_champs, masquer
from rag import kb
from schemas import AgentResponse, AuditResult, ChatRequest, ChatResponse

TAILLE_MAX_UPLOAD = int(os.getenv("GOVIA_MAX_UPLOAD_MB", "5")) * 1024 * 1024
TYPES_IMAGE = {"image/png", "image/jpeg"}
MESSAGE_CONSENTEMENT = (
    "Consentement préalable requis (Loi n° 2024/017, article 9). "
    "Veuillez lire la notice et donner votre accord pour utiliser ce service."
)

NOTICE = {
    "FR": {
        "titre": "Vos données et votre consentement",
        "responsable": "Équipe GOVIA Cameroun, prototype de démonstration pour le hackathon ITU AI for Good Lab.",
        "finalite": "Vous orienter dans vos démarches administratives en citant les textes applicables.",
        "donnees": "Le texte de vos questions et, si vous en envoyez une, le texte lu sur une pièce.",
        "destinataires": "Aucun. Avec le modèle local, rien n'est transmis à l'extérieur du serveur.",
        "conservation": "Vos questions et vos pièces ne sont pas conservées. Le journal d'audit ne garde que la démarche, les sources citées et le verdict.",
        "transfert": "Aucun transfert à l'étranger avec le modèle local. Le modèle cloud reste désactivé par défaut.",
        "droits": "Vous pouvez refuser, retirer votre accord à tout moment, contester une réponse et demander une intervention humaine. L'agent oriente : il ne prend aucune décision administrative.",
        "limites": "Prototype : n'envoyez pas de vraies pièces, ni photo d'identité, ni empreinte. Le masquage automatique des données peut être incomplet. Aucune autorisation de l'Autorité de protection des données n'a été délivrée à ce prototype.",
        "action": "J'ai lu ces informations et j'accepte",
    },
    "EN": {
        "titre": "Your data and your consent",
        "responsable": "GOVIA Cameroon team, demonstration prototype for the ITU AI for Good Lab hackathon.",
        "finalite": "Guiding you through administrative procedures by citing the applicable texts.",
        "donnees": "The text of your questions and, if you send one, the text read from a document.",
        "destinataires": "None. With the local model, nothing is sent outside the server.",
        "conservation": "Your questions and documents are not stored. The audit log only keeps the procedure, the sources cited and the verdict.",
        "transfert": "No transfer abroad with the local model. The cloud model is disabled by default.",
        "droits": "You may refuse, withdraw your consent at any time, challenge an answer and request human intervention. The agent guides you: it takes no administrative decision.",
        "limites": "Prototype: do not send real documents, identity photos or fingerprints. Automatic data masking may be incomplete. No authorisation from the Data Protection Authority has been issued to this prototype.",
        "action": "I have read this information and I agree",
    },
}

app = FastAPI(
    title="GOVIA Cameroun",
    version="0.2.0",
    description="Agent d'assistance administrative et de conformité",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in os.getenv("GOVIA_CORS_ORIGINS", "http://localhost:3000").split(",") if o.strip()],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

agent = AgentAssistant(use_llm=os.getenv("GOVIA_USE_LLM", "1") == "1")


@app.get("/")
def health():
    return {
        "status": "ok" if kb.chunks else "base_vide",
        "service": "GOVIA Cameroun",
        "version": app.version,
        "base_de_connaissances": len(kb.chunks),
        "recherche": kb.mode,
        "llm_active": agent.use_llm,
        "llm_cloud": cloud_actif(),
    }


# Quand le modèle cloud est actif, la notice ne peut plus dire que rien ne quitte le serveur.
NOTICE_CLOUD = {
    "FR": {
        "destinataires": "Groq, fournisseur du modèle de langage, reçoit le texte de vos questions après masquage des données personnelles.",
        "transfert": "Oui : le texte masqué de vos questions est transmis à un service situé à l'étranger. Aucune autorisation de l'Autorité de protection des données n'a été délivrée : n'envoyez que des questions fictives.",
    },
    "EN": {
        "destinataires": "Groq, the language model provider, receives the text of your questions after personal data has been masked.",
        "transfert": "Yes: the masked text of your questions is sent to a service located abroad. No authorisation from the Data Protection Authority has been issued: send fictitious questions only.",
    },
}


def cloud_actif() -> bool:
    return agent.use_llm and _llm_cloud_autorise()


@app.get("/consentement")
def consentement(langue: str = Query("FR", pattern="^(FR|EN)$")):
    return {**NOTICE[langue], **(NOTICE_CLOUD[langue] if cloud_actif() else {})}


@app.get("/kb/stats")
def kb_stats():
    return {
        "total_chunks": len(kb.chunks),
        "total_documents": len({c["doc"] for c in kb.chunks}),
        "par_statut_verification": dict(Counter(c["statut_verification"] for c in kb.chunks)),
        "par_type_source": dict(Counter(c["type_source"] for c in kb.chunks)),
        "par_demarche": dict(Counter(c["procedure_id"] for c in kb.chunks)),
        "demarches": dict(Counter(d["statut"] for d in agent.catalogue.demarches)),
    }


@app.get("/kb/documents")
def kb_documents():
    return json.loads((KB_DIR / "index.json").read_text(encoding="utf-8"))


@app.get("/kb/catalogue")
def kb_catalogue():
    return [
        {
            "id": d["id"],
            "nom": d["nom"],
            "nom_en": d["nom_en"],
            "domaine": d["domaine"],
            "statut": d["statut"],
            "autorite": d["autorite"],
            "note_lacune": d.get("note_lacune"),
        }
        for d in agent.catalogue.demarches
    ]


@app.get("/kb/search")
def kb_search(q: str = Query(min_length=2, max_length=500), n: int = Query(5, ge=1, le=50)):
    return {"query": q, "results": kb.retrieve(q, n_k=n)}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    if not req.consentement:
        raise HTTPException(status_code=403, detail=MESSAGE_CONSENTEMENT)
    utilisateurs = [m.content for m in req.messages if m.role == "user"]
    if not utilisateurs or req.messages[-1].role != "user":
        raise HTTPException(status_code=422, detail="Le dernier message doit venir du citoyen.")
    question, historique = utilisateurs[-1], utilisateurs[:-1][-3:]

    if req.version == "A":
        if os.getenv("GOVIA_ALLOW_VERSION_A", "0") != "1":
            raise HTTPException(status_code=403, detail="La version A sert uniquement à la comparaison et reste désactivée.")
        try:
            reponse_agent = agent.respond_ungoverned(question, req.language)
        except Exception as erreur:
            raise HTTPException(status_code=503, detail=f"LLM indisponible pour la version A ({type(erreur).__name__}).")
        # L'auditeur observe sans bloquer : on mesure ce que la gouvernance aurait intercepté.
        resultat = agent.validation.observer(reponse_agent["reponse"])
    else:
        reponse_agent = agent.respond(question, historique, req.language)
        demarche = agent.catalogue.par_id.get(reponse_agent["procedure_id"] or "")
        # Second passage de l'agent de validation, sur la réponse finale.
        resultat = agent.validation.controler_reponse(reponse_agent, demarche)
        if resultat.decision == "bloquer":
            # Filet de sécurité : la réponse composée d'extraits ne devrait jamais en arriver là.
            reponse_agent["reponse"] = (
                "Cette réponse a été retenue par l'auditeur de conformité."
                if req.language == "FR"
                else "This answer was withheld by the compliance auditor."
            )
            reponse_agent["pieces_requises"], reponse_agent["etapes"] = [], []
            reponse_agent["formulaire_prerempli"] = None

    reponse = ChatResponse(version=req.version, agent=AgentResponse(**reponse_agent), audit=resultat)
    consigner(version=req.version, langue=req.language, agent=reponse.agent.model_dump(), audit=resultat.model_dump())
    return reponse


@app.post("/upload")
async def upload(
    file: UploadFile = File(...),
    consentement: bool = Form(False),
    procedure_id: str = Form(""),
):
    """Lit une pièce pour préparer le formulaire. L'image n'est jamais conservée."""
    if not consentement:
        raise HTTPException(status_code=403, detail=MESSAGE_CONSENTEMENT)
    if file.content_type not in TYPES_IMAGE:
        raise HTTPException(status_code=415, detail="Formats acceptés : PNG et JPEG.")
    contenu = await file.read(TAILLE_MAX_UPLOAD + 1)
    if len(contenu) > TAILLE_MAX_UPLOAD:
        raise HTTPException(status_code=413, detail="Fichier trop volumineux.")
    texte = extract_text(contenu)
    if texte is None:
        raise HTTPException(status_code=422, detail="Lecture impossible : OCR indisponible ou image illisible.")
    champs = extraire_champs(texte)
    return {
        "texte_masque": masquer(texte),
        "champs_detectes": champs,
        "formulaire": prefill_form(procedure_id, champs) if procedure_id else None,
        "avertissement": "Vérifiez chaque champ : la lecture automatique peut se tromper. Rien n'a été conservé ni soumis.",
    }
