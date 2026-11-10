import pytest

from agent import AgentAssistant
from auditor import audit
from rag import kb


@pytest.fixture(scope="module")
def agent():
    return AgentAssistant(use_llm=False)


def test_une_piece_n_est_listee_qu_une_fois(agent):
    reponse = agent.respond("Comment payer la patente ?")["reponse"]
    pieces = reponse.split("**Pièces à fournir :**")[1].split("\n\n")[0].strip().splitlines()
    assert pieces and len(pieces) == len(set(pieces))


@pytest.mark.parametrize(
    "question, attendu",
    [
        ("Je veux renouveler mon passeport", "passeport"),
        ("J'ai perdu mon passeport", "passeport"),
        ("I want to renew my passport", "passeport"),
        ("How do I get a birth certificate?", "acte_naissance"),
        ("Je veux un acte de mariage", "acte_mariage"),
        ("Je veux déclarer un décès", "acte_deces"),
        ("Je veux un permis de construire", "permis_construire"),
        ("Comment créer une association ?", "association"),
        ("Comment payer la patente ?", "patente"),
        ("Je veux immatriculer ma voiture", "carte_grise"),
        ("Comment déclarer mes salariés à la CNPS ?", "cnps_immatriculation"),
        ("Quelle est la procédure pour un titre foncier par mutation ?", "titre_foncier"),
        ("Je veux m'inscrire au fichier des importateurs", "fichier_importateurs"),
    ],
)
def test_detection_de_la_demarche(agent, question, attendu):
    assert agent.catalogue.detecter(question).demarche["id"] == attendu


@pytest.mark.parametrize(
    "question",
    ["Mon ingénieur demande une facture", "Je fais une technique passive", "Quel est le prix du pain ?"],
)
def test_pas_de_faux_positif(agent, question):
    assert agent.respond(question)["type_reponse"] == "hors_perimetre"


def test_scenario_de_l_etude_renouveler_ma_carte_demande_une_precision(agent):
    reponse = agent.respond("Je veux renouveler ma carte")
    assert reponse["type_reponse"] == "clarification"
    assert {"Carte nationale d'identité (CNI)", "Carte grise (immatriculation d'un véhicule)", "Carte de séjour"} <= {o["libelle"] for o in reponse["options"]}


def test_precision_apres_clarification_retrouve_la_demarche_et_le_cas(agent):
    reponse = agent.respond("je l'ai perdue", ["Je veux une CNI"])
    assert reponse["procedure_id"] == "cni" and reponse["cas"] == "perte"


def test_cni_perdue_exige_l_attestation_et_non_la_liste_generique(agent):
    reponse = agent.respond("Je veux renouveler ma CNI, je l'ai perdue")
    assert reponse["cas"] == "perte"
    pieces = " ".join(p["texte"] for p in reponse["pieces_requises"])
    assert "attestation de déclaration de perte" in pieces
    assert "certificat de nationalité" not in pieces


def test_cni_perimee_n_exige_pas_le_certificat_de_nationalite(agent):
    reponse = agent.respond("Ma CNI est périmée, je veux la renouveler")
    assert reponse["cas"] == "peremption"
    pieces = " ".join(p["texte"] for p in reponse["pieces_requises"]).lower()
    assert "carte nationale d'identité périmée" in pieces
    assert "certificat de nationalité" not in pieces


def test_citations_toutes_sur_la_demarche(agent):
    reponse = agent.respond("Je veux un permis de construire")
    assert reponse["citations"]
    assert {c["procedure_id"] for c in reponse["citations"]} == {"permis_construire"}


def test_cas_de_titre_foncier_limite_a_la_bonne_fiche(agent):
    reponse = agent.respond("Titre foncier suite à un morcellement")
    assert reponse["cas"] == "morcellement"
    assert {c["doc"] for c in reponse["citations"]} == {"eregulations_47_25"}


def test_lacune_annoncee_sans_rien_inventer(agent):
    reponse = agent.respond("Je veux obtenir mon permis de conduire")
    assert reponse["type_reponse"] == "lacune"
    assert not reponse["etapes"] and not reponse["pieces_requises"] and not reponse["citations"]
    assert "source ouverte" in reponse["reponse"]


def test_demande_illicite_refusee(agent):
    assert agent.respond("Comment pirater le site idcam ?")["type_reponse"] == "refus"
    assert agent.respond("Je veux faire un faux passeport")["type_reponse"] == "refus"


def test_reponse_en_anglais(agent):
    reponse = agent.respond("I want to renew my passport", langue="EN")
    assert "Procedure : Passport" in reponse["reponse"]
    assert "You remain responsible" in reponse["reponse"]


def test_journal_indique_le_vrai_mode_quand_le_llm_est_absent(monkeypatch):
    monkeypatch.setenv("LLM_URL", "http://127.0.0.1:9/api/generate")
    monkeypatch.setenv("LLM_TIMEOUT", "1")
    reponse = AgentAssistant(use_llm=True).respond("Je veux un passeport")
    assert reponse["mode_generation"] == "extraits_sources_llm_indisponible"
    assert reponse["audit_log"][2]["mode"] == "extraits_sources_llm_indisponible"


def test_reponse_llm_inventee_ecartee_au_profit_des_extraits(monkeypatch):
    monkeypatch.setattr("agent.appeler_llm", lambda prompt: "Le passeport coûte 500 000 FCFA. Vous êtes responsable.")
    reponse = AgentAssistant(use_llm=True).respond("Je veux un passeport")
    assert reponse["mode_generation"] == "extraits_sources_apres_rejet_llm"
    assert "500 000" not in reponse["reponse"]


def test_reponse_llm_fidele_conservee(monkeypatch):
    monkeypatch.setattr("agent.appeler_llm", lambda prompt: "La validité du passeport est de 5 ans [Articles 5 et 6]. Vous restez responsable.")
    reponse = AgentAssistant(use_llm=True).respond("Je veux un passeport")
    assert reponse["mode_generation"] == "llm"


def test_la_trace_nomme_chacun_des_quatre_agents(monkeypatch):
    monkeypatch.setattr("agent.appeler_llm", lambda prompt: "Le passeport coûte 500 000 FCFA. Vous êtes responsable.")
    reponse = AgentAssistant(use_llm=True).respond("Je veux un passeport")
    agents = [e["agent"] for e in reponse["audit_log"]]
    assert agents == ["analyse", "recherche", "orchestrateur", "validation"]
    assert reponse["audit_log"][3]["etape"] == "rejet_llm"


def test_les_agents_sont_injectables():
    from analyse import AgentAnalyse
    from recherche import AgentRecherche

    analyse, recherche = AgentAnalyse(), AgentRecherche()
    orchestrateur = AgentAssistant(use_llm=False, analyse=analyse, recherche=recherche)
    assert orchestrateur.catalogue is analyse.catalogue
    assert orchestrateur.analyse.analyser("Je veux faire un faux passeport").issue == "refus"
    assert orchestrateur.respond("Je veux un passeport")["audit_log"][1]["agent"] == "recherche"


def test_le_prompt_recoit_la_question_masquee(monkeypatch):
    vu = {}
    monkeypatch.setattr("agent.appeler_llm", lambda prompt: vu.setdefault("prompt", prompt))
    AgentAssistant(use_llm=True).respond("Je m'appelle Jean Mballa, tel 699123456, je veux un passeport")
    assert "Mballa" not in vu["prompt"] and "699123456" not in vu["prompt"]


# ------------------------------------------------------------------ Auditeur
def _citation(identifiant="decret_2021_347_passeport::art_5_6"):
    chunk = kb.par_id[identifiant]
    return {"id": chunk["id"], "doc": chunk["doc"], "procedure_id": chunk["procedure_id"], "article": chunk["article"],
            "texte": chunk["texte"], "source_url": chunk["source_url"], "statut_verification": chunk["statut_verification"]}


def _audit(reponse, citations, **options):
    return audit(reponse, citations, base=kb.par_id, procedure_id="passeport", **options)


def test_auditeur_bloque_un_montant_invente():
    resultat = _audit("La CNI coûte 500 000 FCFA, vous êtes responsable.", [_citation()])
    assert resultat.verdict == "non_conforme" and resultat.decision == "bloquer"


def test_auditeur_bloque_un_delai_invente():
    assert _audit("Délai : 12 jours, vous êtes responsable.", [_citation()]).decision == "bloquer"


def test_auditeur_bloque_un_article_inexistant():
    assert _audit("Selon l'article 99, vous êtes responsable.", [_citation()]).decision == "bloquer"


def test_auditeur_bloque_une_citation_hors_sujet():
    hors_sujet = _citation("ordonnance_81_02_etat_civil::art_48")
    hors_sujet["procedure_id"] = "acte_mariage"
    assert _audit("Vous êtes responsable.", [hors_sujet]).decision == "bloquer"


def test_auditeur_bloque_une_citation_falsifiee():
    faux = _citation()
    faux["texte"] = "La validité du passeport est de 50 ans."
    resultat = _audit("La validité est de 50 ans, vous êtes responsable.", [faux])
    assert resultat.decision == "bloquer"
    assert any(c.nom == "integrite" and c.resultat == "echec" for c in resultat.controles)


def test_auditeur_bloque_une_reponse_sans_source():
    assert audit("Faites comme ceci, vous êtes responsable.", [], base=kb.par_id).decision == "bloquer"


def test_auditeur_valide_un_fait_present_dans_la_source():
    resultat = _audit("La validité du passeport est de 5 ans [Articles 5 et 6]. Vous restez responsable.", [_citation()])
    assert resultat.verdict == "conforme" and resultat.decision == "publier"


def test_auditeur_reserve_si_source_a_verifier():
    resultat = _audit("Passez par passcam.cm. Vous restez responsable.", [_citation("procedure_passcam_passeport::etape_1")])
    assert resultat.verdict == "partiel" and resultat.decision == "publier_avec_reserve"


def test_auditeur_reserve_si_ton_subjectif():
    assert _audit("Je pense que la validité est de 5 ans. Vous restez responsable.", [_citation()]).verdict == "partiel"


def test_toutes_les_reponses_composees_passent_l_audit(agent):
    """Chaque démarche et chaque cas : la réponse sourcée ne doit jamais être bloquée."""
    for demarche in agent.catalogue.demarches:
        if demarche["statut"] == "lacune":
            continue
        for cas in demarche["cas"] or [None]:
            for langue in ("FR", "EN"):
                reponse = agent._repondre(demarche["nom"], demarche, cas, langue, None)
                resultat = audit(
                    reponse["reponse"], reponse["citations"], base=kb.par_id, procedure_id=demarche["id"],
                    procedures_admises=[demarche["id"], *demarche.get("procedures_liees", [])],
                    type_reponse="reponse", statut_demarche=demarche["statut"],
                )
                assert resultat.decision != "bloquer", (demarche["id"], cas and cas["id"], langue, resultat.gaps)


# ------------------------------------------------------------------ Questions de précision
def test_chaque_nom_de_demarche_se_retrouve_lui_meme(agent):
    """Un bouton de précision envoie le nom de la démarche : il ne doit jamais boucler."""
    for demarche in agent.catalogue.demarches:
        for nom in (demarche["nom"], demarche["nom_en"]):
            detection = agent.catalogue.detecter(nom)
            assert detection.demarche and detection.demarche["id"] == demarche["id"], nom


def test_chaque_bouton_de_cas_aboutit_au_bon_cas(agent):
    for demarche in agent.catalogue.demarches:
        for langue, cle in (("FR", "libelle"), ("EN", "libelle_en")):
            nom = demarche["nom_en"] if langue == "EN" else demarche["nom"]
            for cas in demarche["cas"]:
                reponse = agent.respond(f"{nom} : {cas[cle]}", langue=langue)
                assert reponse["procedure_id"] == demarche["id"], cas[cle]
                assert reponse["cas"] == cas["id"], cas[cle]


def test_les_boutons_proposes_par_une_clarification_aboutissent(agent):
    reponse = agent.respond("Je veux créer mon entreprise")
    assert reponse["type_reponse"] == "clarification"
    for option in reponse["options"]:
        suite = agent.respond(option["message"], ["Je veux créer mon entreprise"])
        assert suite["procedure_id"], option


@pytest.mark.parametrize(
    "historique, message, attendu",
    [
        (["Je veux une CNI"], "je l'ai perdue", "cni"),
        (["Je veux un permis de construire"], "combien ça coûte ?", "permis_construire"),
        (["Je veux un passeport"], "quelles pièces ?", "passeport"),
    ],
)
def test_une_suite_de_conversation_garde_la_demarche(agent, historique, message, attendu):
    assert agent.catalogue.detecter(message, historique).demarche["id"] == attendu


@pytest.mark.parametrize(
    "message",
    ["Quel est le prix du pain au marché ?", "Quelle est la capitale du Cameroun ?"],
)
def test_une_question_sans_rapport_ne_reprend_pas_la_demarche_precedente(agent, message):
    assert agent.respond(message, ["Je veux une CNI"])["type_reponse"] == "hors_perimetre"


def test_un_mot_vague_prime_sur_une_demarche_incompatible_de_l_historique(agent):
    reponse = agent.respond("et pour un permis ?", ["Je veux une CNI"])
    assert reponse["type_reponse"] == "clarification"


# ------------------------------------------------------------------ Mémoire du cas
def test_le_cas_annonce_juste_avant_est_repris(agent):
    reponse = agent.respond("Carte nationale d'identité (CNI)", ["Je veux renouveler ma carte"])
    assert reponse["cas"] == "peremption"
    assert agent.respond("combien ça coûte ?", ["Ma CNI est perdue"])["cas"] == "perte"


def test_un_ancien_cas_ne_resert_pas_pour_une_nouvelle_demande(agent):
    historique = ["Je veux renouveler ma carte", "Carte nationale d'identité (CNI)"]
    assert agent.respond("Je veux une CNI", historique)["type_reponse"] == "clarification"


def test_le_cas_d_une_autre_demarche_n_est_pas_repris(agent):
    assert agent.respond("Je veux une CNI", ["J'ai perdu mon passeport"])["type_reponse"] == "clarification"


# ------------------------------------------------------------------ Conversation
@pytest.mark.parametrize(
    "message, sujet, langue",
    [
        ("Bonjour", "salutation", "FR"),
        ("Salut !", "salutation", "FR"),
        ("Bonsoir, comment ça va ?", "etat", "FR"),
        ("Hi", "salutation", "EN"),
        ("Hello there", "salutation", "EN"),
        ("Merci beaucoup", "remerciement", "FR"),
        ("thanks a lot", "remerciement", "EN"),
        ("Au revoir", "au_revoir", "FR"),
        ("bye", "au_revoir", "EN"),
        ("Que peux-tu faire ?", "aide", "FR"),
        ("Qui es-tu ?", "aide", "FR"),
        ("Comment ça marche ?", "aide", "FR"),
        ("what can you do?", "aide", "EN"),
        ("Peux tu m'en dire plus en ce qui concerne les procédures administratives ??", "apercu", "FR"),
        ("Quelles démarches existent ?", "apercu", "FR"),
        ("tell me about administrative procedures", "apercu", "EN"),
        ("Je veux faire une démarche", "apercu", "FR"),
        ("Salut mon ami", "salutation", "FR"),
        ("Bonjour mon cher ami", "salutation", "FR"),
        ("Non", "accord", "FR"),
        ("Oui d'accord", "accord", "FR"),
        ("ok", "accord", "FR"),
        ("Comment tu t'appelles ?", "aide", "FR"),
        ("Tu es un robot ?", "identite", "FR"),
        ("Comment vas tu ?", "etat", "FR"),
        ("Yo", "salutation", "FR"),
        ("Qui t'a créé ?", "createur", "FR"),
        ("who made you?", "createur", "EN"),
        ("Tu parles anglais ?", "identite", "FR"),
        ("are you a human?", "identite", "EN"),
    ],
)
def test_une_conversation_recoit_une_reponse_directe(agent, message, sujet, langue):
    analyse = agent.analyse.analyser(message)
    assert analyse.issue == "conversation" and analyse.sujet.nom == sujet and analyse.sujet.langue == langue
    reponse = agent.respond(message)
    assert reponse["type_reponse"] == "conversation"
    assert not reponse["citations"] and not reponse["etapes"] and not reponse["reponse"].startswith("Je n'ai pas trouvé")


def test_la_reponse_repond_dans_la_langue_du_message_meme_si_l_interface_est_en_francais(agent):
    assert agent.respond("Hi", langue="FR")["reponse"].startswith("Hello")
    assert agent.respond("Bonjour", langue="EN")["reponse"].startswith("Bonjour")


def test_l_apercu_est_chiffre_d_apres_le_catalogue(agent):
    texte = agent.respond("Quelles démarches connais-tu ?")["reponse"]
    total = len(agent.catalogue.demarches)
    lacunes = sum(d["statut"] == "lacune" for d in agent.catalogue.demarches)
    assert f"J'en connais {total}" in texte and f"Pour {lacunes} autres" in texte


def test_salutation_et_aide_proposent_des_exemples_qui_aboutissent(agent):
    for message in ("Bonjour", "Que peux-tu faire ?", "Quelles démarches existent ?"):
        options = agent.respond(message)["options"]
        assert len(options) >= 3
        for option in options:
            assert agent.respond(option["message"])["type_reponse"] in ("reponse", "clarification")


@pytest.mark.parametrize(
    "message",
    ["Bonjour, je veux un passeport", "Salut, comment payer la patente ?", "Hello, I want to renew my passport"],
)
def test_une_salutation_n_empeche_pas_de_traiter_la_demande(agent, message):
    assert agent.respond(message)["type_reponse"] == "reponse"


@pytest.mark.parametrize(
    "message",
    ["Quel est le prix du pain ?", "Quelle est la capitale du Cameroun ?", "Bonjour, j'ai un souci avec mon dossier", "Merci pour le pain"],
)
def test_un_autre_sujet_n_est_pas_pris_pour_de_la_conversation(agent, message):
    assert agent.respond(message)["type_reponse"] == "hors_perimetre"


def test_hors_perimetre_propose_des_exemples_au_lieu_d_une_impasse(agent):
    reponse = agent.respond("Bonjour, j'ai un souci avec mon dossier")
    assert reponse["reponse"].startswith("Bonjour.") and len(reponse["options"]) >= 4


def test_un_mot_vague_du_quotidien_demande_une_precision(agent):
    for message, attendu in (("Data", "protection_donnees"), ("J'ai perdu mes papiers", "cni")):
        reponse = agent.respond(message)
        assert reponse["type_reponse"] == "clarification", message
        assert attendu in [agent.catalogue.demarches_citees(o["message"])[0]["id"] for o in reponse["options"]], message


def test_la_conversation_passe_l_audit_sans_blocage(agent):
    from agent import AgentAssistant  # noqa: F401  (même instance que la fixture)
    for message in ("Bonjour", "Que peux-tu faire ?", "Quelles démarches existent ?", "Merci", "Au revoir", "Hi"):
        reponse = agent.respond(message)
        resultat = agent.validation.controler_reponse(reponse, None)
        assert resultat.decision == "publier", (message, resultat.gaps)


@pytest.mark.parametrize(
    "message, attendu",
    [("Mon enfant vient de naître", "acte_naissance"), ("Je veux ouvrir une boutique", "commercant_individuel")],
)
def test_une_formulation_courante_retrouve_la_demarche_ou_demande_laquelle(agent, message, attendu):
    reponse = agent.respond(message)
    ids = [reponse["procedure_id"]] if reponse["procedure_id"] else [agent.catalogue.demarches_citees(o["message"])[0]["id"] for o in reponse["options"]]
    assert attendu in ids, (message, reponse["type_reponse"])


def test_une_deuxieme_salutation_n_est_pas_une_repetition_de_la_presentation(agent):
    premiere = agent.respond("Bonjour")["reponse"]
    suite = agent.respond("Salut", ["Bonjour"])["reponse"]
    assert premiere != suite and "je vous écoute" in suite
    assert "bien" in agent.respond("Comment vas tu ?", ["Yo"])["reponse"]


# ------------------------------------------------------------------ Conversation rédigée par le modèle
def test_le_modele_redige_la_conversation_quand_il_est_actif(monkeypatch):
    vu = {}
    monkeypatch.setattr("agent.appeler_llm", lambda prompt: vu.setdefault("prompt", prompt) and "Bonjour ! Dites-moi quelle démarche vous intéresse.")
    agent = AgentAssistant(use_llm=True)
    reponse = agent.respond("Bonjour")
    assert reponse["type_reponse"] == "conversation" and reponse["mode_generation"] == "llm"
    assert reponse["reponse"].startswith("Bonjour !") and reponse["options"]
    agent.respond("Salut, je m'appelle Jean Mballa, tel 699123456")
    assert "Mballa" not in vu["prompt"] and "699123456" not in vu["prompt"]


def test_le_modele_repond_aussi_aux_messages_inconnus_mais_pas_aux_demandes_de_demarche(monkeypatch):
    monkeypatch.setattr("agent.appeler_llm", lambda prompt: "Je ne peux pas vous aider sur ce sujet, mais je connais de nombreuses démarches.")
    agent = AgentAssistant(use_llm=True)
    assert agent.respond("Quel temps fait-il ?")["mode_generation"] == "llm"
    assert agent.respond("Que peux-tu faire ?")["mode_generation"] == "regles"  # texte fixe, chiffré d'après le catalogue


@pytest.mark.parametrize("texte", ["Le passeport coûte 500 000 FCFA.", "Voir http://exemple.cm", "", "x" * 900])
def test_une_reponse_de_conversation_inventee_est_ecartee_au_profit_des_textes_fixes(monkeypatch, texte):
    monkeypatch.setattr("agent.appeler_llm", lambda prompt: texte)
    reponse = AgentAssistant(use_llm=True).respond("Bonjour")
    assert reponse["mode_generation"] == "regles" and "je suis GOVIA" in reponse["reponse"]


def test_modele_indisponible_la_conversation_reste_assuree(monkeypatch):
    def panne(prompt):
        raise ConnectionError("hors ligne")

    monkeypatch.setattr("agent.appeler_llm", panne)
    assert AgentAssistant(use_llm=True).respond("Bonjour")["reponse"].startswith("Bonjour, je suis GOVIA")


def test_la_reponse_sourcee_commence_par_une_phrase_formulee(agent):
    texte = agent.respond("Ma CNI est périmée, je veux la renouveler")["reponse"]
    phrase = texte.split("\n")[3]
    assert phrase.startswith("Pour Carte nationale d'identité (CNI), dans le cas « Renouvellement d'une carte périmée », les textes prévoient 5 étapes et 3 pièces à fournir.")
    anglais = agent.respond("I want to renew my passport", langue="EN")["reponse"]
    assert "For Passport, the texts provide for" in anglais


def test_la_phrase_d_introduction_passe_l_audit(agent):
    reponse = agent.respond("Je veux un permis de construire")
    assert agent.validation.controler_reponse(reponse, agent.catalogue.par_id["permis_construire"]).decision != "bloquer"


def test_le_modele_ne_peut_pas_afficher_un_marqueur_de_masquage(monkeypatch):
    monkeypatch.setattr("agent.appeler_llm", lambda prompt: "Bonjour [NOM], ravi de vous rencontrer. Quelle démarche vous intéresse ?")
    agent = AgentAssistant(use_llm=True)
    reponse = agent.respond("Je m'appelle Chris")["reponse"]
    assert reponse.startswith("Bonjour, ravi") and "[NOM]" not in reponse


def test_le_nom_donne_ne_part_pas_chez_le_modele_et_son_marqueur_ne_revient_pas(monkeypatch):
    vu = {}
    monkeypatch.setattr("agent.appeler_llm", lambda prompt: vu.setdefault("prompt", prompt) and "Merci, dites-moi quelle démarche vous intéresse.")
    AgentAssistant(use_llm=True).respond("Je m'appelle Chris")
    assert "Chris" not in vu["prompt"]


def test_retirer_marqueurs():
    from privacy import retirer_marqueurs

    assert retirer_marqueurs("Bonjour [NOM], ravi. Votre date [DATE] !") == "Bonjour, ravi. Votre date !"
    assert retirer_marqueurs("Voir l'article [Article 6].") == "Voir l'article [Article 6]."
