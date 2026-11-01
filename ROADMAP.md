# Roadmap

Projet sans calendrier engageant. Ce fichier est le **plan opérationnel** :
il porte le cycle en cours, et seulement lui. Ce qui est livré est dans
`CHANGELOG.md`, les cycles à venir et les idées dans `BACKLOG.md`. Règles
de tenue : `CLAUDE.md`, section « Suivi ».

## Cycle en cours : Sénat, suite

Branche `senat-suite`. But : le Sénat de 2017-2022 lu comme celui d'après, et les compléments laissés hors du cycle Sénat. Décisions de Max du 01/11/2026.

1. **Données** : scrutins et votes depuis le 27/06/2017, contrôle croisé sur senat.fr. Fait.
2. **Période** (règle 26) : deux périodes, coupées au 28/06/2022. Fait.
3. **Votes du Sénat sur les textes de la XVe** : décidés, à charger puis à publier depuis l'admin.
4. **Amendements clés du Sénat** (règles 11 et 26) : 19 décidés sur 87 candidats, à charger puis à publier. Budgets au backlog.
5. **Cartes partageables** des sénateur·ices. Fait.
6. **Comparer** pour le Sénat, à l'intérieur de la chambre (`/senat/comparer`). Fait.
7. **Mise en service** : fusion, déploiement de l'admin, `lvnd sync-admin --remote`, chargement de `source/brouillons-suite-final`, publication.
