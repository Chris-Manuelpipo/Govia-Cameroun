"""La base doit rester traçable : ces tests empêchent le retour des erreurs corrigées."""
import json

import pytest

from catalogue import Catalogue
from rag import kb, load_all_chunks
from textes_utils import normaliser


@pytest.fixture(scope="module")
def chunks():
    return {c["id"]: c for c in load_all_chunks()}


@pytest.fixture(scope="module")
def catalogue():
    return Catalogue()


def test_chaque_chunk_indique_source_et_verification(chunks):
    for chunk in chunks.values():
        assert chunk["source_url"].startswith("https://"), chunk["id"]
        assert chunk["statut_verification"] in ("verifie", "a_verifier"), chunk["id"]
        assert chunk["type_source"] in ("texte_officiel", "reproduction", "portail_institutionnel"), chunk["id"]


def test_aucune_procedure_inventee_de_la_base_initiale(chunks):
    textes = " ".join(c["titre"] + c["texte"] for c in chunks.values())
    for trace in ["Casablanca", "impot.gouv.cm", "dcr.gov.cm", "urbanisme.gouv.cm", "Tribunal de Commerce", "DPAE"]:
        assert trace not in textes, trace
    urls = {c["source_url"] for c in chunks.values()}
    assert not any(u.rstrip("/").endswith((".gouv.cm", "dcr.gov.cm")) for u in urls)


def test_articles_corriges_du_decret_cni(chunks):
    """Le décret 2016/375 compte 12 articles : les pièces sont à l'article 6, pas au 11."""
    assert "decret_2016_375_cni::art_13" not in chunks
    assert chunks["decret_2016_375_cni::art_6_c"]["article"].startswith("Article 6")
    assert "retrait" in chunks["decret_2016_375_cni::art_10"]["texte"].lower()
    assert "ID-1" in chunks["decret_2016_375_cni::art_2"]["texte"]


def test_articles_corriges_du_decret_passeport(chunks):
    assert "cinq (05) ans" in chunks["decret_2021_347_passeport::art_5_6"]["texte"]
    assert "refusé" in chunks["decret_2021_347_passeport::art_7"]["texte"]
    assert "passcam" not in chunks["decret_2021_347_passeport::art_7"]["texte"].lower()


def test_loi_2024_017_article_33_porte_sur_l_impact(chunks):
    assert "évaluation d'impact" in chunks["loi_2024_017_protection_donnees::art_33"]["texte"]
    assert "autorisation préalable" in chunks["loi_2024_017_protection_donnees::art_32"]["texte"]
    assert "biométrie" in chunks["loi_2024_017_protection_donnees::art_5_sensible"]["texte"]
    assert "biométrie en matière de santé" in chunks["loi_2024_017_protection_donnees::art_48"]["texte"]


def test_ordonnance_conserve_le_delai_de_trois_mois(chunks):
    assert "délai de trois mois" in chunks["ordonnance_81_02_etat_civil::art_33"]["texte"]
    assert "acte de décès énonce" in chunks["ordonnance_81_02_etat_civil::art_79"]["texte"]
    assert "dans le mois" in chunks["ordonnance_81_02_etat_civil::art_78"]["texte"]


def test_contrat_ecrit_a_l_article_27(chunks):
    assert "doit être constaté par écrit" in chunks["loi_92_007_code_travail::art_27"]["texte"]


def test_pieces_et_etapes_sont_des_extraits_exacts(chunks, catalogue):
    for demarche in catalogue.demarches:
        elements = demarche["pieces"] + demarche["etapes"]
        for cas in demarche["cas"]:
            elements += cas["pieces"]
        for element in elements:
            assert normaliser(element["texte"]) in normaliser(chunks[element["chunk"]]["texte"]), element


def test_les_lacunes_n_ont_aucune_source_et_s_expliquent(catalogue):
    lacunes = [d for d in catalogue.demarches if d["statut"] == "lacune"]
    assert lacunes
    for demarche in lacunes:
        assert not demarche["chunks"] and demarche["note_lacune"] and demarche["note_lacune_en"]


def test_catalogue_depasse_les_pieces_d_identite(catalogue):
    domaines = {d["domaine"] for d in catalogue.demarches if d["statut"] != "lacune"}
    for attendu in ["Création d'entreprise", "Protection sociale", "Impôts et taxes", "Urbanisme et foncier", "Commerce extérieur", "Vie associative"]:
        assert attendu in domaines


def test_index_coherent_avec_les_fichiers(chunks):
    from catalogue import KB_DIR

    index = json.loads((KB_DIR / "index.json").read_text(encoding="utf-8"))
    assert index["total_chunks"] == len(chunks) == len(kb.chunks)


def test_references_internationales_hors_reponses_citoyennes(chunks):
    """RGPD et règlement IA servent à l'analyse d'écarts, jamais de règle citée au citoyen."""
    from agent import AgentAssistant

    etrangers = {i for i, c in chunks.items() if c["procedure_id"] == "references_internationales"}
    assert {"ue_2016_679_rgpd::art_22_1", "ue_2024_1689_reglement_ia::art_50_1"} <= etrangers
    agent = AgentAssistant(use_llm=False)
    for question in [
        "Une décision automatisée par intelligence artificielle est-elle permise ?",
        "Mes données peuvent-elles être envoyées à l'étranger ?",
        "pseudonymisation des données personnelles par une intelligence artificielle",
    ]:
        reponse = agent.respond(question)
        cites = {c["id"] for c in reponse["citations"]}
        assert not cites & etrangers, (question, cites & etrangers)
