# Comparaison version A / version B

Générée le 2026-11-10 par `scripts/compare_ab.py`. Les réponses complètes sont dans `comparaison_ab.json`.

Recherche : mots_cles. LLM de la version B : activé. Modèle (A et B) : openai/gpt-oss-120b via Groq.

| Scénario | Version A | Version B | Verdict B |
|---|---|---|---|
| Demande ambiguë (scénario de l'étude) | Verdict observé : non_conforme | clarification | conforme |
| Cas particulier : perte | Verdict observé : non_conforme | reponse (cni, perte), 5 citations | partiel |
| Renouvellement simple : quelles pièces ? | Verdict observé : non_conforme | reponse (cni, peremption), 7 citations | partiel |
| Démarche hors identité | Verdict observé : non_conforme | clarification (creation_societe) | conforme |
| Coût d'une démarche | Verdict observé : non_conforme | reponse (permis_construire), 20 citations | conforme |
| Démarche sans texte ouvert | Verdict observé : non_conforme | lacune (permis_conduire) | conforme |
| Sujet hors périmètre | Verdict observé : non_conforme | hors_perimetre | conforme |
| Demande illicite | Verdict observé : non_conforme | refus | conforme |
| Données personnelles dans la question | Verdict observé : non_conforme | reponse (passeport), 9 citations | partiel |
| Question en anglais | Verdict observé : non_conforme | reponse (passeport), 6 citations | partiel |
| Question sur les données | Verdict observé : non_conforme | reponse (protection_donnees), 3 citations | conforme |
