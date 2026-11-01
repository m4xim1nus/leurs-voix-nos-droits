# Roadmap

Projet sans calendrier engageant. Ce fichier est le **plan opérationnel** :
il porte le cycle en cours, et seulement lui. Ce qui est livré est dans
`CHANGELOG.md`, les cycles à venir et les idées dans `BACKLOG.md`. Règles
de tenue : `CLAUDE.md`, section « Suivi ».

## Cycle en cours : Relecture XVe

Ouvert le 01/11/2026. La v1.4.0 a publié 70 textes de la XVe sur des vues jamais relues avec de vraies données. Le but : relire
ce qui est en ligne, corriger ce qui en sort, et solder les reliquats d'outillage et de catalogue. Cycle court, sans nouvelle
qualification. Le travail se fait sur la branche `relecture-xve`, à la demande de Max (01/11/2026).

### Avant de commencer

Vérifier la passe quotidienne du 02/11/2026, première avec la XVe, et nettoyer les branches : ces deux tâches restent dans
« À trier » de `BACKLOG.md`, hors cycle. Tant que cette passe n'est pas confirmée, `data/export/` peut encore bouger.

### Garde-fous

- Toute correction qui change un décisif ou un score s'arrête et remonte à Max : l'item 7 est annoncé sans effet sur les deux, à
  vérifier par un diff de `scores_*.csv`, pas à présumer.
- Un `lvnd build` local peut réécrire les exports de l'AN : traiter l'item 6 avant l'item 7, et ne commiter que les changements voulus.

### Items

1. [x] **Filtre Législature de `/textes`** : XVIIe et XVIe sont en dur, sans XVe, avec « Les deux » comme choix par défaut
   (`site/src/routes/textes/+page.svelte:51`). Vu dans le code, à confirmer à l'écran. Tirer les options des données, renommer le
   choix par défaut (« Toutes »), et chercher le même défaut ailleurs.
2. [ ] **Relecture du site avec la XVe**, à l'écran et avec Max : vues par législature (`/droits`, groupes, accueil), fiche
   député·e et score par législature (règle 19), député·e présent·e sur plusieurs législatures, page Méthodologie. Ce qui en sort
   s'ajoute ici s'il s'agit d'une correction simple, à la fin d'« À trier » sinon.
3. [x] **Alertes** (`pipeline/lvnd/alertes.py`) : signaler un texte rejeté par le rejet d'une partie (PLFSS 2027, V9097) et un vote
   sur l'ensemble sans scrutin public, que `etat` suit déjà. Ensuite, retirer la réserve correspondante de « Textes à surveiller ».
4. [x] **`lvnd check`** : `DELAI_AMENDEMENTS` (`pipeline/lvnd/check.py:43`) ne s'applique plus à une législature figée. La XVIe
   doit afficher 3 159/3 173 au lieu de 3 041/3 053. Contrôler que la XVe reste au-dessus de son seuil de 98 %.
5. [x] **`lvnd download --leger`** : ne plus retenter le dump de l'AN, ni rester bloqué 20 minutes, pour des amendements XVe et XVIe
   venus du plan B ou de la release ; même chose en CI quand l'archive manque au cache. Un `.part` périmé (« taille X, attendu Y »)
   doit se purger seul.
6. [x] **`lvnd build` en local** : il réécrit les exports de l'AN quand `data/raw/` diffère de la copie de la CI. Le corriger si c'est
   simple, sinon documenter la marche à suivre pour ne changer qu'une partie des exports.
7. [ ] **Scrutins XVe mal rattachés ou mal situés** : V483 (immigration), V1094 (DLR5L15N36601), V1093 (en AN1, c'est la nouvelle
   lecture), V1518 et V1536 (programmation de la justice), V1941 (LOM), V3838 (révision constitutionnelle), V3518 et V3633 (climat et
   résilience). Titre différent de la division de l'amendement ou du PDF : V45, V738, V1612. Corriger dans les rattachements figés
   quand c'est sûr.
8. [ ] **Catalogue** : `cc_sens` vide pour 2021-817 DC ; `textes.csv` titre « 2021 à 2027 » pour la programmation de la recherche,
   alors que la loi dit 2030.
9. [ ] **« Prochains votes » de la fiche député·e** (`prochains`, `site/src/lib/server/vues.ts:205`) : y ajouter les textes du seul
   Sénat attendus à l'AN (casseurs-payeurs), exclus pendant le cycle Sénat pour ne pas toucher aux vues de l'AN.
