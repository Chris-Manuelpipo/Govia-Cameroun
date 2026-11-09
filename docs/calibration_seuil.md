# Calibration du seuil de recherche

Générée le 2026-11-06 par `scripts/calibrer_seuil.py`, avec le modèle `paraphrase-multilingual-MiniLM-L12-v2` et ChromaDB dans l'image Docker du backend.

Le seuil `GOVIA_MIN_SCORE` ne joue que pour une question sans démarche identifiée : il décide entre proposer des passages proches et répondre qu'aucune démarche n'a été trouvée. Une recherche restreinte à une démarche n'y est pas soumise.

**Seuil le mieux noté : 0.45**, avec 0 question(s) hors sujet sur 14 qui reçoivent des passages et 16 question(s) du périmètre sur 20 qui reçoivent un passage de la bonne démarche.

Sans seuil, le bon passage arrive en tête pour 16 questions sur 20, et dans les trois premiers pour 18 sur 20.

Ce jeu de 34 questions, écrit par l'équipe, permet de choisir un seuil. Il ne mesure pas la qualité de la recherche en conditions réelles.

| Seuil | Hors sujet avec passages | Périmètre avec le bon passage |
|---|---|---|
| 0.20 | 8/14 | 18/20 |
| 0.25 | 5/14 | 18/20 |
| 0.30 | 2/14 | 18/20 |
| 0.35 | 1/14 | 17/20 |
| 0.40 | 1/14 | 16/20 |
| 0.45 | 0/14 | 16/20 |
| 0.50 | 0/14 | 13/20 |
| 0.55 | 0/14 | 10/20 |
| 0.60 | 0/14 | 9/20 |
| 0.65 | 0/14 | 5/20 |
| 0.70 | 0/14 | 2/20 |

## Questions hors sujet

| Question | Meilleur score |
|---|---|
| Quelle est la meilleure équipe de football du Cameroun ? | 0.448 |
| Quelle heure est-il ? | 0.342 |
| Comment soigner le paludisme ? | 0.279 |
| Quel est le prix du pain au marché ? | 0.275 |
| Qui a gagné la coupe du monde ? | 0.274 |
| Raconte-moi une blague | 0.232 |
| Comment réparer mon téléphone ? | 0.225 |
| What is the capital of France? | 0.219 |
| What is the weather like today? | 0.171 |
| Quel temps fait-il à Douala ? | 0.168 |
| Donne-moi une recette de ndolé | 0.157 |
| Comment faire un gâteau au chocolat ? | 0.095 |
| Recommend me a good movie | 0.087 |
| How do I learn to play guitar? | 0.073 |

## Questions du périmètre

| Question | Meilleur score | Démarche en tête | Bonne démarche dans le top 3 |
|---|---|---|---|
| How long is a passport valid? | 0.798 | passeport | oui |
| What can a passport application be refused for? | 0.773 | passeport | oui |
| Quelles sanctions si j'envoie des données à l'étranger sans autorisation ? | 0.690 | protection_donnees | oui |
| Is an electronic signature legally valid? | 0.670 | signature_electronique | oui |
| Combien de temps ma carte d'identité reste-t-elle valable ? | 0.668 | cni | oui |
| Comment devenir propriétaire légal d'un terrain ? | 0.647 | titre_foncier | oui |
| Who may ask for a nationality certificate? | 0.626 | certificat_nationalite | oui |
| Can personal data be sent abroad? | 0.613 | protection_donnees | oui |
| Combien de temps pour déclarer un nouveau-né ? | 0.601 | acte_naissance | oui |
| Mon employeur doit-il me donner un contrat écrit ? | 0.553 | contrat_travail | oui |
| À partir de quel âge peut-on avoir une pièce d'identité ? | 0.538 | passeport | oui |
| Ma mère âgée peut-elle toucher une retraite ? | 0.537 | cnps_pension_vieillesse | oui |
| Qui célèbre un mariage à la mairie ? | 0.501 | acte_mariage | oui |
| Ai-je le droit de refuser une décision prise par une machine ? | 0.499 | protection_donnees | oui |
| Quels papiers pour bâtir une maison ? | 0.498 | permis_construire | oui |
| Je vends au marché, quel impôt dois-je payer ? | 0.484 | commercant_individuel | non |
| Mon mari est mort, ai-je droit à une pension ? | 0.469 | cnps_pension_vieillesse | oui |
| Que faire si on m'a volé mes papiers ? | 0.394 | protection_donnees | non |
| Comment faire venir des marchandises de l'étranger ? | 0.381 | fichier_importateurs | oui |
| Je veux ouvrir une boutique | 0.344 | commercant_individuel | oui |
