---
title: "Étude de faisabilité technique et juridique"
subtitle: "GOVIA Cameroun — Agent intelligent d'assistance administrative et de conformité aux procédures publiques"
author: "Équipe GOVIA Cameroun"
date: "26 octobre 2026"
lang: fr
---

# GOVIA Cameroun — Étude de faisabilité technique et juridique

**Agent intelligent d'assistance administrative et de conformité aux procédures publiques**

---

## 1. Synthèse exécutive

GOVIA Cameroun est un **agent d'IA agentique bilingue (français / anglais)** qui assiste le citoyen dans ses démarches administratives : il identifie la procédure, vérifie les pièces requises, explique les étapes, **cite les textes officiels applicables** et propose de **pré-remplir le formulaire officiel** pour que le citoyen le valide et le soumette. Un **second agent (« auditeur de conformité »)** contrôle que chaque réponse et action de l'assistant est justifiée par un texte de la base de connaissances, et détecte les incohérences entre procédures et textes.

**Conclusion de faisabilité : OUI, réalisable — à condition de respecter quatre contraintes majeures.**

| Axe | Verdict | Conditions / risques majeurs |
|---|---|---|
| Faisabilité juridique | OK  Faisable | Respect de la **Loi n° 2024/017** (protection des données), consentement explicite, **pas de transfert transfrontalier non autorisé**, pas de traitement de données biométriques, responsabilité gardée par le citoyen. |
| Faisabilité technique | OK  Faisable | Part de zéro, pile **gratuite / low-cost** (LLM local ou API à tarification dégressive + RAG local), OCR local, base de connaissances ouverte. |
| Conformité hackathon | OK  Respectable | Deux parties obligatoires remplies (technique + réglementaire), pipeline **Y.3172** cartographié, base RAG ouverte, **analyse d'écarts** produite, politiques **réelles et ouvertes**, données de cas d'usage **synthétiques**. |
| Calendrier | ATTENTION  Urgent | Délai **10 novembre 2026**. Plan en 3 phases ciblé sur un MVP solide + démo. |

**Recommandations clés :**
1. Adopter le **modèle local (Ollama + Mistral/Qwen)** pour la conformité data ; utiliser une **API cloud (Groq/DeepSeek)** avec **anonymisation stricte** uniquement pour la démo rapide.
2. **Ne pas inventer de politiques.** Documenter chaque lacune (gap) — c'est la partie la plus valorisée du hackathon.
3. La **CNI n'est qu'un exemple** : construire une base de connaissances **multi-démarches** (passeport, état civil, nationalité, contrat de travail, NIU, carte grise, etc.).
4. Faire du **mapping Y.3172 détaillé** et de la **comparaison version A (sans gouvernance) vs version B (gouvernée)** les piliers de la démo.

---

## 2. Contexte, objectifs et contraintes du hackathon

### 2.1 Le hackathon ITU « AI for Good Lab » (UAE)

Activité crowdsourcée ouverte à tous (étudiants, chercheurs, professionnels, startups). Objectif : construire, par pays, une **base de connaissances ouverte** et des **agents d'IA (agentic AI)** pour étudier comment le comportement des agents change selon les politiques appliquées.

**Deux parties obligatoires (les deux requises pour concourir, **soumises avant le 10 novembre**) :**
- **Partie 1 — Solution technique** : **le système fonctionnel** (agent + RAG + auditeur + démo). Le système **cite les textes** dans ses réponses et **vérifie** sa conformité en interne. C'est le produit.
- **Partie 2 — Ancrage réglementaire** : **le dossier** qui trace, étape par étape du pipeline Y.3172, **quel texte réel gouverne l'action**, et l'**analyse d'écarts** (où les textes manquent). C'est la justification documentaire.

> **À noter :** Partie 1 **contient** des justifications (le système cite les textes en pratique), Partie 2 **formalise** cette justification pour les juges. La distinction est **fonction (P1) vs dossier (P2)**, pas « avec/sans justification ».

**Ce qui est évalué :**
- **Mapping détaillé sur le pipeline ITU-T Y.3172** (critère le plus valorisé).
- **Analyse d'écarts (gap analysis)** — partie la plus valorisée.
- **Base de connaissances / RAG** (partie intégrante de la solution).
- Mapping aux **dimensions de l'AI Readiness Report**.
- Bonus : comparer **version A (sans gouvernance) vs version B (gouvernée)** ; comparer une lacune du pays avec la réglementation d'un autre pays.

**Ce qui n'est PAS évalué :**
- **L'exactitude du modèle (accuracy)** n'est pas un critère.
- **La valeur business / commerciale** n'est pas un critère. Un pitch deck sans prototype fonctionnel est écarté.

### 2.2 Contraintes et règles de conformité (à respecter scrupuleusement)

| Règle | Implication pour GOVIA |
|---|---|
| Interdiction formelle d'utiliser des informations confidentielles (accès restreint) | Seules les **sources publiées et ouvertes** sont admises. Pas d'accès à des systèmes IDCAM/DGI internes. |
| **Ne pas inventer de politiques** | En l'absence de document applicable, **documenter la lacune (gap)** — valorisé, pas pénalisé. |
| Données du cas d'usage peuvent être générées/augmentées/simulées/synthétiques | Le scénario citoyen, les pièces, les formulaires sont **synthétiques** pour la démo. |
| Les documents de politique doivent être **réels — jamais fictifs** | La base de connaissances cite des textes réels (décrets, lois) avec références. |
| Modèles propriétaires / non open source autorisés | Seule la **base de connaissances doit être ouverte** (le code peut rester privé). |
| Base de connaissances : découpée en chunks machine-readable, embarquée dans la solution (RAG) pour traçabilité | Chaque décision de l'agent doit être **justifiable par une politique**. |
| Taille modeste attendue (~30 politiques ou moins) | Suffisant si les politiques gouvernent réellement chaque étape du pipeline. |
| Code source peut rester privé ; la base de connaissances doit rester ouverte | Livraison : rapport (5 pages max), dépôt GitHub, base de connaissances, vidéo démo (7 min max). |
| Composition d'équipe : max 4 (4 participants ou 3 + 1 mentor) | À vérifier pour l'inscription. |
| Date critique : **10 novembre 2026** (soumission complète) | Plan d'action pragmatique (§7). |

### 2.3 Pipeline ITU-T Y.3172 — élément central

Structure attendue : un **bloc intent** (le prompt) → un **orchestrateur** → le pipeline lui-même, dupliqué en deux instances identiques : un **sandbox** (test/validation) et l'**environnement réseau de production**.

| Nœud | Signification | Ce qu'il faut décrire |
|---|---|---|
| **SRC** | Source de données | Nature des données, métadonnées, technologie de collecte, emplacement, fréquence/durée, configuration. |
| **C** | Collecteur | Comment les données sont agrégées : plateforme edge, transmission réseau, cloud cœur ou edge. |
| **PP** | Pré-traitement | Nettoyage, gestion multimodal, standardisation des formats, **dé-identification/anonymisation**, traitement des valeurs nulles. |
| **M** | Modèle | Type (régression, détection d'anomalie, vision, audio, multimodal…), hébergement, paramètres, fonction. |
| **P** | **Politique** | À chaque étape, la **politique nationale applicable** : loi de protection des données, niveau d'anonymisation requis, etc. |
| **D** | Distributeur | Comment la sortie du modèle est acheminée vers sa cible, identification de la cible. |
| **SINK** | Cible | Ce qui exécute le résultat (application, actionneur, plateforme d'analyse…). |

---

## 3. Description du cas d'usage et concept de solution

### 3.1 Problème

Le citoyen ne maîtrise pas la procédure exacte d'une démarche administrative (ex. renouvellement de CNI), ignore les **pièces exigibles**, et les dossiers incomplets ou incorrects coûtent temps, argent et refus. L'information administrative est **dispersée en silos** (IDCAM, PassCam, DGI, SID, mairies…) et peu accessible.

### 3.2 Solution — GÉNÉRALISTE (la CNI n'est qu'un exemple)

> ATTENTION  **Clarification importante :** la procédure CNI illustrée dans le scénario initial est **un exemple parmi beaucoup d'autres**. GOVIA couvre **le maximum de démarches administratives possibles** (voir §6).

**GOVIA** est un agent bilingue (FR/EN) qui, à partir de la question du citoyen :
1. **Identifie** la procédure administrative concernée.
2. **Vérifie les pièces requises** (selon la démarche).
3. **Explique les étapes** de la procédure.
4. **Cite les textes officiels applicables** (décret, loi, arrêté) avec référence précise.
5. Propose de **pré-remplir le formulaire officiel** ; le citoyen **valide et soumet**.

### 3.3 Architecture en deux agents

| Agent | Rôle |
|---|---|
| **GOVIA-Assistant** | Dialogue avec le citoyen ; identifie la démarche ; vérifie les pièces ; explique les étapes ; cite les textes ; pré-remplit le formulaire. |
| **GOVIA-Auditeur (conformité)** | Contrôle que chaque réponse et action de l'assistant est **justifiée par un texte de la base de connaissances** ; détecte les incohérences ; bloque/signale si une action n'est pas couverte par un texte. |

Cette architecture est directement inspirée du thème : « Un second agent peut contrôler si les réponses respectent les règles publiées. »

### 3.4 Autonomie choisie : **pré-remplissage** (citoyen valide et soumet)

L'agent **pré-remplit** le formulaire mais **ne soumet pas** à la place du citoyen. Le citoyen garde la maîtrise et la responsabilité de la soumission. Cela limite fortement le risque juridique (§4) et respecte la règle du hackathon (le citoyen valide).

---

## 4. Faisabilité juridique

### 4.1 Socle juridique camerounais — réel et ouvert

Tous les textes ci-dessous sont **réels, publics et ouverts** — ils constituent le cœur de la base de connaissances (Partie 2 du hackathon).

| Instrument | Référence | Pertinence pour GOVIA | Statut |
|---|---|---|---|
| Décret n° 2016/375 du 04 août 2016 | CNI — caractéristiques & modalités de délivrance (art. 5 obligation ; art. 11 pièces) | Texte principal du scénario de référence CNI | OK  Ouvert |
| Décret n° 2021/347 du 17 juin 2021 | Passeports biométriques — conditions d'établissement | Démarche passeport | OK  Ouvert |
| Ordonnance n° 81/02 du 29 juin 1981 | Organisation de l'état civil (naissance, mariage, décès) | Actes d'état civil | OK  Ouvert |
| Loi n° 2011/011 du 06 mai 2011 | Délais de déclaration des actes d'état civil | Délais naissance/décès | OK  Ouvert |
| Code civil camerounais | État des personnes (art. 34, 49, 76, 78, 79) | Actes d'état civil | OK  Ouvert |
| Loi n° 1968-LF-3 du 11 juin 1968 | Code de la nationalité camerounaise (art. 42 certificat) | Certificat de nationalité | OK  Ouvert |
| Décret n° 68-DF-478 du 16 déc. 1968 | Modalités d'application du Code de la nationalité | Certificat de nationalité | OK  Ouvert |
| Loi n° 92-007 du 14 août 1992 | Code du travail (art. 23, 25 contrat CDI/CDD) | Contrat de travail | OK  Ouvert |
| **Loi n° 2024/017 du 23 déc. 2024** | **Protection des données à caractère personnel** | Consentement, DPIA, **transferts transfrontaliers (art. 32)**, données sensibles (art. 33), sanctions | OK  Ouvert |
| Loi n° 2010/012 du 21 déc. 2010 | Cybersécurité et cybercriminalité (signature électronique, ANTIC) | Signature électronique, sécurité | OK  Ouvert |
| Loi n° 2010/021 du 21 déc. 2010 | Commerce électronique | Documents/signatures électroniques | OK  Ouvert |
| Loi n° 2010/013 du 21 déc. 2010 | Communications électroniques (modifiée par 2015/006) | Contexte télécoms | OK  Ouvert |
| OHADA — Acte Uniforme AUDCG | Signature électronique (effet supranational) | Validité signature électronique | OK  Ouvert |
| Décret n° 79/341 du 03 sept. 1979 | Immatriculation des véhicules (carte grise) | Carte grise | OK  Ouvert |
| Décret n° 2020/PM du 01 juin 2020 | Documents de transport sécurisés (cartes grises) | Carte grise moderne | OK  Ouvert |
| Décret n° 2016/373 du 04 août 2016 | Entrée, séjour et sortie des étrangers (loi 97/012) | Carte de séjour / étrangers | OK  Ouvert |
| Procédure IDCAM (DGSN) | idcam.cm, 17 février 2025 — pré-enrôlement CNI | Procédure CNI réelle | OK  Ouvert |
| Procédure PassCam (DGSN) | passcam.cm, 2024 — pré-enrôlement passeport | Procédure passeport réelle | OK  Ouvert |
| FGI 2026 / E-Gov'A 2026 | DPI, interopérabilité, identité numérique | Contexte stratégique | OK  Ouvert |

### 4.2 Analyse par enjeu

#### a) Protection des données personnelles — **Loi n° 2024/017 du 23 décembre 2024**

La Loi n° 2024/017 est **l'instrument le plus contraignant** pour GOVIA. Points clés :

- **Consentement** : tout traitement de données personnelles requiert un consentement **clair, distinct, explicite** du citoyen. GOVIA doit recueillir ce consentement avant de traiter les pièces et avant le pré-remplissage.
- **Minimisation et finalité** : ne traiter que les données nécessaires à la démarche demandée.
- **Données sensibles (art. 33)** : les données biométriques (empreintes, photo d'identité biométrique) sont **interdites de traitement sauf autorisation**. **GOVIA ne doit pas traiter les données biométriques** — uniquement les pièces justificatives administratives (acte de naissance, certificat de nationalité, etc.). La capture biométrique reste exclusivement du ressort de l'administration (DGSN).
- **DPIA** : un traitement à haut risque (massification de données administratives) requiert une **analyse d'impact relative à la protection des données**.
- **Transferts transfrontaliers (art. 32)** : tout transfert de données personnelles **hors du Cameroun** requiert une **autorisation préalable de l'Autorité de protection des données**. Un LLM cloud étranger (OpenAI, Groq, Mistral USA/EU) implique un transfert → soit autorisation, soit **traitement local**, soit **anonymisation/désidentification avant envoi**.
- **Responsabilité conjointe** : le donneur et le destinataire sont **solidairement responsables** en cas de transfert illicite.
- **Sanctions** : amendes de 1 à 1 000 millions FCFA selon le manquement ; peines d'emprisonnement jusqu'à 10 ans pour transferts illégaux. Période transitoire **expirée le 23 juin 2026** → la loi est pleinement applicable.

#### b) Identité, état civil et titres — décrets et ordonnances

- **CNI (décret 2016/375)** : la possession est obligatoire dès 18 ans ; les pièces exigent un certificat de nationalité, un acte de naissance, etc. (art. 11). Le pré-enrôlement IDCAM est la procédure réelle. GOVIA cite ces exigences textuelles.
- **État civil (ordonnance 81/02, loi 2011/011)** : actes de naissance, mariage, décès ; délais de déclaration (naissance 60 jours, décès 90 jours). Jugement supplétif pour naissance non déclarée à temps (art. 33).
- **Nationalité (loi 1968-LF-3)** : certificat de nationalité délivré par le tribunal (art. 42), pièce clé de la première CNI.

#### c) Transactions électroniques et signature — validité du pré-remplissage

- **Loi n° 2010/012 (cybersécurité)** et **Loi n° 2010/021 (commerce électronique)** : la **signature électronique avancée** a **la même valeur juridique** que la signature manuscrite (art. 17). **OHADA AUDCG** : la signature électronique ne peut être refusée au seul motif de sa forme électronique.
- **Implication pour GOVIA** : le pré-remplissage du formulaire par l'agent + **validation/signature électronique du citoyen** est juridiquement solide. L'agent ne signe pas ; le citoyen valide et signe. Cela sécurise la conformité.

#### d) Cybersécurité et responsabilité

- L'agent est un **intermédiaire technique non délégué** de l'administration. En cas d'erreur de pré-remplissage, **le citoyen reste responsable** des informations qu'il valide et soumet. GOVIA doit afficher cette limitation clairement.
- La **responsabilité de l'agent IA tiers** dans les démarches administratives camerounaises n'a **pas de cadre explicite** → **lacune réglementaire à documenter** (voir §4.3).

#### e) Interopérabilité et DPI — contexte stratégique

- Le Cameroun promeut les **Infrastructures Publiques Numériques (DPI)** : identité numérique, paiements, échanges sécurisés de données, registres de référence (FGI 2026, E-Gov'A 2026). Le ministère de la Fonction publique (AIGLES) recense 400+ processus, 9 250 règles de gestion.
- **Implication** : GOVIA s'inscrit dans la volonté d'interopérabilité, mais les systèmes restent en silos (IDCAM, PassCam, DGI, SID séparés) → **gap** à documenter.

### 4.3 Analyse d'écarts juridiques (GAP ANALYSIS) — **partie la plus valorisée**

| # | Écart (gap) identifié | Conséquence | Mitigation / recommandation |
|---|---|---|---|
| 1 | **Pas d'API publique officielle** pour IDCAM / PassCam | L'agent **ne peut pas soumettre** directement ; le pré-remplissage est une **reconstitution/simulation**. | Documenter le gap ; positionner GOVIA comme assistant de pré-remplissage + validation citoyenne. Ne pas simuler une soumission réelle. |
| 2 | **Absence de cadre explicite** pour la responsabilité d'un agent IA tiers dans les démarches administratives | En cas d'erreur, répartition de la responsabilité incertaine. | Afficher que le citoyen reste responsable ; ajouter une clause de non-responsabilité ; proposer un « carnet d'audit » traçable. |
| 3 | **Transfert transfrontalier des données** (art. 32, Loi 2024/017) | Un LLM cloud étranger transfère des données hors du Cameroun → **illégal sans autorisation**. | Utiliser un **modèle local** (Ollama) pour la conformité ; ou anonymiser/désidentifier avant envoi cloud ; ou obtenir l'autorisation de l'Autorité. |
| 4 | **Données biométriques** (art. 33) | Empreintes / photo biométrique = données sensibles interdites de traitement sauf autorisation. | **Exclure toute capture/traitement biométrique** de GOVIA. Laisser la capture à l'administration (DGSN). |
| 5 | **Absence de texte d'application** de la Loi 2024/017 (décret / lignes directrices de l'Autorité) | Applicabilité partielle ; incertitude sur les DPIA et autorisations. | Documenter le gap ; se conformer aux principes généraux (consentement, minimisation, sécurité). |
| 6 | **Absence de cadre spécifique aux agents IA / IA générative dans les services publics** | Pas de règles de classement, de surveillance, d'audit des agents. | Documenter le gap (forte valeur). Comparer avec l'UE (AI Act) et l'Afrique du Sud (POPIA) / Maroc (loi 09-08) — **bonus**. |
| 7 | **Fragmentation / silos administratifs** (IDCAM, PassCam, DGI, SID séparés) | Pas d'échange de données structuré ; l'agent doit interroger plusieurs sources. | Documenter le gap (aligné sur FGI 2026 « de la fragmentation à l'interopérabilité ») ; proposer une base de connaissances unifiée. |
| 8 | **Consentement** explicite requis | L'agent doit recueillir un consentement clair et distinct. | Implémenter un consentement dédié avant traitement et pré-remplissage. |

**Comparaison avec un autre pays (bonus) :** le Cameroun n'a **pas de cadre équivalent à l'AI Act de l'UE** (règles par catégorie de risque, obligations pour systèmes à haut risque, surveillance humaine) ni de loi sur l'IA générative. L'**Afrique du Sud (POPIA)** et le **Maroc (loi 09-08, CNDP)** ont des régimes de transfert transfrontalier plus développés. **Gap de normalisation** à soumettre à l'ITU.

### 4.4 Matrice risque / conformité

| Risque | Niveau | Mesure de mitigation |
|---|---|---|
| Transfert transfrontalier illégal des données | **Élevé** | Modèle local (Ollama) ; ou anonymisation avant envoi cloud ; ou autorisation de l'Autorité. |
| Traitement de données biométriques | **Élevé** | Exclure toute donnée biométrique de GOVIA. |
| Consentement absent | **Moyen** | Implémenter un consentement explicite avant traitement/pré-remplissage. |
| Hallucination / conseil non fondé | **Moyen** | RAG obligatoire ; l'auditeur bloque si pas de texte ; le citoyen valide. |
| Responsabilité en cas d'erreur | **Moyen** | Citoyen responsable ; clause de non-responsabilité ; journal d'audit. |
| Utilisation de données confidentielles | **Élevé** | Seules des sources ouvertes et réelles ; données de cas d'usage synthétiques. |

---

## 5. Faisabilité technique

### 5.1 Architecture proposée

```
[Citoyen] --prompt bilingue--> [Intent / orchestrateur]
                                     |
            +------------------------+------------------------+
            |                                                |
      [GOVIA-Assistant]                              [GOVIA-Auditeur]
         |  RAG sur base politiques                    | vérifie chaque
         |  extraction intent + requêtage              | réponse/action vs textes
         |  génération réponse + pré-remplissage        | blocage si gap
         |  journal d'audit                              |
      [Formulaire pré-rempli] --validation citoyenne--> [SINK : soumission citoyenne]
```

### 5.2 Mapping ITU-T Y.3172 détaillé (esquisse)

| Nœud | Rôle dans GOVIA | Description détaillée |
|---|---|---|
| **SRC** | Source de données | 1) Prompt du citoyen (texte, FR/EN) ; 2) pièces uploadées (images de documents : acte de naissance, certificat, CNI…) ; 3) **base de politiques ouvertes et réelles** (décrets, lois, procédures). Métadonnées : source, date de publication, autorité, URL. |
| **C** | Collecteur | Collecte de la conversation ; OCR des pièces (Tesseract local ou vision LLM cloud avec anonymisation) ; récupération des politiques pertinentes via indexation. |
| **PP** | Pré-traitement | Nettoyage du texte ; **détection de langue (FR/EN)** ; **anonymisation / désidentification** des données personnelles avant ingestion dans le modèle (masquage des noms, dates, numéros) ; normalisation des formats (PDF, image, Word). |
| **M** | Modèle | LLM (multimodal si OCR de pièces) + **RAG** sur la base politiques ; extraction d'intention (identifier la démarche) + requêtage des textes applicables ; génération de réponse + pré-remplissage du formulaire. Hébergement : local (Ollama) ou cloud (Groq/DeepSeek) — voir §5.3. |
| **P** | **Politique** | À chaque étape, la politique applicable : **Loi 2024/017** (protection des données, anonymisation, consentement) ; **décret 2016/375** (CNI, pièces) ; **ordonnance 81/02** (état civil) ; **loi 92-007** (contrat) ; etc. L'agent cite la référence. |
| **D** | Distributeur | La sortie (réponse + formulaire pré-rempli + rapport de conformité) est acheminée au citoyen via l'interface ; le formulaire est présenté pour validation. |
| **SINK** | Cible | Le **citoyen** qui valide et soumet le formulaire ; et l'**auditeur de conformité** qui reçoit le rapport d'audit. |

### 5.3 Modèles : analyse cloud vs local (comme demandé)

| Critère | **Cloud** (Groq, DeepSeek, OpenAI, Mistral API) | **Local** (Ollama + Mistral/Qwen/Llama) |
|---|---|---|
| **Coût** | OK  Tarification dégressive ; Groq/DeepSeek très abordables ; tier gratuit pour démo | OK  Gratuit après téléchargement des modèles |
| **Conformité (Loi 2024/017 art. 32)** | NON  Transfert transfrontalier des données → autorisation requise ou anonymisation stricte | OK  **Aucune donnée ne sort du Cameroun** — conformité native |
| **Qualité linguistique (FR/EN)** | OK  Très bonne ; modèles multilingues performants | OK  Bonne ; Mistral 7B / Qwen2.5 multilingues acceptables |
| **OCR / multimodal** | OK  Vision LLM cloud performant | ATTENTION  Possible (modèle de vision local) ou Tesseract local |
| **Matériel** | OK  Aucun GPU local nécessaire | ATTENTION  Besoin de 8–16 GB RAM ; fonctionne sur CPU |
| **Souveraineté / autonomie** | NON  Dépendance réseau + fournisseur | OK  Souveraineté des données |
| **Latence** | OK  Rapide | ATTENTION  Légèrement plus lent (sans GPU) |
| **Recommandation** | Démo rapide **avec anonymisation stricte** | Version conformité recommandée |

**Recommandation :**
- **Prototype / démo rapide** : **cloud (Groq ou DeepSeek API)** avec **anonymisation/désidentification obligatoire avant envoi** et **pas de données personnelles brutes**. Cela permet un déploiement rapide sans matériel.
- **Version conforme (production)** : **modèle local (Ollama + Mistral 7B / Qwen2.5)**. Aucune donnée ne sort du Cameroun → respect de l'art. 32 de la Loi 2024/017. Pour l'OCR, utiliser **Tesseract local** ou un modèle de vision local.

### 5.4 Base de connaissances — RAG / graphe, machine-readable, ouverte

- **Format** : chunks **machine-readable** (JSON/JSONL) découpés **par article/section** de chaque texte.
- **Structure** : chaque chunk = `{id, texte_civil, texte_officiel, source, URL, autorité, date, procedure, etape, tags}`.
- **Moteur** : **RAG vectoriel** (ChromaDB local + embeddings) + requêtage par similarité ; option **graphe de connaissances** (politique → démarche → étape → pièce) pour la traçabilité.
- **Traçabilité** : chaque réponse de l'assistant doit citer les chunks utilisés → **journal d'audit**.
- **Ouverture** : la base est **ouverte** (GitHub), versionnée, extensible à d'autres démarches.
- **Taille** : ~20–30 politiques suffisent pour couvrir les démarches du catalogue (§6).

### 5.5 Comparaison version A (sans gouvernance) vs version B (gouvernée) — bonus majeur

| | Version A (sans gouvernance) | Version B (gouvernée par les politiques) |
|---|---|---|
| Requêtage de la base | Non systématique | **Obligatoire** ; chaque réponse citée |
| Traçabilité | Aucune | **Journal d'audit** + références aux textes |
| Hallucination | Risque élevé ; réponse non fondée | Bloquée par l'auditeur si pas de texte |
| Incohérences | Non détectées | **Détectées et signalées** par l'auditeur |
| Responsabilité | Incertaine | Citoyen responsable + consentement + audit |
| Démo | Réponse rapide mais potentiellement erronée | Réponse fondée, citable, vérifiée |

**Scénario de démo :** poser une question ambiguë (ex. « Je veux renouveler ma carte » sans préciser) → Version A donne une réponse directe (potentiellement fausse) ; Version B demande clarification + identifie les démarches possibles (CNI, carte grise, carte de séjour) + cite les textes + l'auditeur signale l'ambiguïté.

### 5.6 Stack recommandée (gratuite / low-cost, partir de zéro)

| Composant | Recommandation |
|---|---|
| Langage | Python 3.10+ |
| LLM | **Ollama + Mistral 7B / Qwen2.5** (conformité) ; ou **Groq/DeepSeek API** (démo avec anonymisation) |
| RAG | **ChromaDB** (vectoriel local) + embeddings (HuggingFace all-MiniLM ou local) ; option **FAISS** |
| OCR | **Tesseract** (local) ou vision LLM cloud (avec anonymisation) |
| Chunking | Découpage par article/section → JSON/JSONL |
| Orchestration | **LangChain / LlamaIndex** (ou simplicité : module custom) |
| API / interface | **FastAPI** (backend) + **Next.js / React + Tailwind + next-intl** (frontend FR/EN) |
| Base de connaissances | JSON/JSONL + RAG, **ouverte**, versionnée sur GitHub |
| Conteneurisation | Docker |
| Suivi / audit | Journal d'audit en JSON |

### 5.7 Faisabilité et risques techniques

- **Partir de zéro** : le MVP est réalisable en ~1 semaine avec une pile simple (LLM + ChromaDB + Next.js + FastAPI).
- **Multilinguisme FR/EN** : les modèles modernes (Mistral, Qwen, Groq) gèrent bien le mix FR/EN ; test requis.
- **OCR des pièces** : Tesseract local gère les documents imprimés ; prévoir un étalonnage sur des pièces camerounaises.
- **Pré-remplissage du formulaire** : reconstitution du formulaire IDCAM/PassCam **sans API réelle** → simulation de pré-remplissage (gap documenté).
- **Scalabilité** : la base RAG est extensible à d'autres démarches (dimension cross-domain de l'AI Readiness).

---

## 6. Catalogue des démarches administratives camerounaises (section dédiée)

Recherche des démarches + leurs **textes réels et ouverts**. Statuts : OK  = texte ouvert identifié ; ATTENTION  = texte partiellement ouvert / gap.

| # | Démarche | Autorité compétente | Texte réel (référence) | Pièces clés | Statut |
|---|---|---|---|---|---|
| 1 | **CNI (renouvellement)** — scénario de référence | DGSN (idcam.cm) | Décret n° 2016/375 du 04 août 2016 (art. 5, 11) | Ancienne CNI, acte de naissance, certificat de nationalité, acte de mariage (femmes), justificatif de profession | OK  |
| 2 | **Passeport biométrique** | DGSN (passcam.cm) | Décret n° 2021/347 du 17 juin 2021 | Acte de naissance, certificat de nationalité, CNI, jugement supplétif | OK  |
| 3 | **Acte de naissance** | Officier d'état civil (mairie) | Ordonnance n° 81/02 du 29 juin 1981 ; Loi n° 2011/011 du 06 mai 2011 | Déclaration ; jugement supplétif si tardif (art. 33) | OK  |
| 4 | **Acte de mariage** | Officier d'état civil | Ordonnance n° 81/02 (art. 48, 49) ; Code civil (art. 76) | Acte de naissance, consentement, témoins | OK  |
| 5 | **Acte de décès** | Officier d'état civil | Ordonnance n° 81/02 (art. 78, 79) | Déclaration dans les 90 jours | OK  |
| 6 | **Certificat de nationalité** | Tribunal de première instance | Loi n° 1968-LF-3 du 11 juin 1968 (art. 42) ; Décret n° 68-DF-478 | Acte de naissance, preuve de filiation | OK  |
| 7 | **Contrat de travail (CDI/CDD)** | Employeur / MINTSS | Loi n° 92-007 du 14 août 1992 Code du travail (art. 23, 25) | Offert d'emploi, bulletin de paie, etc. | OK  |
| 8 | **Immatriculation fiscale / NIU / attestation d'immatriculation** | DGI (impots.cm, teledeclaration-dgi.cm) | Loi de finances 2020 (art. L.1 bis) — NIU obligatoire | Identité, activité, adresse | OK  |
| 9 | **Carte grise / immatriculation véhicule** | Ministère des Transports (SID) | Décret n° 79/341 du 03 sept. 1979 ; Décret n° 2020/PM du 01 juin 2020 | Carte d'identité, facture d'achat, certificat de dédouanement (Portrans.cm) | OK  |
| 10 | **Carnet de famille** | Officier d'état civil | Ordonnance n° 81/02 | Acte de mariage, actes de naissance des enfants | OK  |
| 11 | **Jugement supplétif d'acte de naissance** | Tribunal | Ordonnance n° 81/02 (art. 23, 24, 33) | Preuve de la naissance tardive | OK  |
| 12 | **Carte de séjour / autorisation de séjour** | DGSN | Décret n° 2016/373 du 04 août 2016 (loi 97/012) | Passeport, justificatif de séjour, moyens d'existence | OK  |
| 13 | **Légalisation de documents** | Ministère des Affaires Étrangères (MAE) | Circulaire / pratique diplomatique | Document à légaliser, identité | ATTENTION  Texte peu accessible |
| 14 | **Certificat de résidence / attestation d'hébergement** | Mairie / chef de quartier | Règlement local | Preuve de domicile | ATTENTION  Pas de texte national clair ouvert |
| 15 | **Diplôme / équivalence** | Ministère de l'Éducation | Texte à identifier | Certificat, relevés de notes | ATTENTION  Texte à identifier |

**Gap global** : les démarches ATTENTION  (légalisation, attestation de résidence, équivalence) illustrent l'**absence de textes ouverts accessibles** pour certaines procédures → **à documenter comme gaps** (valué, pas pénalisé).

---

## 7. Plan d'action & calendrier (urgent — jusqu'au 10 novembre)

**Profil** : équipe technique, part de zéro, compétences de dev, calendrier urgent.

### Phase 1 — Fondations (J0–J3, ~26–29 oct.)
- [ ] Finaliser le concept et l'architecture (2 agents).
- [ ] **Constituer la base de connaissances** (textes réels du §6, découpés en chunks JSON).
- [ ] Squelette du code : Next.js (React) + FastAPI + Docker Compose.
- [ ] Décision cloud vs local (démo cloud avec anonymisation ; version conforme local).

### Phase 2 — MVP (J4–J7, ~30 oct.–2 nov.)
- [ ] **GOVIA-Assistant** : RAG + extraction d'intention + génération + pré-remplissage.
- [ ] **GOVIA-Auditeur** : vérification des réponses vs textes, journal d'audit.
- [ ] OCR des pièces (Tesseract).
- [ ] Consentement explicite du citoyen.

### Phase 3 — Livrables (J8–J10, ~3–10 nov.)
- [ ] **Démo** (vidéo ≤ 7 min : version A vs B).
- [ ] **Rapport technique** (5 pages max, template ITU).
- [ ] **Dépôt GitHub** (code + base de connaissances ouverte).
- [ ] **Mapping Y.3172** détaillé + **analyse d'écarts**.

### Risques & mitigation
| Risque | Mitigation |
|---|---|
| Temps trop court | Prioriser le MVP (2 démarches : CNI + passeport) ; compléter après. |
| API cloud indisponible / coût | Modèle local (Ollama) dès le départ. |
| Qualité FR/EN | Tests d'étalonnage ; écrémer les modèles. |
| Base de connaissances incomplète | Documenter les gaps ; ne pas inventer. |

---

## 8. Livrables & conformité au hackathon — checklist

| Livrable / règle | Statut |
|---|---|
| Partie 1 — Solution technique (système fonctionnel : agent + RAG + auditeur + démo) | OK  Prévue |
| Partie 2 — Ancrage réglementaire (dossier : mapping Y.3172 + analyse d'écarts) | OK  Prévue (§4.1) |
| **Date limite : les deux parties soumises avant le 10 novembre 2026** | ⚠️ Plan urgent (§7) |
| Mapping ITU-T Y.3172 détaillé | OK  (§5.2 + annexe) |
| Base de connaissances RAG ouverte & machine-readable | OK  (§5.4) |
| Analyse d'écarts (gap analysis) | OK  (§4.3, §6) |
| Comparaison version A vs B | OK  (§5.5) |
| Politiques réelles et ouvertes (pas inventées) | OK  |
| Données de cas d'usage synthétiques | OK  |
| Rapport technique ≤ 5 pages | OK  (à produire) |
| Vidéo démo ≤ 7 min | OK  (à produire) |
| Dépôt GitHub | OK  (à produire) |
| Aucune information confidentielle | OK  |
| Équipe ≤ 4 personnes | ATTENTION  À confirmer |
| Date limite 10 novembre 2026 | ATTENTION  Plan urgent |

---

## 9. Recommandations & conclusion

GOVIA Cameroun est **faisable**, à condition de :
1. **Respecter la Loi n° 2024/017** : consentement explicite, pas de transfert transfrontalier non autorisé, pas de données biométriques → privilégier un **modèle local**.
2. **Ne pas inventer de politiques** : documenter chaque lacune (gap) — c'est la **partie la plus valorisée** du hackathon.
3. **Construire une base multi-démarches** (CNI = exemple, pas la seule) avec des **textes réels et ouverts**.
4. **Détailler le mapping Y.3172** et faire la **démo version A vs B**.
5. **Travailler en urgence** sur un MVP ciblé (CNI + passeport), livré avant le **10 novembre**.

**Prochaines étapes immédiates :** lancer la constitution de la base de connaissances (chunks JSON des textes du §6) ; monter le squelette du code ; décider du modèle (cloud pour démo avec anonymisation, local pour conformité).

---

## Annexe A — Mapping Y.3172 complété (tableau détaillé)

| Nœud | Description détaillée GOVIA | Politique applicable (exemples) |
|---|---|---|
| SRC | Prompt citoyen + pièces (images) + base politiques (JSON) | Loi 2024/017 (finalité, minimisation) |
| C | Conversation + OCR (Tesseract) + indexation politiques | Loi 2024/017 (sécurité des données) |
| PP | Nettoyage, détection langue, **anonymisation**, normalisation formats | Loi 2024/017 (art. 33 données sensibles, anonymisation) |
| M | LLM (Ollama/Groq) + RAG (ChromaDB) + extraction intent + pré-remplissage | Décret 2016/375 (CNI, pièces) ; ordonnance 81/02 (état civil) |
| P | Chaque étape cadrée par un texte cité | Loi 2024/017 (consentement, DPIA) ; décret 2016/375 ; loi 92-007 |
| D | Réponse + formulaire pré-rempli + rapport d'audit vers le citoyen | Loi 2010/012, 2010/021 (signature électronique, validation citoyenne) |
| SINK | Citoyen valide/soumet ; auditeur reçoit le rapport | Décret 2016/375 (validation finale) ; responsabilité du citoyen |

## Annexe B — Références des textes juridiques (ouverts)

- Décret n° 2016/375 du 04 août 2016 (CNI) — DGSN / prc.cm
- Décret n° 2021/347 du 17 juin 2021 (Passeports) — legecam.cm / prc.cm
- Ordonnance n° 81/02 du 29 juin 1981 (État civil) — droitcamerounais.info
- Loi n° 2011/011 du 06 mai 2011 (délais état civil) — camerlex.com
- Loi n° 1968-LF-3 du 11 juin 1968 (Code de la nationalité) — refworld.org / ILO
- Loi n° 92-007 du 14 août 1992 (Code du travail) — ILO / droitcamerounais.info
- **Loi n° 2024/017 du 23 décembre 2024 (Protection des données)** — Présidence / mathihis
- Loi n° 2010/012 du 21 décembre 2010 (Cybersécurité) — antic.cm
- Loi n° 2010/021 du 21 décembre 2010 (Commerce électronique) — mincommerce.gov.cm
- Décret n° 79/341 du 03 septembre 1979 (Immatriculation véhicules) — hacig.fr.gd
- Décret n° 2020/PM du 01 juin 2020 (Cartes grises sécurisées) — spm.gov.cm
- Décret n° 2016/373 du 04 août 2016 (Étrangers) — lc-doc.com
- Procédure IDCAM — idcam.cm ; Procédure PassCam — passcam.cm
- FGI 2026 / E-Gov'A 2026 — contexte DPI

## Annexe C — Scénario de démo (version A vs B)

**Question du citoyen (ambiguë) :** « Je veux renouveler ma carte. »

| | Version A (sans gouvernance) | Version B (gouvernée) |
|---|---|---|
| Réponse | Directe : « Renouvellez votre CNI en ligne sur idcam.cm. » (risque : la carte peut être la carte grise ou la carte de séjour) | Demande clarification ; identifie les démarches possibles (CNI, carte grise, carte de séjour) ; **cite les textes** (décret 2016/375, décret 79/341, décret 2016/373) ; l'**auditeur** signale l'ambiguïté et demande précision. |
| Traçabilité | Aucune | Références aux textes + journal d'audit |
| Conformité | Risque d'erreur non contrôlé | Chaque conseil justifié par un texte ; consentement requis |

---

*Document généré le 26 octobre 2026 — Étude de faisabilité technique et juridique GOVIA Cameroun. Respect des contraintes et règles du hackathon ITU AI for Good Lab.*
