#!/usr/bin/env python3
"""Test de bout en bout de l'interface : Firefox -> Next.js standalone -> FastAPI (sans LLM ni Chroma).

Prérequis : `pip install selenium`, Firefox, geckodriver, et `npm run build` dans frontend/.
Usage : python scripts/test_interface.py [dossier_de_travail]
Variables facultatives : GOVIA_TEST_FIREFOX (binaire), GOVIA_TEST_GECKODRIVER (pilote).
Les captures d'écran sont écrites dans <dossier_de_travail>/captures.
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
from selenium.webdriver.support.ui import WebDriverWait

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

    def lignes():
        return driver.find_elements(By.CSS_SELECTOR, "tbody tr")

    print("--- annuaire, sans consentement ---")
    driver.get(f"{ORIGINE}/")
    attente.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "tbody tr")) == 43)
    texte = corps()
    verifier("L'annuaire s'ouvre d'abord et liste les 43 démarches", "Démarches administratives" in texte)
    verifier("Le résumé vient de l'API", "43 démarches répertoriées, dont 31 couvertes" in texte and "10 sans source ouverte" in texte, texte[:400])
    verifier("L'administration compétente est indiquée", "Direction Générale des Impôts" in texte)
    verifier("Le statut de prototype est affiché", "Prototype" in texte and "ne remplace ni le texte officiel" in texte)
    photo("01_annuaire")
    audit_accessibilite("annuaire")

    champ_filtre = driver.find_element(By.CSS_SELECTOR, "input[type=search]")
    champ_filtre.send_keys("passe")
    time.sleep(0.3)
    verifier("Le filtre par nom réduit la liste", len(lignes()) == 1 and "Passeport" in lignes()[0].text, len(lignes()))
    champ_filtre.clear()
    champ_filtre.send_keys("identite")
    time.sleep(0.3)
    verifier("Le filtre ignore les accents", any("identité" in l.text for l in lignes()), len(lignes()))
    champ_filtre.clear()
    time.sleep(0.2)
    clic(next(b for b in boutons() if b.text.startswith("Sans source ouverte")))
    verifier("Le filtre des lacunes donne les 10 démarches sans source", len(lignes()) == 10, len(lignes()))
    clic(next(b for b in boutons() if b.text.startswith("Tous les domaines")))
    verifier("Tous les domaines ramène les 43 démarches", len(lignes()) == 43, len(lignes()))

    print("--- sources et données, sans consentement ---")
    clic(bouton("Sources"))
    attente.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "tbody tr")) == 44)
    texte = corps()
    verifier("La page Sources liste les 44 documents", "44 documents ouverts, découpés en 256 extraits : 248 vérifiés à la source, 8 à vérifier." in texte, texte[:400])
    liens = driver.find_elements(By.CSS_SELECTOR, "tbody a[href^='http']")
    verifier("Chaque document renvoie vers sa source", len(liens) == 44 and all(l.get_attribute("target") == "_blank" for l in liens), len(liens))
    photo("02_sources")
    audit_accessibilite("sources")

    print("--- consentement ---")
    clic(bouton("Assistant"))
    attente.until(lambda d: d.find_elements(By.CSS_SELECTOR, "dl"))
    champ = driver.find_element(By.CSS_SELECTOR, "input[type=text]")
    verifier("Saisie bloquée avant le consentement", not champ.is_enabled())
    verifier("Le champ explique pourquoi il est bloqué", "Acceptez" in (champ.get_attribute("placeholder") or ""))
    verifier("Bouton Envoyer bloqué avant le consentement", not driver.find_element(By.CSS_SELECTOR, "button[type=submit]").is_enabled())
    notice = driver.find_element(By.TAG_NAME, "dl").text
    verifier("La notice expose finalité, droits et limites", all(m in notice for m in ["Finalité", "Vos droits", "Limites", "intervention humaine", "Transfert à l'étranger"]), notice)
    verifier("Un refus est possible", any(b.text == "Refuser" for b in boutons()))
    photo("03_notice")
    audit_accessibilite("notice")
    clic(bouton("Refuser"))
    verifier("Refuser ramène à l'annuaire", len(lignes()) == 43 or "Démarches administratives" in corps())
    journal_avant = nombre_chat_journalises()
    clic(next(b for b in boutons() if b.text == "Patente"))
    time.sleep(0.5)
    verifier("Un clic sans accord met la demande en attente", "« Patente » sera traitée après votre accord" in corps(), corps()[:400])
    verifier("Aucune question n'est envoyée sans accord", nombre_chat_journalises() == journal_avant and not driver.find_elements(By.TAG_NAME, "article"))
    photo("04_demande_en_attente")
    clic(next(b for b in boutons() if "accepte" in b.text.lower()))
    attente.until(lambda d: d.find_elements(By.TAG_NAME, "article"))
    attendre_fin()
    verifier("Après l'accord, la demande en attente est traitée", "Patente" in fiche(), corps()[:400])

    print("--- fiche patente ---")
    texte = fiche()
    verifier("Toutes sources vérifiées : état vert mérité", "Sources vérifiées" in texte, texte[:300])
    verifier("Coût et durée sont présentés", "Procédure gratuite" in texte and "2 j à 7 j" in texte, texte[:600])
    verifier("Pas de doublon dans les pièces", texte.count("Déclaration des contributions des patentes et licences") == 1)
    verifier("Pas de marqueur de mise en forme brut", "**" not in corps())
    verifier("La liste « Textes et sources » n'est pas répétée dans la fiche", "Textes et sources" not in texte)
    verifier("Le rappel de responsabilité reste visible", "Vous restez responsable" in texte)
    photo("05_fiche_patente")
    audit_accessibilite("fiche")

    print("--- précision puis cas ---")
    clic(bouton("Effacer"))
    verifier("Effacer vide le fil et affiche les exemples", "Exemples de questions" in corps() and not driver.find_elements(By.TAG_NAME, "article"))
    photo("06_assistant_vide")
    poser("Je veux renouveler ma carte")
    options_btn = [b for b in boutons() if b.text in ("Carte nationale d'identité (CNI)", "Carte de séjour")]
    verifier("Une question vague propose un choix dans le fil", len(options_btn) == 2, corps()[-400:])
    verifier("Une question de précision n'ouvre pas de fiche", not driver.find_elements(By.TAG_NAME, "article"))
    photo("07_precision")
    clic(next(b for b in options_btn if "CNI" in b.text))
    attendre_fin()
    verifier("« Renouveler » puis CNI retient le cas du renouvellement", "Renouvellement d'une carte périmée" in fiche(), corps()[-300:])
    poser("Je veux une CNI")
    verifier("Sans indice, l'agent demande le cas", "De quel cas s'agit-il" in corps(), corps()[-300:])
    clic(next(b for b in reversed(boutons()) if b.text == "Perte, vol ou détérioration"))
    attendre_fin()
    texte = fiche()
    verifier("Le choix du cas donne la bonne pièce", "attestation de déclaration de perte" in texte.lower(), texte[:500])
    verifier("L'état ne prétend pas que tout est vérifié", "Sources en partie à vérifier" in texte, texte[:300])
    verifier("L'alerte sur les sources à vérifier est visible", "pas encore pu vérifier" in texte)
    verifier("Les onglets annoncent leur contenu", all(any(b.text.startswith(n) for b in driver.find_elements(By.CSS_SELECTOR, "[role=tab]")) for n in ["Démarche", "Sources (", "Contrôle (", "Formulaire"]))
    photo("08_fiche_cni")

    print("--- checklist des pièces ---")
    case = driver.find_elements(By.CSS_SELECTOR, "article input[type=checkbox]")[-1]
    verifier("Le compteur de pièces démarre à zéro", "0 sur 1 prête" in fiche(), fiche()[:500])
    clic(case)
    verifier("Cocher une pièce met à jour le compteur", "1 sur 1 prête" in fiche(), fiche()[:500])

    print("--- onglets ---")
    onglet("Sources")
    texte = fiche()
    verifier("Les sources affichent le statut de vérification", "À vérifier" in texte and "Vérifié" in texte)
    liens = driver.find_elements(By.CSS_SELECTOR, "article a[href^='http']")
    verifier("Chaque source renvoie vers son texte, dans un nouvel onglet", liens and all(l.get_attribute("target") == "_blank" for l in liens))
    photo("09_onglet_sources")
    audit_accessibilite("onglet sources")
    onglet("Contrôle")
    texte = fiche()
    verifier("Le verdict et la décision sont affichés", "Partiel" in texte and "Publiée avec réserve" in texte, texte[:500])
    verifier("Le mode de rédaction réel est affiché", "Extraits des sources" in texte, texte[:500])
    verifier("Les contrôles portent un nom lisible", "Intégrité des citations" in texte and "Fiabilité des sources" in texte and "integrite" not in texte)
    verifier("Les contrôles n'affichent ni liste brute ni identifiant interne", "['" not in texte and "procedure_idcam" not in texte and "IDCAM pour la Carte" in texte, texte[-500:])
    photo("10_onglet_controle")
    audit_accessibilite("onglet contrôle")
    onglet("Formulaire")
    texte = fiche()
    verifier("Le formulaire annonce que rien n'est soumis", "Rien n'est soumis" in texte)
    entrees = [e for e in driver.find_elements(By.CSS_SELECTOR, "article label input") if e.get_attribute("type") not in ("file", "checkbox")]
    verifier("Le formulaire commence vide : aucune valeur inventée", entrees and all(e.get_attribute("value") == "" for e in entrees))
    photo("11_onglet_formulaire")
    audit_accessibilite("onglet formulaire")
    onglet("Démarche")
    verifier("La case cochée reste cochée après un changement d'onglet ou se remet à zéro sans erreur", "sur 1 prête" in fiche())

    print("--- longue démarche ---")
    poser("Je veux un permis de construire")
    texte = fiche()
    sous_titres = [h.text for h in driver.find_elements(By.CSS_SELECTOR, "article h3")]
    verifier("Étapes et pièces sont groupées par fiche", sous_titres.count("Obtention du plan de masse et de situation") == 2, sous_titres)
    verifier("Le préfixe de la fiche n'est pas répété à chaque ligne", "Obtention du plan de masse et de situation : " not in texte)
    verifier("Le coût total est visible, son détail reste replié", "Le coût total de la procédure est estimé à CFA 41,900" in texte and "Détail (" in texte, texte[:400])
    verifier("Le détail du coût est masqué par défaut", "11,000 XAF pour la demande et les 10 plans" not in texte)
    verifier("La numérotation des étapes continue d'un groupe à l'autre", "22." in texte)
    haut = driver.execute_script("return document.querySelector('article').getBoundingClientRect().top")
    verifier("La nouvelle fiche s'ouvre depuis son début", haut < 200, haut)
    photo("12_fiche_permis")

    print("--- autres réponses ---")
    poser("Je veux obtenir mon permis de conduire")
    texte = fiche()
    verifier("Lacune annoncée sans inventer", "Lacune documentée" in texte and "plutôt que d'inventer" in texte, texte[:400])
    photo("13_fiche_lacune")
    poser("Comment faire un faux passeport ?")
    verifier("Demande illicite refusée", "Je ne peux pas aider" in corps())
    poser("Quel est le prix du pain au marché ?")
    verifier("Sujet hors périmètre signalé", "Je n'ai pas trouvé de démarche" in corps())
    photo("14_fil_complet")
    clic(next(b for b in reversed(boutons()) if b.text.startswith("Permis de construire")))
    verifier("Une fiche précédente se rouvre depuis le fil", "Permis de construire" in driver.find_element(By.CSS_SELECTOR, "article h1").text)

    print("--- anglais ---")
    clic(bouton("Effacer"))
    clic(bouton("EN"))
    attente.until(lambda d: d.find_element(By.CSS_SELECTOR, "input[type=text]").get_attribute("placeholder").startswith("Ask"))
    verifier("Le bouton EN traduit l'interface", driver.find_element(By.TAG_NAME, "html").get_attribute("lang") == "en")
    poser("I want to renew my passport")
    texte = fiche()
    verifier("Réponse en anglais", "You remain responsible" in texte, texte[-400:])
    verifier("Le compteur de pièces est en anglais", " ready" in texte)
    photo("15_fiche_anglais")
    clic(bouton("Procedures"))
    attente.until(lambda d: "National identity card (CNI)" in corps())
    verifier("L'annuaire passe en anglais", "Administrative procedures" in corps() and "Identity and civil status" in corps())
    photo("16_annuaire_anglais")

    print("--- retrait du consentement ---")
    clic(bouton("Your data"))
    verifier("La page des données indique l'accord donné", "Consent given" in corps())
    photo("17_vos_donnees")
    audit_accessibilite("vos données")
    clic(bouton("Withdraw my consent"))
    clic(bouton("Assistant"))
    attente.until(lambda d: not d.find_element(By.CSS_SELECTOR, "input[type=text]").is_enabled())
    verifier("Retirer son accord rebloque la saisie", True)
    verifier("Retirer son accord efface la conversation", "You remain responsible" not in corps() and not driver.find_elements(By.TAG_NAME, "article"))
    verifier("La notice est de nouveau présentée", "Your rights" in corps())

    print("--- requêtes externes ---")
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

    attente.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "tbody tr")) == 43)
    largeur = debord()
    verifier("360 px : pas de défilement horizontal, annuaire", largeur[0] <= largeur[1], largeur)
    verifier("360 px : le filtre de domaine devient une liste déroulante", driver.find_element(By.TAG_NAME, "select").is_displayed())
    photo_tel("18_tel_annuaire")
    clic(bouton("Assistant"))
    attente.until(lambda d: any("accepte" in b.text.lower() for b in d.find_elements(By.TAG_NAME, "button")))
    largeur = debord()
    verifier("360 px : pas de défilement horizontal, notice", largeur[0] <= largeur[1], largeur)
    photo_tel("19_tel_notice")
    clic(next(b for b in boutons() if "accepte" in b.text.lower()))
    time.sleep(0.5)
    poser("Je veux un permis de construire")
    time.sleep(0.5)
    largeur = debord()
    verifier("360 px : pas de défilement horizontal, longue fiche", largeur[0] <= largeur[1], largeur)
    verifier("360 px : la fiche est amenée à l'écran", driver.execute_script("return document.querySelector('article').getBoundingClientRect().top") < 300)
    photo_tel("20_tel_fiche")
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
