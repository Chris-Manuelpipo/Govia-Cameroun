import pytest

from privacy import extraire_champs, masquer


@pytest.mark.parametrize(
    "entree, absent",
    [
        ("Nom: MBALLA Jean Pierre, né le 12 mars 1990 à Yaoundé", "MBALLA"),
        ("Nom: MBALLA Jean Pierre, né le 12 mars 1990 à Yaoundé", "12 mars 1990"),
        ("Nom: MBALLA Jean Pierre, né à Yaoundé", "Yaoundé"),
        ("Je m'appelle Jean Mballa et je veux une CNI", "Mballa"),
        ("Tel: 699 12 34 56", "699"),
        ("Tel: +237 699 12 34 56", "699"),
        ("Tel: 677123456", "677123456"),
        ("Fixe : 222 20 45 87", "222 20"),
        ("CNI n° 112345678 du 12/03/1990", "112345678"),
        ("CNI n° 112345678 du 12/03/1990", "12/03/1990"),
        ("NIU P012345678901X", "P012345678901X"),
        ("Adresse: Bastos, rue 1.234", "Bastos"),
        ("Écrivez à jean.mballa@example.cm", "jean.mballa"),
        ("My name is John Smith", "Smith"),
    ],
)
def test_donnees_personnelles_masquees(entree, absent):
    assert absent not in masquer(entree)


@pytest.mark.parametrize(
    "texte",
    [
        "REPUBLIQUE DU CAMEROUN",
        "Je veux renouveler ma CNI",
        "Le timbre coûte 110000 FCFA",
        "Je veux un permis de construire",
    ],
)
def test_texte_ordinaire_preserve(texte):
    assert masquer(texte) == texte


def test_extraction_des_champs_pour_le_formulaire():
    texte = "Nom : MBALLA\nPrénoms : Jean Pierre\nDate de naissance : 12/03/1990\nProfession : Enseignant"
    champs = extraire_champs(texte)
    assert champs == {"nom": "MBALLA", "prenoms": "Jean Pierre", "date_naissance": "12/03/1990", "profession": "Enseignant"}


def test_la_telemetrie_d_onnxruntime_est_coupee_avant_tout_chargement():
    import os

    import rag  # noqa: F401

    assert os.environ["ORT_DISABLE_TELEMETRY"] == "1"
