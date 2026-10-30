# Roadmap

Projet sans calendrier engageant. Ce fichier est le **plan opérationnel** :
il porte le cycle en cours, et seulement lui. Ce qui est livré est dans
`CHANGELOG.md`, les cycles à venir et les idées dans `BACKLOG.md`. Règles
de tenue : `CLAUDE.md`, section « Suivi ».

## Cycle en cours : Stock des lois de finances

But : qualifier les six lois de finances adoptées par 49.3 sans vote final, pour
qu'elles figurent sur le site avec leurs motions de censure. Elles ne comptent
dans aucun score (règle 9). Items `[→Stock des lois de finances]` de
`BACKLOG.md`. Le modèle est `plf-2026` dans `data/editorial.json`.

| Texte | Dossier | Scrutins au catalogue | Loi |
|---|---|---|---|
| PLF 2023 | DLR5L16N45988 | 201 | 2022-1726 |
| PLFSS 2023 | DLR5L16N46347 | 43 | 2022-1616 |
| PLF 2024 | DLR5L16N48397 | 99 | 2023-1322 |
| PLFSS 2024 | DLR5L16N48683 | 30 | 2023-1250 |
| PLF 2025 | DLR5L17N50198 | 344 | 2025-127 |
| PLFSS 2025 | DLR5L17N50588 | 79 | 2025-199 |

Aucun de ces six dossiers n'a de vote sur l'ensemble au catalogue (mesuré le
30/10/2026).

1. ✅ **Attribuer les motions de censure à chaque texte.** Chacune d'après la page du
   dossier de l'AN et le compte rendu de la séance du vote. PLF 2023 : V358, V359,
   V494, V744, V780, V822. PLFSS 2023 : V360, V485, V486, V632, V634, V664. PLF 2024 :
   V2798, V2799, V2944, V3210, V3211, V3215. PLFSS 2024 : V2809, V2810, V2887, V3046,
   V3067, V3116. PLF 2025 : V693. PLFSS 2025 : V519, V694, V739, V791. V2610 et V2989
   portent sur la programmation des finances publiques : non retenues.
2. ✅ **Préparer les six qualifications** : les six sont « à relire » dans l'admin.
3. ✅ **Décision de Max, texte par texte**, puis validation et publication (30/10/2026,
   `b512282`).
4. ✅ **Écarter les dossiers d'engagement de responsabilité** rattachés à part, avec
   leur motif : DLR5L17N50975, DLR5L17N51427, DLR5L17N51462, DLR5L17N51475 (PLFSS
   2025) et DLR5L17N53689 (PLF 2026) (publié le 30/10/2026, `044d105`).
5. ✅ **Contrôle final** : `lvnd check` vert. Avec ou sans les six lois (éditorial de
   `58ee13f` contre celui de `044d105`, même export), `scores_*.csv` et
   `participation.csv` sont identiques à l'octet.
