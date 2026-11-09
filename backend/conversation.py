"""Messages de conversation : salutations, remerciements, adieux, demandes d'aide et questions générales.

Ces messages ne portent sur aucune démarche précise. L'agent y répond directement, avec des exemples à
cliquer, au lieu d'annoncer « aucun texte ouvert ». La reconnaissance est déterministe (mots entiers, sans
accents, français et anglais) : elle ne s'applique que si aucune démarche n'a été détectée, et un message
qui contient un mot inconnu (« prix du pain ») n'est jamais pris pour de la conversation.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from textes_utils import normaliser

SALUTATIONS = set(
    "bonjour bonsoir salut salutations coucou allo hello hi hey hola yo hiya howdy bjr bsr slt wesh morning afternoon evening".split()
)
REMERCIEMENTS = set("merci mercii mercis remercie remercions remerciements thanks thank thx thankyou".split())
# Petits mots qui accompagnent un remerciement sans rien demander.
ACCOMPAGNEMENT_MERCI = set("beaucoup bien tres vraiment infiniment super cool parfait excellent genial nickel ok okay great lot much very so".split())
# « ça va ? », « how are you ? » : de la politesse, pas une demande.
POLITESSE = set("va vas vais allez ca forme tout monde whats up sup doing there everyone all team".split())
# « oui », « non », « d'accord » : un acquiescement, pas une demande.
ACQUIESCEMENTS = set("oui non ok okay accord daccord yes no super parfait cool bien entendu compris voila hmm euh ah oh bon ben alors".split())
GENERIQUES = set(
    "procedure procedures demarche demarches administratif administratifs administrative administratives "
    "administration formalite formalites services service papiers paperasse".split()
)
ADIEUX = re.compile(
    r"\bau revoir\b|\ba bientot\b|\ba la prochaine\b|\ba plus tard\b|^a plus$|\bbonne (journee|soiree|nuit|fin de journee)\b"
    r"|\bbye\b|\bgoodbye\b|\bsee you\b|\bciao\b|\bgood ?night\b|\bhave a (nice|good|great) day\b"
)
ETAT = re.compile(
    r"\b(comment )?(vas|va|allez) (tu|vous)\b|\bca va\b|\btu vas bien\b|\bvous allez bien\b|\bhow are you\b|\bhow r u\b|\bwhat s up\b|\bwhats up\b|\bsup\b|\ba la forme\b"
)
CREATEUR = re.compile(
    r"\bqui (t|vous) a (cree|fait|developpe|concu|programme|invente)\b|\bqui est (ton|votre) (createur|developpeur)\b|\b(ton|votre) (createur|developpeur)\b"
    r"|\bwho (made|created|built|developed|programmed) you\b|\bwho is your (creator|developer)\b"
)
IDENTITE = re.compile(
    r"\btu es (un|une) (robot|ia|humain|personne|vrai)\b|\bes tu (un|une) (robot|ia|humain|personne)\b|\b(robot|humain|intelligence artificielle)\b"
    r"|\btu parles?\b|\bparles tu\b|\bparlez vous\b|\bdo you speak\b|\bare you (a|an) (robot|bot|human|ai)\b|\bspeak (english|french)\b"
)
AIDE = re.compile(
    r"\b(que|qu|quoi) (peux|peut|pouvez|sais|sait|savez|fais|fait|faites|sers|sert|servez|proposes|proposez)\b"
    r"|\b(tu|vous|il) (peux|peut|pouvez|sais|sait|savez|fais|fait|faites|sers|sert|proposes|proposez)\b.*\b(quoi|faire|aider)\b"
    r"|\ba quoi (tu |vous |il |ca )?(sers|sert|servez)\b"
    r"|\bqui (es|etes|est) (tu|vous)\b|\b(tu es|vous etes|t es) qui\b|\bpresente(z)? (toi|vous)\b"
    r"|\bcomment (ca|cela|tu|vous|on|dois je|faut il|puis je) (marche|fonctionne|fonctionnes|fonctionnez|utiliser|utilise|t utiliser|vous utiliser)\b"
    r"|\b(aide|aider|aidez|help)\b|\bpar ou commencer\b"
    r"|\bcomment (tu t appelles|t appelles tu|vous appelez vous|vous vous appelez)\b|\bton nom\b|\bvotre nom\b|\byour name\b"
    r"|\bwhat (can|could|do) you (do|offer)\b|\bwho are you\b|\bwhat are you\b|\bhow (does|do) (this|it|you) work\b"
    r"|\bhow can you help\b|\bcan you help\b"
)
# Mots courants sans contenu : ils n'empêchent pas de reconnaître une conversation.
FILLERS = set(
    "je j tu t vous il elle on nous me m moi toi te se s en y le la les l un une des du de d au aux et ou mais donc "
    "que qu qui quoi dont a ai as avons avez ont est es sont suis etes etre avoir fais faire fait faites "
    "peux peut peuvent pouvez puis pourrais pourriez voudrais voulez veux souhaite souhaiterais aimerais savoir "
    "connais connaitre connaissez sais sait dis dire dites explique expliquer expliquez parle parler parlez donne "
    "donner donnez montre montrer montrez plus davantage encore aussi peu pas ne n cela ce c cet cette ces "
    "mon ma mes ton ta tes son sa ses notre votre nos vos leur leurs si il plait svp stp concerne concernant "
    "concernent sujet propos rapport infos info information informations renseignement renseignements detail details "
    "precision precisions general generale generalement exemple exemples pour par avec sans sur sous dans entre vers "
    "chez comme quel quelle quels quelles quand comment pourquoi combien ici voila voici alors deja tout toute tous "
    "toutes quelque quelques autre autres meme faut falloir existe existent disponible disponibles possible possibles "
    "oui non ok accord besoin sur "
    "i me my you your the an of to in on for and or is are am be can could would will do does did tell show explain "
    "give more about what which who how there any some please info want need like know let lets us it its that this "
    "these those with from at by yes no okay govia assistant bot".split()
)
MOTS_ANGLAIS = set(
    "hello hi hey thanks thank help what who you your can how tell me more about please bye goodbye procedures "
    "administrative the is are do does want need morning afternoon evening there everyone".split()
)
MOTS_FRANCAIS = set(
    "bonjour bonsoir salut merci aide que qui tu vous peux peut dire plus demarches administratives les des une un "
    "je veux est sont pour sur quelles quels comment".split()
)


@dataclass
class Sujet:
    nom: str  # salutation, etat, remerciement, au_revoir, aide, apercu, accord, identite, createur
    langue: str  # langue de la réponse : celle du message, à défaut celle de l'interface
    salutation: bool = False  # le message commence par une salutation
    repete: bool = False  # l'utilisateur a déjà salué dans cet échange


def langue_du_message(jetons: list[str], par_defaut: str) -> str:
    anglais = sum(j in MOTS_ANGLAIS for j in jetons)
    francais = sum(j in MOTS_FRANCAIS for j in jetons)
    if anglais > francais:
        return "EN"
    if francais > anglais:
        return "FR"
    return par_defaut


def contient_salutation(message: str) -> bool:
    return any(j in SALUTATIONS for j in normaliser(message).split()[:2])


def reconnaitre(message: str, langue: str = "FR", deja_salue: bool = False) -> Optional[Sujet]:
    """Sujet de conversation du message, ou None s'il contient autre chose que de la conversation."""
    texte = normaliser(message)
    jetons = texte.split()
    if len(jetons) > 16:
        return None
    reponse_en = langue_du_message(jetons, langue)
    salut = any(j in SALUTATIONS for j in jetons)

    def sujet(nom: str) -> Sujet:
        return Sujet(nom, reponse_en, salutation=salut, repete=deja_salue)

    reste = [j for j in jetons if j not in FILLERS]
    if ADIEUX.search(texte) and len([j for j in reste if j not in SALUTATIONS]) <= 4:
        return sujet("au_revoir")
    if any(j in REMERCIEMENTS for j in jetons) and not [j for j in reste if j not in REMERCIEMENTS | ACCOMPAGNEMENT_MERCI | SALUTATIONS]:
        return sujet("remerciement")
    if CREATEUR.search(texte) and len(jetons) <= 10:
        return sujet("createur")
    if ETAT.search(texte) and len([j for j in reste if j not in SALUTATIONS | POLITESSE]) == 0 and len(jetons) <= 7:
        return sujet("etat")
    if IDENTITE.search(texte) and len(jetons) <= 10:
        return sujet("identite")
    if AIDE.search(texte) and len(jetons) <= 12:
        # Les mots de la formule d'aide (« comment ça marche ») ne comptent pas comme un autre sujet.
        autres = [j for j in AIDE.sub(" ", texte).split() if j not in FILLERS | SALUTATIONS | GENERIQUES]
        if not autres:
            return sujet("aide")
    # « Salut mon ami », « Bonjour cher monsieur » : une salutation en tête d'un message très court, le reste est une formule d'adresse.
    if jetons and jetons[0] in SALUTATIONS and len(jetons) <= 5:
        return sujet("salutation")
    if jetons and all(j in ACQUIESCEMENTS or j in FILLERS for j in jetons) and any(j in ACQUIESCEMENTS for j in jetons) and len(jetons) <= 4:
        return sujet("accord")
    inconnus = [j for j in reste if j not in SALUTATIONS | POLITESSE | GENERIQUES]
    if inconnus:
        return None
    if any(j in GENERIQUES for j in jetons):
        return sujet("apercu")
    if salut or any(j in POLITESSE for j in jetons):
        return sujet("salutation")
    # Rien que des mots courants (« je veux savoir plus », « ?? ») : on demande quelle démarche.
    return sujet("apercu")
