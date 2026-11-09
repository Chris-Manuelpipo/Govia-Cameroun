# Comparaison version A / version B

Générée le 2026-11-06 par `scripts/compare_ab.py`. Les réponses complètes sont dans `comparaison_ab.json`.

Recherche : vectoriel. LLM de la version B : désactivé.

> **Version A non exécutée : aucun LLM n'était joignable.** Relancer le script avec Ollama démarré avant d'utiliser ce tableau dans le rapport.

| Scénario | Version A | Version B | Verdict B |
|---|---|---|---|
| Demande ambiguë (scénario de l'étude) | Non exécutée | clarification | conforme |
| Cas particulier : perte | Non exécutée | reponse (cni, perte), 7 citations | partiel |
| Renouvellement simple : quelles pièces ? | Non exécutée | reponse (cni, peremption), 7 citations | partiel |
| Démarche hors identité | Non exécutée | clarification (creation_societe) | conforme |
| Coût d'une démarche | Non exécutée | reponse (permis_construire), 20 citations | conforme |
| Démarche sans texte ouvert | Non exécutée | lacune (permis_conduire) | conforme |
| Sujet hors périmètre | Non exécutée | hors_perimetre | conforme |
| Demande illicite | Non exécutée | refus | conforme |
| Données personnelles dans la question | Non exécutée | reponse (passeport), 9 citations | partiel |
| Question en anglais | Non exécutée | reponse (passeport), 9 citations | partiel |
| Question sur les données | Non exécutée | reponse (protection_donnees), 3 citations | conforme |
