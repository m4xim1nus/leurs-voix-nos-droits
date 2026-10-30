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

1. ⏳ **Attribuer les motions de censure à chaque texte.** Leur intitulé ne nomme
   pas le texte. En XVIIe, les dossiers le disent : V693 pour le PLF 2025 ; V519,
   V694, V739 et V791 pour le PLFSS 2025. En XVIe, seule V664 est rattachée (PLFSS
   2023) ; 25 motions du 49.3, du 24/10/2022 au 21/12/2023, n'ont aucun dossier
   (hors retraites, V1240 et V1241), et certaines peuvent porter sur un autre texte
   (programmation des finances publiques). On les attribue une à une, chacune d'après
   une source officielle de l'AN, et une motion sans attribution sûre n'est pas retenue.
2. ⏳ **Préparer les six qualifications**, lot par le circuit de
   `docs/QUALIFICATION.md` : mesures qui touchent des droits, sens selon les règles
   de la grille (règle 4 pour un texte composite), au moins une source publique admise,
   résumé qui dit l'adoption par 49.3. Faute de source admise, le texte attend. Les
   sources de 2022-2023 seront plus rares : la fiche le dit.
3. ⏳ **Décision de Max, texte par texte**, puis validation et publication.
4. ⏳ **Écarter les dossiers d'engagement de responsabilité** rattachés à part, avec
   leur motif : DLR5L17N50975, DLR5L17N51427, DLR5L17N51462, DLR5L17N51475 (PLFSS
   2025) et DLR5L17N53689 (PLF 2026, déjà qualifié avec ces motions). À faire après
   la publication des textes dont ils portent les motions.
5. ⏳ **Contrôle final** : `lvnd check` vert et `scores_*.csv` identiques à
   l'octet, le 49.3 ne comptant dans aucun score.
