import io
import json

import pytest
from fastapi.testclient import TestClient

import journal
import main


@pytest.fixture()
def client():
    return TestClient(main.app)


def _chat(client, texte, **options):
    corps = {"messages": [{"role": "user", "content": texte}], "consentement": True, **options}
    return client.post("/chat", json=corps)


def test_sante_signale_la_base(client):
    donnees = client.get("/").json()
    assert donnees["status"] == "ok" and donnees["base_de_connaissances"] > 200


def test_chat_exige_le_consentement(client):
    corps = {"messages": [{"role": "user", "content": "Je veux un passeport"}]}
    assert client.post("/chat", json=corps).status_code == 403


def test_upload_exige_le_consentement(client):
    fichier = {"file": ("a.png", io.BytesIO(b"x"), "image/png")}
    assert client.post("/upload", files=fichier).status_code == 403


def test_upload_refuse_un_format_non_image(client):
    fichier = {"file": ("a.txt", io.BytesIO(b"x"), "text/plain")}
    assert client.post("/upload", files=fichier, data={"consentement": "true"}).status_code == 415


def test_upload_refuse_un_fichier_trop_lourd(client, monkeypatch):
    monkeypatch.setattr(main, "TAILLE_MAX_UPLOAD", 4)
    fichier = {"file": ("a.png", io.BytesIO(b"123456"), "image/png")}
    assert client.post("/upload", files=fichier, data={"consentement": "true"}).status_code == 413


def test_upload_ne_renvoie_jamais_le_texte_brut(client, monkeypatch):
    monkeypatch.setattr(main, "extract_text", lambda contenu: "Nom : MBALLA\nTel: 699 12 34 56")
    fichier = {"file": ("a.png", io.BytesIO(b"x"), "image/png")}
    donnees = client.post("/upload", files=fichier, data={"consentement": "true", "procedure_id": "cni"}).json()
    assert "MBALLA" not in donnees["texte_masque"] and "699" not in donnees["texte_masque"]
    assert "texte_extrait" not in donnees
    assert donnees["formulaire"]["champs"][0] == {"nom": "nom", "valeur": "MBALLA"}
    assert donnees["formulaire"]["soumis"] is False


def test_chat_reponse_sourcee(client):
    donnees = _chat(client, "Je veux renouveler mon passeport").json()
    assert donnees["agent"]["procedure_id"] == "passeport"
    assert donnees["audit"]["decision"] != "bloquer"
    assert any(c["nom"] == "integrite" and c["resultat"] == "ok" for c in donnees["audit"]["controles"])


def test_chat_lacune_reconnue(client):
    donnees = _chat(client, "Comment obtenir un casier judiciaire ?").json()
    assert donnees["agent"]["type_reponse"] == "lacune"
    assert donnees["audit"]["gaps"]


def test_chat_utilise_l_historique(client):
    corps = {
        "consentement": True,
        "messages": [
            {"role": "user", "content": "Je veux une CNI"},
            {"role": "assistant", "content": "De quel cas s'agit-il ?"},
            {"role": "user", "content": "Perte, vol ou détérioration"},
        ],
    }
    donnees = client.post("/chat", json=corps).json()
    assert donnees["agent"]["cas"] == "perte"


def test_le_dernier_message_doit_venir_du_citoyen(client):
    corps = {"consentement": True, "messages": [{"role": "assistant", "content": "Bonjour"}]}
    assert client.post("/chat", json=corps).status_code == 422


def test_version_a_desactivee_par_defaut(client):
    assert _chat(client, "Je veux un passeport", version="A").status_code == 403


def test_version_a_observee_par_l_auditeur_sans_blocage(client, monkeypatch):
    monkeypatch.setenv("GOVIA_ALLOW_VERSION_A", "1")
    monkeypatch.setattr("agent.appeler_llm", lambda prompt: "Le passeport coûte 500 000 FCFA.")
    donnees = _chat(client, "Je veux un passeport", version="A").json()
    assert "500 000" in donnees["agent"]["reponse"]
    assert donnees["audit"]["verdict"] == "non_conforme"


def test_journal_sans_donnee_personnelle(client):
    journal.CHEMIN.unlink(missing_ok=True)
    _chat(client, "Je m'appelle Jean Mballa, je veux un passeport")
    entree = json.loads(journal.CHEMIN.read_text(encoding="utf-8").splitlines()[-1])
    assert entree["procedure_id"] == "passeport" and entree["citations"]
    assert "Mballa" not in json.dumps(entree)


def test_notice_de_consentement_bilingue(client):
    assert "consentement" in client.get("/consentement").json()["titre"]
    assert "consent" in client.get("/consentement?langue=EN").json()["titre"]


def test_catalogue_expose_les_lacunes(client):
    statuts = {d["statut"] for d in client.get("/kb/catalogue").json()}
    assert statuts == {"couvert", "partiel", "lacune"}


def test_recherche_bornee(client):
    assert client.get("/kb/search", params={"q": "passeport", "n": 1000}).status_code == 422
    assert client.get("/kb/search", params={"q": "passeport validité"}).json()["results"]
