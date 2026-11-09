#!/usr/bin/env python3
"""Test de bout en bout de l'interface : Firefox -> Next.js standalone -> FastAPI (sans LLM ni Chroma).

Prérequis : `pip install selenium`, Firefox, geckodriver, et `npm run build` dans frontend/.
Usage : python scripts/test_interface.py [dossier_de_travail]
Variables facultatives : GOVIA_TEST_FIREFOX (binaire), GOVIA_TEST_GECKODRIVER (pilote).
Les captures d'écran sont écrites dans <dossier_de_travail>/captures.

Couvre l'en-tête officiel, les quatre vues, le parcours citoyen (consentement, précision requise, aucun
texte ouvert, fiche), l'accessibilité WCAG A/AA (axe-core), la taille des cibles (44 px), le mouvement
réduit et un écran de 360 px.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
import urllib.error
import urllib.request

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.ui import Select, WebDriverWait

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp(prefix="govia_ui_")
os.makedirs(B, exist_ok=True)
SHOTS = f"{B}/captures"
shutil.rmtree(SHOTS, ignore_errors=True)
os.makedirs(SHOTS)
API, WEB = "8765", "3111"
ORIGINE = f"http://127.0.0.1:{WEB}"
FRONT = f"{R}/frontend"
STANDALONE = f"{FRONT}/.next/standalone"
AXE_URL = "https://cdn.jsdelivr.net/npm/axe-core@4.10.2/axe.min.js"
if not os.path.exists(f"{B}/axe.min.js"):
    urllib.request.urlretrieve(AXE_URL, f"{B}/axe.min.js")
AXE = open(f"{B}/axe.min.js", encoding="utf-8").read()

shutil.copytree(f"{FRONT}/.next/static", f"{STANDALONE}/.next/static", dirs_exist_ok=True)
shutil.copytree(f"{FRONT}/public", f"{STANDALONE}/public", dirs_exist_ok=True)

env_api = dict(
    os.environ, GOVIA_DISABLE_CHROMA="1", GOVIA_USE_LLM="1", LLM_URL="http://127.0.0.1:9/api/generate",
    LLM_TIMEOUT="1", GOVIA_AUDIT_LOG=f"{B}/ui_audit.jsonl", GOVIA_CORS_ORIGINS=ORIGINE,
)
env_web = dict(os.environ, PORT=WEB, HOSTNAME="127.0.0.1", API_URL=f"http://127.0.0.1:{API}", NEXT_TELEMETRY_DISABLED="1")
api = subprocess.Popen([sys.executable, "-m", "uvicorn", "main:app", "--port", API, "--log-level", "warning"], cwd=f"{R}/backend", env=env_api)
web = subprocess.Popen(["node", "server.js"], cwd=STANDALONE, env=env_web, stdout=subprocess.DEVNULL)


def attendre(url):
    for _ in range(120):
        try:
            urllib.request.urlopen(url, timeout=2)
            return
        except Exception:
            time.sleep(0.5)
    raise RuntimeError(f"{url} ne répond pas")


def api_web(chemin, corps=None):
    donnees = json.dumps(corps).encode() if corps is not None else None
    req = urllib.request.Request(f"{ORIGINE}{chemin}", data=donnees, headers={"Content-Type": "application/json"} if donnees else {})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, json.load(e)


def nombre_chat_journalises():
    chemin = f"{B}/ui_audit.jsonl"
    return sum(1 for _ in open(chemin, encoding="utf-8")) if os.path.exists(chemin) else 0


verdicts = []


def verifier(nom, condition, detail=""):
    verdicts.append(bool(condition))
    print(f"{'OK  ' if condition else 'ECHEC'} {nom}{' — ' + str(detail)[:400] if detail and not condition else ''}")


# Cibles interactives visibles de moins de 44 px (hors liens en ligne dans une phrase, exemptés par WCAG 2.5.8).
CIBLES_TROP_PETITES = """
const visible = (e) => {
  const r = e.getBoundingClientRect(); const s = getComputedStyle(e);
  return s.display !== 'none' && s.visibility !== 'hidden' && r.width > 1 && r.height > 1;
};
const petites = [];
for (const e of document.querySelectorAll('button, a[href], input:not([type=hidden]), select, textarea, summary, [role=tab]')) {
  let cible = e;
  if (e.tagName === 'INPUT' && (e.type === 'checkbox' || e.type === 'radio')) cible = e.closest('label') || e;
  if (!visible(cible)) continue;
  const r = cible.getBoundingClientRect();
  const enLigne = e.tagName === 'A' && getComputedStyle(e).display === 'inline' && e.parentElement && e.parentElement.childNodes.length > 1;
  if (!enLigne && (r.width < 43.5 || r.height < 43.5)) petites.push(`${e.tagName.toLowerCase()} « ${(e.innerText || e.getAttribute('aria-label') || '').trim().slice(0, 40)} » ${Math.round(r.width)}x${Math.round(r.height)}`);
}
return petites;
"""

driver = None
try:
    attendre(f"http://127.0.0.1:{API}/")
    attendre(f"{ORIGINE}/")

    print("--- proxy Next.js ---")
    code, donnees = api_web("/api/consentement?langue=FR")
    verifier("GET /api/consentement passe par le proxy", code == 200 and "consentement" in donnees["titre"])
    code, donnees = api_web("/api/chat", {"messages": [{"role": "user", "content": "passeport"}]})
    verifier("POST /api/chat sans consentement renvoie 403 et un detail", code == 403 and "detail" in donnees, donnees)
    code, donnees = api_web("/api/catalogue")
    verifier("GET /api/catalogue renvoie les 43 démarches", code == 200 and len(donnees) == 43, code)
    code, donnees = api_web("/api/stats")
    verifier("GET /api/stats renvoie le nombre de documents", code == 200 and donnees["total_documents"] == 44, donnees)
    code, donnees = api_web("/api/documents")
    verifier("GET /api/documents renvoie les 44 documents", code == 200 and len(donnees["documents"]) == 44, code)

    print("--- navigateur ---")
    options = Options()
    options.add_argument("-headless")
    if os.getenv("GOVIA_TEST_FIREFOX"):
        options.binary_location = os.environ["GOVIA_TEST_FIREFOX"]
    options.set_preference("intl.accept_languages", "fr")
    options.set_preference("ui.prefersReducedMotion", 1)  # l'interface doit respecter prefers-reduced-motion
    os.environ.setdefault("TMPDIR", f"{B}/ff_tmp")
    os.makedirs(os.environ["TMPDIR"], exist_ok=True)
    pilote = os.getenv("GOVIA_TEST_GECKODRIVER")
    driver = webdriver.Firefox(options=options, service=Service(pilote) if pilote else Service())
    driver.set_window_size(1366, 900)
    driver.set_script_timeout(90)
    attente = WebDriverWait(driver, 25)

    def corps():
        return driver.find_element(By.TAG_NAME, "body").text

    def boutons():
        return driver.find_elements(By.TAG_NAME, "button")

    def bouton(texte):
        return next(b for b in boutons() if b.text == texte)

    def attendre_fin():
        time.sleep(0.4)
        attente.until(lambda d: not d.find_elements(By.CSS_SELECTOR, "[data-chargement]"))
        time.sleep(0.5)

    def poser(question):
        champ = driver.find_element(By.CSS_SELECTOR, "input[type=text]")
        champ.clear()
        champ.send_keys(question)
        driver.find_element(By.CSS_SELECTOR, "button[type=submit]").click()
        attendre_fin()

    def clic(element):
        driver.execute_script("arguments[0].click()", element)
        time.sleep(0.3)

    def onglet(debut):
        clic(next(b for b in driver.find_elements(By.CSS_SELECTOR, "[role=tab]") if b.text.startswith(debut)))

    def fiche():
        return driver.find_element(By.TAG_NAME, "article").text

    def photo(nom):
        time.sleep(0.2)
        driver.save_screenshot(f"{SHOTS}/{nom}.png")

    def audit_accessibilite(nom):
        driver.execute_script(AXE)
        resultat = driver.execute_async_script(
            "const fin = arguments[arguments.length - 1];"
            "axe.run(document, {runOnly: {type: 'tag', values: ['wcag2a', 'wcag2aa']}})"
            ".then(r => fin(r.violations.map(v => ({id: v.id, impact: v.impact, noeuds: v.nodes.length,"
            " exemple: v.nodes[0].target.join(' ') + ' :: ' + v.nodes[0].any.map(a => a.message).join(' ').slice(0, 160)}))))"
            ".catch(e => fin([{id: 'erreur', exemple: String(e)}]))"
        )
        verifier(f"Accessibilité WCAG A/AA (axe) : {nom}", not resultat, resultat)

    def cibles(nom):
        petites = driver.execute_script(CIBLES_TROP_PETITES)
        verifier(f"Cibles cliquables de 44 px au moins : {nom}", not petites, petites)

    def lignes():
        """Démarches affichées, en carte (grand écran) ou en ligne de tableau (mobile)."""
        return [e for e in driver.find_elements(By.CSS_SELECTOR, "tr[data-demarche], li[data-carte]") if e.is_displayed()]

    def bouton_demarche(nom):
        return next(b for b in driver.find_elements(By.CSS_SELECTOR, "tr[data-demarche] button, li[data-carte] button") if b.is_displayed() and b.text.split("\n")[0] == nom)

    def echanges():
        """Un élément par question posée : la question et la réponse qui la suit."""
        return driver.find_elements(By.CSS_SELECTOR, "section[aria-label='Échanges'] ol > li")

    def fiche_visible():
        return any(a.is_displayed() for a in driver.find_elements(By.TAG_NAME, "article"))

    def carte(libelle):
        return next(b for b in driver.find_elements(By.CSS_SELECTOR, "main [role=group] button[aria-pressed]") if libelle in b.text)

    def choisir_option(libelle):
        clic(next(label for label in driver.find_elements(By.CSS_SELECTOR, "fieldset label") if label.text == libelle))

    print("--- en-tête officiel et annuaire, sans consentement ---")
    driver.get(f"{ORIGINE}/")
    attente.until(lambda d: len(lignes()) == 43)
    texte = corps()
    verifier("L'annuaire s'ouvre d'abord et liste les 43 démarches", "Annuaire des démarches" in texte)
    compte = driver.execute_script("return Array.from(document.querySelectorAll('main [role=group][aria-label] button[aria-pressed]')).map(b => b.innerText.replace(/\\n/g, ' '))")
    verifier("Les cartes d'état portent les chiffres de l'API", all(any(c.startswith(n) for c in compte) for n in ["43 ", "31 ", "2 ", "10 "]), compte)
    verifier("L'administration compétente est indiquée", "Direction Générale des Impôts" in texte)
    verifier("Plus de mention « Prototype » ni de bande « Règles d'or »", "PROTOTYPE" not in texte.upper() and "RÈGLES D'OR" not in texte.upper(), texte[:300])
    verifier("La réserve d'usage reste au pied de la page", "ne remplace ni le texte officiel" in texte)
    verifier(
        "L'en-tête porte les devises dans les deux langues",
        all(m in texte.upper() for m in ["RÉPUBLIQUE DU CAMEROUN", "PAIX – TRAVAIL – PATRIE", "REPUBLIC OF CAMEROON", "PEACE – WORK – FATHERLAND"]),
        texte[:300],
    )
    couleurs = driver.execute_script("return Array.from(document.querySelectorAll('header span')).slice(0, 3).map(e => getComputedStyle(e).backgroundColor)")
    verifier("La bande tricolore est vert, rouge, jaune", couleurs == ["rgb(0, 122, 61)", "rgb(206, 17, 38)", "rgb(252, 209, 22)"], couleurs)
    nav = driver.find_elements(By.CSS_SELECTOR, "nav button")
    verifier("Quatre onglets de navigation", [b.text for b in nav] == ["Annuaire", "Assistant", "Sources", "Données et consentement"], [b.text for b in nav])
    langue = bouton("FR")
    position = driver.execute_script("const r = arguments[0].getBoundingClientRect(); return [r.right, r.top, window.innerWidth]", langue)
    verifier("Le sélecteur FR/EN est en haut à droite, FR actif", position[0] > position[2] * 0.8 and position[1] < 100 and langue.get_attribute("aria-pressed") == "true", position)
    photo("01_annuaire")
    audit_accessibilite("annuaire")
    cibles("annuaire")

    champ_filtre = driver.find_element(By.CSS_SELECTOR, "input[type=search]")
    champ_filtre.send_keys("passe")
    time.sleep(0.3)
    verifier("La recherche par nom réduit la liste", len(lignes()) == 1 and "Passeport" in lignes()[0].text, len(lignes()))
    champ_filtre.clear()
    champ_filtre.send_keys("identite")
    time.sleep(0.3)
    verifier("La recherche ignore les accents", any("identité" in l.text for l in lignes()), len(lignes()))
    champ_filtre.clear()
    champ_filtre.send_keys("DGI")
    time.sleep(0.3)
    verifier("La recherche porte aussi sur l'administration", len(lignes()) >= 6 and all("DGI" in l.text for l in lignes()), len(lignes()))
    champ_filtre.clear()
    time.sleep(0.2)
    clic(carte("Sans texte ouvert"))
    verifier("La catégorie « sans texte ouvert » donne les 10 démarches", len(lignes()) == 10, len(lignes()))
    verifier("Les lacunes forment une section à part, expliquée", "10 démarches sans texte ouvert" in corps() and "n'a trouvé aucun texte ouvert" in corps())
    photo("02_annuaire_lacunes")
    clic(carte("Toutes les démarches"))
    verifier("Toutes les démarches ramène les 43 lignes", len(lignes()) == 43, len(lignes()))
    Select(driver.find_element(By.CSS_SELECTOR, "main select")).select_by_visible_text("Véhicules (3)")
    time.sleep(0.3)
    verifier("Le filtre par domaine réduit la liste", len(lignes()) == 3, len(lignes()))
    Select(driver.find_element(By.CSS_SELECTOR, "main select")).select_by_value("")
    time.sleep(0.2)

    print("--- sources et données, sans consentement ---")
    clic(bouton("Sources"))
    attente.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "tbody tr")) == 44)
    tuiles = [t.text.replace("\n", " ") for t in driver.find_elements(By.CSS_SELECTOR, "dl > div")]
    verifier(
        "Les statistiques de la base viennent de l'API",
        all(any(mot in t and valeur in t.split() for t in tuiles) for mot, valeur in [("Documents", "44"), ("indexés", "256"), ("vérifiés", "248"), ("à vérifier", "8")]),
        tuiles,
    )
    jauge = driver.find_element(By.CSS_SELECTOR, "[role=img]").get_attribute("aria-label")
    verifier("La jauge de vérification a un nom accessible", jauge == "248 extraits vérifiés sur 256 ; 8 à vérifier", jauge)
    texte = corps()
    liens = driver.find_elements(By.CSS_SELECTOR, "tbody a[href^='http']")
    verifier("Chaque document renvoie vers sa source", len(liens) == 44 and all(l.get_attribute("target") == "_blank" for l in liens), len(liens))
    verifier("L'adresse de chaque source est visible", "prc.cm/files" in texte and "yaounde.eregulations.org" in texte)
    verifier("Le type de source est indiqué", "Texte officiel" in texte and "Reproduction" in texte and "Portail" in texte)
    photo("03_sources")
    audit_accessibilite("sources")
    cibles("sources")
    Select(driver.find_elements(By.CSS_SELECTOR, "main select")[1]).select_by_visible_text("À vérifier")
    time.sleep(0.3)
    verifier(
        "Le filtre « À vérifier » isole les 2 documents et dit pourquoi",
        len(driver.find_elements(By.CSS_SELECTOR, "tbody tr")) == 2 and "Portail inaccessible au robot" in corps(),
        len(driver.find_elements(By.CSS_SELECTOR, "tbody tr")),
    )
    Select(driver.find_elements(By.CSS_SELECTOR, "main select")[1]).select_by_visible_text("Toutes")

    clic(bouton("Données et consentement"))
    attente.until(lambda d: d.find_elements(By.CSS_SELECTOR, "dl"))
    texte = corps()
    verifier(
        "La vue Données réunit la notice et les chiffres de la base",
        all(m in texte for m in ["Vos données et votre consentement", "La base de connaissances en chiffres", "loi n° 2024/017", "Aucun accord donné"]),
        texte[:500],
    )
    photo("04_donnees")
    audit_accessibilite("données et consentement")
    cibles("données et consentement")

    print("--- consentement ---")
    clic(bouton("Assistant"))
    attente.until(lambda d: d.find_elements(By.CSS_SELECTOR, "dl"))
    champ = driver.find_element(By.CSS_SELECTOR, "input[type=text]")
    verifier("Saisie bloquée avant le consentement", not champ.is_enabled())
    verifier("Le champ explique pourquoi il est bloqué", "Acceptez" in (champ.get_attribute("placeholder") or "") and "Saisie bloquée" in corps())
    verifier("Bouton Envoyer bloqué avant le consentement", not driver.find_element(By.CSS_SELECTOR, "button[type=submit]").is_enabled())
    notice = driver.find_element(By.TAG_NAME, "dl").text
    verifier("La notice expose finalité, droits et limites", all(m in notice for m in ["Finalité", "Vos droits", "Limites", "intervention humaine", "Transfert à l'étranger"]), notice)
    verifier("Un refus est possible", any(b.text == "Refuser" for b in boutons()))
    photo("05_notice")
    audit_accessibilite("notice")
    cibles("notice")
    clic(bouton("Refuser"))
    verifier("Refuser ramène à l'annuaire", len(lignes()) == 43 or "Annuaire des démarches" in corps())
    journal_avant = nombre_chat_journalises()
    clic(bouton_demarche("Patente"))
    time.sleep(0.5)
    verifier("Un clic sans accord met la demande en attente", "« Patente » sera traitée après votre accord" in corps(), corps()[:400])
    verifier("Aucune question n'est envoyée sans accord", nombre_chat_journalises() == journal_avant and not driver.find_elements(By.TAG_NAME, "article"))
    photo("06_demande_en_attente")
    clic(next(b for b in boutons() if "accepte" in b.text.lower()))
    attente.until(lambda d: d.find_elements(By.TAG_NAME, "article"))
    attendre_fin()
    verifier("Après l'accord, la demande en attente est traitée", "Patente" in fiche(), corps()[:400])

    print("--- fiche patente ---")
    texte = fiche()
    verifier("Toutes sources vérifiées : « Vérifié — sources ouvertes »", "Vérifié — sources ouvertes" in texte, texte[:300])
    verifier("L'administration compétente figure dans la fiche", "Direction Générale des Impôts" in texte, texte[:400])
    verifier("Coût et durée sont présentés", "Procédure gratuite" in texte and "2 j à 7 j" in texte, texte[:700])
    verifier("Pas de doublon dans les pièces", texte.count("Déclaration des contributions des patentes et licences") == 1)
    verifier("Pas de marqueur de mise en forme brut", "**" not in corps())
    verifier("La liste « Textes et sources » du texte n'est pas répétée dans la fiche", "Textes et sources" not in texte)
    verifier("Le rappel de responsabilité reste visible", "Vous restez responsable" in texte)
    verifier("La fiche rappelle ses sources citées, avec lien et état", "SOURCES CITÉES" in texte.upper() and "Vérifié" in texte)
    bulle = echanges()[0]
    verifier(
        "La bulle du fil porte l'indicateur, le titre et le pied « Sources »",
        all(m in bulle.text.upper() for m in ["VÉRIFIÉ — SOURCES OUVERTES", "PATENTE", "SOURCES CITÉES (1)", "EREGULATIONS"]),
        bulle.text,
    )
    liens = bulle.find_elements(By.CSS_SELECTOR, "a[href^='http']")
    verifier("Le pied « Sources » renvoie vers le texte, dans un nouvel onglet", liens and all(l.get_attribute("target") == "_blank" for l in liens))
    photo("07_fiche_patente")
    audit_accessibilite("fiche")
    cibles("fiche")

    print("--- précision requise puis cas ---")
    clic(bouton("Effacer"))
    verifier("Effacer vide le fil et affiche les exemples", "Exemples de questions" in corps() and not driver.find_elements(By.TAG_NAME, "article"))
    photo("08_assistant_vide")
    audit_accessibilite("assistant vide")
    cibles("assistant vide")
    poser("Je veux renouveler ma carte")
    radios = driver.find_elements(By.CSS_SELECTOR, "input[type=radio]")
    verifier("Une question vague ouvre l'écran « Précision requise »", "J'ai besoin d'une précision pour vous citer le bon texte." in corps() and len(radios) >= 2, (len(radios), corps()[-500:]))
    verifier(
        "Les options sont les démarches candidates",
        {"Carte nationale d'identité (CNI)", "Carte de séjour"} <= {label.text for label in driver.find_elements(By.CSS_SELECTOR, "fieldset label")},
    )
    verifier("« Continuer » est inactif tant qu'aucune option n'est choisie", not bouton("Continuer").is_enabled())
    verifier("L'agent explique pourquoi il demande", "Pourquoi cette question ?" in corps() and "ordonnance n° 81/02" in corps() and "Éviter l'erreur" in corps())
    verifier("La bulle du fil annonce la précision requise", "PRÉCISION REQUISE" in echanges()[0].text.upper())
    verifier("Une question de précision n'ouvre pas de fiche", not driver.find_elements(By.TAG_NAME, "article"))
    photo("09_precision")
    audit_accessibilite("précision requise")
    cibles("précision requise")
    choisir_option("Carte nationale d'identité (CNI)")
    verifier("Choisir une option active « Continuer »", bouton("Continuer").is_enabled())
    photo("10_precision_option_choisie")
    clic(bouton("Continuer"))
    attendre_fin()
    verifier("« Renouveler » puis CNI retient le cas du renouvellement", "Renouvellement d'une carte périmée" in fiche(), corps()[-300:])
    poser("Je veux une CNI")
    verifier("Sans indice, l'agent demande le cas", "De quel cas s'agit-il" in corps(), corps()[-300:])
    choisir_option("Perte, vol ou détérioration")
    clic(bouton("Continuer"))
    attendre_fin()
    texte = fiche()
    verifier("Le choix du cas donne la bonne pièce", "attestation de déclaration de perte" in texte.lower(), texte[:600])
    verifier("L'état ne prétend pas que tout est vérifié", "À vérifier" in texte and "Vérifié — sources ouvertes" not in texte, texte[:400])
    verifier("La raison est donnée", "n'a pas encore été vérifiée" in texte, texte[:400])
    verifier("L'avertissement sur les sources à vérifier n'est pas répété", texte.count("pas encore") == 1, texte[:500])
    verifier("Les onglets annoncent leur contenu", all(any(b.text.startswith(n) for b in driver.find_elements(By.CSS_SELECTOR, "[role=tab]")) for n in ["Démarche", "Sources (", "Contrôle (", "Formulaire"]))
    photo("11_fiche_cni")

    print("--- checklist des pièces ---")
    case = driver.find_elements(By.CSS_SELECTOR, "article input[type=checkbox]")[-1]
    verifier("Le compteur de pièces démarre à zéro", "0 sur 1 prête" in fiche(), fiche()[:700])
    clic(case)
    verifier("Cocher une pièce met à jour le compteur", "1 sur 1 prête" in fiche(), fiche()[:700])

    print("--- onglets ---")
    onglet("Sources")
    texte = fiche()
    verifier("Les sources affichent le statut de vérification", "À vérifier" in texte and "Vérifié" in texte)
    liens = driver.find_elements(By.CSS_SELECTOR, "article a[href^='http']")
    verifier("Chaque source renvoie vers son texte, dans un nouvel onglet", liens and all(l.get_attribute("target") == "_blank" for l in liens))
    photo("12_onglet_sources")
    audit_accessibilite("onglet sources")
    cibles("onglet sources")
    onglet("Contrôle")
    texte = fiche()
    verifier("Le verdict et la décision sont affichés", "Partiel" in texte and "Publiée avec réserve" in texte, texte[:500])
    verifier("Le mode de rédaction réel est affiché", "Extraits des sources" in texte, texte[:500])
    verifier("Les contrôles portent un nom lisible", "Intégrité des citations" in texte and "Fiabilité des sources" in texte and "integrite" not in texte)
    verifier("Les contrôles n'affichent ni liste brute ni identifiant interne", "['" not in texte and "procedure_idcam" not in texte and "IDCAM pour la Carte" in texte, texte[-500:])
    photo("13_onglet_controle")
    audit_accessibilite("onglet contrôle")
    onglet("Formulaire")
    texte = fiche()
    verifier("Le formulaire annonce que rien n'est soumis", "Rien n'est soumis" in texte)
    entrees = [e for e in driver.find_elements(By.CSS_SELECTOR, "article label input") if e.get_attribute("type") not in ("file", "checkbox")]
    verifier("Le formulaire commence vide : aucune valeur inventée", entrees and all(e.get_attribute("value") == "" for e in entrees))
    photo("14_onglet_formulaire")
    audit_accessibilite("onglet formulaire")
    cibles("onglet formulaire")
    onglet("Démarche")
    verifier("La case cochée reste cochée après un changement d'onglet ou se remet à zéro sans erreur", "sur 1 prête" in fiche())

    print("--- longue démarche ---")
    poser("Je veux un permis de construire")
    texte = fiche()
    sous_titres = [h.text for h in driver.find_elements(By.CSS_SELECTOR, "article h3")]
    verifier("Étapes et pièces sont groupées par fiche", sous_titres.count("Obtention du plan de masse et de situation") == 2, sous_titres)
    verifier("Le préfixe de la fiche n'est pas répété à chaque ligne", "Obtention du plan de masse et de situation : " not in texte)
    verifier("Le coût total est visible, son détail reste replié", "Le coût total de la procédure est estimé à CFA 41,900" in texte and "Détail (" in texte, texte[:500])
    verifier("Le détail du coût est masqué par défaut", "11,000 XAF pour la demande et les 10 plans" not in texte)
    verifier("La numérotation des étapes continue d'un groupe à l'autre", "22." in texte)
    haut = driver.execute_script("return document.querySelector('article').getBoundingClientRect().top - document.querySelector('section[aria-label=\"Fiche\"]').getBoundingClientRect().top")
    verifier("La nouvelle fiche s'ouvre depuis son début", haut < 40, haut)
    photo("15_fiche_permis")
    audit_accessibilite("longue démarche")
    cibles("longue démarche")

    print("--- aucun texte ouvert ---")
    poser("Je veux obtenir mon permis de conduire")
    texte = corps()
    verifier(
        "Lacune annoncée sans inventer : écran « Aucun texte ouvert disponible. »",
        "Aucun texte ouvert disponible." in texte and "Plutôt que de vous donner une réponse approximative" in texte,
        texte[-600:],
    )
    verifier("L'encadré de transparence a une bordure verte", driver.execute_script("return Array.from(document.querySelectorAll('h2')).some(h => h.textContent.includes('Transparence') && getComputedStyle(h.parentElement).borderTopColor === 'rgb(26, 127, 55)')"))
    verifier("La base dit ce qu'elle a constaté et l'administration à contacter", "n'a pas pu être consulté" in texte and "Contactez l'administration indiquée : Ministère des Transports" in texte, texte[-800:])
    verifier("Les deux actions sont proposées", {"Poser une autre question", "Contacter un service public"} <= {b.text for b in boutons()})
    verifier("Ce n'est pas présenté comme une fiche", not driver.find_elements(By.TAG_NAME, "article"))
    verifier("La bulle du fil l'annonce aussi", "AUCUN TEXTE OUVERT TROUVÉ" in echanges()[-1].text.upper())
    photo("16_aucun_texte")
    audit_accessibilite("aucun texte ouvert")
    cibles("aucun texte ouvert")
    clic(bouton("Contacter un service public"))
    texte = corps()
    verifier(
        "« Contacter un service public » prépare les questions, sans inventer de coordonnées",
        "Questions à poser à l'administration" in texte and "Quel texte (loi, décret ou arrêté)" in texte and "GOVIA ne détient pas de coordonnées vérifiées" in texte,
        texte[-600:],
    )
    verifier("Les questions peuvent être copiées", any(b.text == "Copier les questions" for b in boutons()))
    verifier("Le bouton de contact annonce son état déplié", bouton("Contacter un service public").get_attribute("aria-expanded") == "true")
    photo("17_aucun_texte_contact")
    audit_accessibilite("aucun texte ouvert, contact déplié")
    poser("Comment faire un faux passeport ?")
    verifier("Demande illicite refusée", "Je ne peux pas aider" in corps())
    poser("Quel est le prix du pain au marché ?")
    verifier("Sujet hors périmètre : réponse claire avec des exemples, sans écran « aucun texte »", "pas sûr d'avoir compris" in corps() and any(b.text == "Créer une société" for b in boutons()) and "Aucun texte ouvert" not in echanges()[-1].text, echanges()[-1].text)
    photo("18_fil_complet")
    ouvrir = next(b for b in boutons() if b.text == "Ouvrir la fiche" and "Permis de construire" in b.find_element(By.XPATH, "./ancestor::li[1]").text)
    clic(ouvrir)
    verifier("Une fiche précédente se rouvre depuis le fil", "Permis de construire" in driver.find_element(By.CSS_SELECTOR, "article h1").text)
    verifier("Le fil indique la fiche affichée", any(b.text == "Fiche affichée" for b in boutons()))

    print("--- conversation naturelle ---")
    poser("Bonjour")
    verifier("« Bonjour » reçoit une réponse de GOVIA avec des exemples", "je suis GOVIA" in corps() and any(b.text == "Renouveler ma CNI" for b in boutons()), corps()[-500:])
    verifier("Une salutation n'ouvre ni fiche ni écran d'impasse", "Aucun texte ouvert" not in echanges()[-1].text and "Ouvrir la fiche" not in echanges()[-1].text)
    poser("Peux tu m'en dire plus en ce qui concerne les procédures administratives ??")
    verifier("Une question générale sur les démarches reçoit un aperçu chiffré", "J'en connais 43" in corps() and "Pour 10 autres" in corps(), corps()[-600:])
    photo("19_conversation")
    audit_accessibilite("conversation")
    cibles("conversation")
    clic(next(b for b in boutons() if b.text == "Créer une société"))
    attendre_fin()
    verifier("Un exemple cliquable aboutit à une vraie réponse", driver.find_elements(By.TAG_NAME, "article") or "PRÉCISION REQUISE" in corps().upper(), corps()[-300:])
    poser("Merci beaucoup")
    verifier("Un remerciement reçoit une réponse polie", "Avec plaisir" in corps())
    poser("Hi")
    verifier("« Hi » reçoit une réponse en anglais même si l'interface est en français", "Hello, I'm GOVIA" in corps(), corps()[-300:])

    print("--- mode clair et mode sombre ---")
    verifier("Le thème clair est actif par défaut", driver.find_element(By.TAG_NAME, "html").get_attribute("data-theme") == "light")
    clic(driver.find_element(By.CSS_SELECTOR, "button[aria-label='Passer en mode sombre']"))
    verifier("La bascule passe en mode sombre", driver.find_element(By.TAG_NAME, "html").get_attribute("data-theme") == "dark")
    fond = driver.execute_script("return getComputedStyle(document.body).backgroundColor")
    verifier("Le fond de page devient sombre", fond != "rgb(255, 255, 255)", fond)
    photo("20_mode_sombre_assistant")
    audit_accessibilite("mode sombre, assistant")
    cibles("mode sombre")
    clic(bouton("Annuaire"))
    time.sleep(0.5)
    photo("21_mode_sombre_annuaire")
    audit_accessibilite("mode sombre, annuaire")
    clic(bouton("Sources"))
    time.sleep(0.5)
    audit_accessibilite("mode sombre, sources")
    clic(bouton("Données et consentement"))
    time.sleep(0.5)
    audit_accessibilite("mode sombre, données")
    clic(driver.find_element(By.CSS_SELECTOR, "button[aria-label='Passer en mode clair']"))
    verifier("La bascule revient au mode clair", driver.find_element(By.TAG_NAME, "html").get_attribute("data-theme") == "light")
    clic(bouton("Assistant"))

    print("--- anglais ---")
    clic(bouton("Effacer"))
    clic(bouton("EN"))
    attente.until(lambda d: d.find_element(By.CSS_SELECTOR, "input[type=text]").get_attribute("placeholder").startswith("Ask"))
    verifier("Le bouton EN traduit l'interface", driver.find_element(By.TAG_NAME, "html").get_attribute("lang") == "en")
    verifier("Les devises restent dans les deux langues", all(m in corps().upper() for m in ["PAIX – TRAVAIL – PATRIE", "PEACE – WORK – FATHERLAND"]))
    poser("I want to renew my passport")
    texte = fiche()
    verifier("Réponse en anglais", "You remain responsible" in texte, texte[-400:])
    verifier("Le compteur de pièces est en anglais", " ready" in texte)
    photo("19_fiche_anglais")
    poser("My CNI")
    verifier("Précision requise en anglais", "I need a clarification to cite the right text." in corps() and any(b.text == "Continue" for b in boutons()), corps()[-400:])
    photo("20_precision_anglais")
    poser("I want my driving licence")
    verifier("Aucun texte ouvert en anglais", "No open text available." in corps() and "Rather than give you an approximate answer" in corps(), corps()[-500:])
    photo("21_aucun_texte_anglais")
    clic(bouton("Directory"))
    attente.until(lambda d: "National identity card (CNI)" in corps())
    verifier("L'annuaire passe en anglais", "Directory of procedures" in corps() and "Identity and civil status" in corps() and "procedures with no open text" in corps())
    photo("22_annuaire_anglais")

    print("--- retrait du consentement ---")
    clic(bouton("Data and consent"))
    verifier("La page des données indique l'accord donné", "Consent given" in corps())
    photo("23_vos_donnees")
    audit_accessibilite("vos données")
    clic(bouton("Withdraw my consent"))
    clic(bouton("Assistant"))
    attente.until(lambda d: not d.find_element(By.CSS_SELECTOR, "input[type=text]").is_enabled())
    verifier("Retirer son accord rebloque la saisie", True)
    verifier("Retirer son accord efface la conversation", "You remain responsible" not in corps() and not driver.find_elements(By.TAG_NAME, "article"))
    verifier("La notice est de nouveau présentée", "Your rights" in corps())

    print("--- mouvement réduit et requêtes externes ---")
    duree = driver.execute_script(
        "const e = document.createElement('span'); e.className = 'indicateur-chargement'; document.body.appendChild(e);"
        "const d = getComputedStyle(e).animationDuration; e.remove(); return d;"
    )
    verifier("prefers-reduced-motion : l'indicateur de chargement ralentit", duree == "3s", duree)
    transitions = driver.execute_script("return Array.from(document.querySelectorAll('button, a')).some(e => parseFloat(getComputedStyle(e).transitionDuration) > 0.01)")
    verifier("prefers-reduced-motion : aucune transition", not transitions)
    ressources = driver.execute_script("return performance.getEntriesByType('resource').map(r => r.name)")
    externes = [r for r in ressources if not r.startswith(ORIGINE)]
    verifier("Aucune ressource chargée hors du serveur", not externes, externes)
    police = driver.execute_script("return getComputedStyle(document.body).fontFamily")
    verifier("La police auto-hébergée est appliquée", "__" in police, police)
    verifier("Les polices sont téléchargées depuis le serveur", any(".woff2" in r for r in ressources), ressources[:5])

    print("--- téléphone (360 px, dans un cadre) ---")
    driver.get(f"{ORIGINE}/")
    driver.set_window_size(900, 900)
    driver.execute_script(
        "document.body.style.background='#777';"
        "document.body.innerHTML = '<iframe id=\"tel\" src=\"/\" style=\"width:360px;height:760px;border:0;display:block;margin:0 auto\"></iframe>';"
    )
    time.sleep(1.5)
    driver.switch_to.frame("tel")

    def debord():
        return driver.execute_script("return [document.documentElement.scrollWidth, document.documentElement.clientWidth]")

    def photo_tel(nom):
        driver.switch_to.default_content()
        photo(nom)
        driver.switch_to.frame("tel")

    attente.until(lambda d: len(lignes()) == 43)
    largeur = debord()
    verifier("360 px : pas de défilement horizontal, annuaire", largeur[0] <= largeur[1], largeur)
    verifier("360 px : le domaine se choisit dans une liste déroulante", driver.find_element(By.TAG_NAME, "select").is_displayed())
    verifier("360 px : l'en-tête garde le logo, le sélecteur de langue et la bascule de thème", "GOVIA" in corps().upper() and bouton("EN").is_displayed())
    verifier("360 px : les quatre onglets restent visibles", [b.text for b in driver.find_elements(By.CSS_SELECTOR, "nav button")] == ["Annuaire", "Assistant", "Sources", "Données"])
    cibles("téléphone, annuaire")
    photo_tel("24_tel_annuaire")
    clic(bouton("Assistant"))
    attente.until(lambda d: any("accepte" in b.text.lower() for b in d.find_elements(By.TAG_NAME, "button")))
    largeur = debord()
    verifier("360 px : pas de défilement horizontal, notice", largeur[0] <= largeur[1], largeur)
    cibles("téléphone, notice")
    photo_tel("25_tel_notice")
    clic(next(b for b in boutons() if "accepte" in b.text.lower()))
    time.sleep(0.5)
    poser("Je veux un permis de construire")
    time.sleep(0.5)
    largeur = debord()
    verifier("360 px : pas de défilement horizontal, longue fiche", largeur[0] <= largeur[1], largeur)
    verifier("360 px : la fiche remplace le fil et est amenée à l'écran", driver.execute_script("return document.querySelector('article').getBoundingClientRect().top") < 300)
    verifier("360 px : un lien ramène aux échanges", any(b.text == "Retour aux échanges" for b in boutons()))
    cibles("téléphone, fiche")
    photo_tel("26_tel_fiche")
    clic(bouton("Retour aux échanges"))
    time.sleep(0.4)
    verifier("360 px : le fil réapparaît avec la bulle et ses sources", "SOURCES CITÉES" in corps().upper() and not fiche_visible())
    verifier("360 px : pas de défilement horizontal, fil", debord()[0] <= debord()[1], debord())
    cibles("téléphone, fil")
    photo_tel("27_tel_fil")
    poser("Je veux une CNI")
    time.sleep(0.4)
    verifier("360 px : la précision requise s'affiche en pleine largeur", "J'ai besoin d'une précision" in corps() and debord()[0] <= debord()[1])
    cibles("téléphone, précision")
    photo_tel("28_tel_precision")
    driver.switch_to.default_content()

    erreurs = [e for e in ("Application error", "Unhandled Runtime") if e in corps()]
    verifier("Aucune erreur applicative affichée", not erreurs, erreurs)
except Exception:
    traceback.print_exc()
    verdicts.append(False)
    if driver:
        driver.switch_to.default_content()
        driver.save_screenshot(f"{SHOTS}/erreur.png")
finally:
    if driver:
        driver.quit()
    web.terminate()
    api.terminate()
    print(f"\n{sum(verdicts)}/{len(verdicts)} vérifications réussies")
    sys.exit(0 if verdicts and all(verdicts) else 1)
