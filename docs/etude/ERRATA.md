# Errata de l'étude de faisabilité

L'étude du 26 octobre 2026 (`GOVIA_Cameroun_Etude_Faisabilite.*`) reste utile pour le raisonnement, mais les références ci-dessous sont fausses ou incomplètes. Le rapport technique doit reprendre les références corrigées, relues le 5 novembre 2026 sur les textes sources.

## Références à corriger

| Passage de l'étude | Indication erronée | Référence vérifiée |
|---|---|---|
| §4.1, §4.2, §6 : pièces de la CNI | Décret 2016/375, art. 11 | **Art. 6** ; l'art. 11 contient des dispositions transitoires |
| §4.1, §4.2, §4.3 gap 4, annexe A : données sensibles et biométrie | Loi 2024/017, art. 33 | **Art. 5** (définition), **art. 48** (interdiction, qui vise « la biométrie en matière de santé »), **art. 66** (sanction) |
| §4.1 : analyse d'impact | Non rattachée à un article | **Art. 33** de la Loi 2024/017 |
| §4.2 : transferts | Art. 32 | Correct. Sanctions : **art. 60** (10 à 50 millions de FCFA) et **art. 69** (3 à 10 ans, 2 à 20 millions de FCFA) |
| §4.2 : donneur et destinataire « solidairement responsables » d'un transfert illicite | Présenté comme une règle de la loi | Non retrouvé dans le texte. La solidarité vise la publication sans consentement (art. 23) et le traitement conjoint (art. 31) |
| §4.2 : amendes « de 1 à 1 000 millions » | Présenté comme une fourchette générale | **Art. 71** : 50 millions à 1 milliard de FCFA pour les personnes morales ; autres montants selon l'infraction |
| §4.2 : naissance sous 60 jours, décès sous 90 jours (loi 2011/011) | Non vérifiable | L'ordonnance 81/02 indique 30 jours (art. 30), 3 mois pour le jugement (art. 33) et « dans le mois » pour le décès (art. 78). La loi 2011/011 n'a pas pu être consultée : **à vérifier** |
| §6 : passeport, certificat de nationalité et jugement supplétif requis | Liste de pièces | Absents de l'**art. 12, al. 3** du décret 2021/347 |
| §6 : décret 79/341 pour la carte grise | Immatriculation | La source consultée est l'**arrêté n° 82/705/A/MINT** ; le décret 79/341 (Code de la route) n'a pas été retrouvé |
| Code du travail : écrit obligatoire au-delà de 3 mois (base initiale) | Art. 28 | **Art. 27** ; l'art. 28 traite de l'engagement à l'essai |

## Écarts à ajouter à l'analyse (§4.3)

Ces écarts ressortent de la lecture de la Loi 2024/017 et n'apparaissent pas dans l'étude :

1. **Autorisation préalable de tout traitement (art. 19).** Elle est exigée, avec une pénalité de 5 à 50 millions de FCFA sans autorisation (art. 55), mais ses modalités relèvent d'un texte réglementaire, et l'Autorité qui la délivre doit être créée par décret (art. 53, al. 2). Il faut vérifier si ce décret existe.
2. **Consentement ou mission d'intérêt public (art. 9).** Un service opéré par l'administration pourrait relever de la dérogation de l'art. 9, al. 2 ; un service tiers comme GOVIA dépend du consentement.
3. **Décision automatisée (art. 21 et 44).** Le droit à une intervention humaine existe. GOVIA oriente sans décider, mais aucun texte ne dit où s'arrête l'orientation d'un agent d'IA et où commence une décision.
4. **État civil (art. 72).** Le traitement des données d'état civil relève de « textes spécifiques » : leur absence d'identification est un écart propre aux démarches de GOVIA.
5. **Masquage et anonymisation (art. 5).** La loi distingue les deux. Le masquage de GOVIA relève de la pseudonymisation, et la loi ne dit pas si le masquage automatique d'une question libre suffit avant un envoi à un modèle.

## Lacunes documentaires

La liste à jour des démarches sans source ouverte est générée dans [`docs/catalogue_demarches.md`](../catalogue_demarches.md).
