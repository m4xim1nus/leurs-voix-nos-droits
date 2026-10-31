# Roadmap

Projet sans calendrier engageant. Ce fichier est le **plan opérationnel** :
il porte le cycle en cours, et seulement lui. Ce qui est livré est dans
`CHANGELOG.md`, les cycles à venir et les idées dans `BACKLOG.md`. Règles
de tenue : `CLAUDE.md`, section « Suivi ».

## Cycle en cours : XVe

2017-2022 : sécurité globale, séparatisme, anti-casseurs, état d'urgence sanitaire. Le but : couvrir la
législature, données et qualifications, **d'un coup** à la fin du cycle.

### Où se fait le travail

Tout se passe sur la branche `xve` (worktree `.claude/worktrees/xve`), jamais sur `main`, qui continue de vivre
(passe quotidienne, publications de l'admin) sans rien voir de la XVe. Trois conséquences :

- **Rien de la XVe ne passe par l'admin en ligne avant la fin.** La passe quotidienne de `main` retirerait de D1 un
  catalogue XVe (`sync-admin` efface ce que l'export ne contient pas), et « Publier » écrirait sur `main`.
- Les brouillons sont dans `source/brouillons-xve-*`, les relectures dans `source/relecture-xve-*.md`. Une fois
  validés par Max dans le chat, ils entrent dans le `data/editorial.json` de la branche.
- `main` est fusionnée régulièrement dans `xve`. `data/export/` ne se fusionne jamais à la main : on le régénère.
  `data/editorial.json` non plus, l'admin le réécrit sur `main` : on prend celui de `main`, puis on rejoue
  `lvnd editorial --ajouter` sur chaque `source/brouillons-xve-*`.

### Décisions de Max du 31/10/2026

Passées dans `docs/METHODO.md` : l'échéance d'un régime restrictif vaut dans les deux sens et seul compte le droit de la
date du vote (règle 4) ; lois de finances écartées faute de source (règle 8) ; lois d'une même crise comptées chacune pour
1, et leur note le dit (règle 18). Le Sénat de 2017-2022 reste hors du cycle (`BACKLOG.md`). La fiche député·e aura le
détail par législature (règle 19, item 10). Lot 1 : `regime-exception` retirée de terrorisme 2021 et de sécurité globale,
`vie-privee` principal sur sécurité globale et responsabilité pénale 2022, V3223 affiché, V1642 non retenu. **Les six textes
du lot 1 sont validés par Max** et dans le `data/editorial.json` de la branche.

### Items

1. [x] Sources XVe et XIVe, `LEGISLATURES`, rattachements figés, lignées de groupes, anomalies du dump dans `lvnd check`.
   Sur les mêmes dumps, rien ne change pour les XVIe, XVIIe et le Sénat, sauf 5 lignes de `textes.csv` enrichies de
   leurs votes XVe (aucun décisif modifié).
2. [ ] Amendements XVe : plan B en cours, une dizaine d'heures (le dump plafonne à 11 Ko/s, soit 16 h, et chaque octet
   relance son délai d'attente : il ne bascule jamais seul sur le plan B, à corriger dans `lvnd download`). Puis seuil de
   `lvnd check`, et copie dans la release `donnees-figees` : **sans elle, la passe quotidienne échouerait après la
   fusion**, faute de pouvoir récupérer l'archive.
3. [ ] Temps de la passe quotidienne avec la XVe (60 min au plus, sans cache des `seance.parquet`) ; garde-fous de
   `donnees-quotidien.yml`.
4. [x] Site : vues par législature, XVe affichée dès qu'un de ses textes est qualifié ; périmètre et limites sur la
   page Méthodologie. À revoir avec de vraies qualifications, fiche député·e comprise.
5. [x] Contrôle croisé des positions XVe avec datan.fr (leurs-votes.fr ne couvre pas 2017-2022) : aucun écart réel.
   Section XVe de `docs/SOURCES.md`.
6. [x] Tri validé par Max (31/10/2026), fiche `source/relecture-xve-tri.md` : 173 écarts entrés (règle 8 : 33 ; règle 9 : 76,
   sans exception ; hors grille : 64). Restent à qualifier les 74 de la liste A, et 13 lois de finances à passer par une
   recherche courte (écart si rien).
7. [x] Qualifications, par lots thématiques. Lots 1 à 6 validés par Max, dans `editorial.json` : libertés, crise sanitaire,
   immigration, lois de finances (3 qualifiées, 10 écartées), justice, enfants, égalité, droits civiques, social, environnement
   et santé. Consigne commune aux agents : `source/consigne-xve-agents.md`.
8. [x] Ticket restaurant étudiant (DLR5L15N41895) : reste écarté, motif neuf, aucune source admise.
9. [x] `lvnd download` : sous 20 Ko/s pendant la patience, une source avec plan B y bascule (`sources.DEBIT_MINIMAL`).
10. [x] Fiche député·e : score par législature à partir de deux législatures (règle 19), `scores_deputes_legislatures.csv`,
    écrit par `lvnd scores`. À revoir avec les qualifications de la XVe, comme l'item 4.
11. [x] Entrée des textes validés dans le `data/editorial.json` de la branche, sans D1 :
    `uv run lvnd editorial --ajouter ../source/brouillons-xve-lotN` (`--remplacer` pour corriger un texte déjà entré),
    seulement après la réponse explicite de Max, puis `uv run lvnd scores`. Rejouable sans effet.
12. [x] Résumés du Conseil constitutionnel du lot 1, repris sur l'original et entrés dans `editorial.json`. Le
    rattachement de la loi ordinaire de 2017 sur la vie politique passe de 2017-753 DC, décision de la loi organique, à
    2017-752 DC : effet sur `textes.csv` au rebuild de A.
13. [ ] Amendements clés des lots 1 à 6 à recontrôler après le plan B ; tout changement repasse par Max.
14. [x] Sigles de la XVe à l'affichage : `UDI-I` sur le site, `UDI_I` reste dans les données.

### Reprendre : deux conversations en parallèle

**La conversation A** (celle qui a ouvert le cycle) dort jusqu'à la fin du plan B des amendements, puis fait l'item 2 et le
rebuild. **La conversation B** a avancé le reste, et s'arrête : voir « Passation » plus bas. Elles partagent le worktree `.claude/worktrees/xve` et commitent par
chemins nommés.

Règles pour B, tant que le plan B tourne (`pgrep -f sources.download`) :

- **Ne pas lancer `lvnd download`** : le verrou de `data/raw/` est pris. Ne pas supprimer `data/raw/an_amendements_15/`.
- **Ne jamais commiter `data/export/`** : c'est une copie de travail XVe, sans amendements, sur des dumps du 31/10 au
  matin. Les agents et le site la lisent telle quelle, `amendement_id` et division vides pour la XVe. Ne pas la restaurer.
- Un `lvnd build` s'écrit ailleurs (`--sqlite` et `--export` dans le scratchpad). Il crée `data/raw/an_amendements_15/seance.parquet`,
  partiel : A le supprime avant son build final. Le test `donnees.test.ts` échoue sur DLR5L17N51427 tant que les dumps
  sont ceux du matin, c'est attendu ; `lvnd check` échoue sur les amendements XVe, c'est attendu aussi.
- Ne rien pousser sans l'accord de Max. Ne rien charger dans D1 (voir plus haut).

Ordre conseillé pour B :

1. **Tri (item 6)** : `source/relecture-xve-tri.md`, avec les listes d'écart d'office (règle 8 : 33 ; règle 9 : 76) et les 156
   textes, chacun avec une proposition d'une ligne, plus les 49.3 sans vote final et le ticket restaurant (item 8). Max répond
   en lot. Les YAML d'écart vont dans `source/brouillons-xve-tri/`.
2. **Item 12**, si le site du Conseil constitutionnel répond ou si Max colle les décisions.
3. **Lots suivants**, selon `docs/QUALIFICATION.md` (cinq textes au plus par agent, dossier neuf `source/brouillons-xve-lotN/`, pas
   de bloc `senat`). Prochain lot : crise sanitaire, avec la règle 4 et la règle 18. Rappeler aux agents que `amendement_id` est vide
   (règle 11 d'après le titre du scrutin, à recontrôler), qu'on ne contourne aucun refus de site, et que tout document collectif
   se vérifie sur ses signataires.
4. **Items 9, 10 et 14** quand le tri laisse du temps.

Quand le plan B se termine, A : supprime `seance.parquet` ; `lvnd download --leger` puis `lvnd download an_dossiers_14` (manifeste) ; `lvnd
build` ; règle le seuil de `lvnd check` pour la XVe si besoin ; `pytest`, tests du site ; mesure la passe quotidienne (item 3) ; commite
`data/export/`. B recontrôle alors les amendements clés de tous les brouillons déjà faits.

### Passation de B à A (31/10/2026)

**B est close : A porte seule tout ce qui suit la fin du plan B.** Lots 1 à 6 commités, rien de B en attente dans le worktree.
En plus de la liste ci-dessus, A fait l'item 13 et ces recontrôles :

1. **Item 13.** Pour chaque scrutin `role: amendement` de la XVe dans `data/editorial.json`, lire `amendement_id` et la division dans
   `scrutins.csv`. Vérifier que c'est bien la suppression de l'article que dit `objet`, puis lire les points « à recontrôler » dans
   `relecture.points_attention` du brouillon (`source/brouillons-xve-*`). Chercher aussi les suppressions manquées, quand le titre du
   scrutin ne disait pas « suppression ».
2. **`lvnd check` complet sur la XVe** : les « scrutin absent du dossier » doivent disparaître au rebuild (sqlite d'avant la XVe).
   Lots 1 à 6 jamais passés par ce contrôle.
3. **Effets attendus au rebuild :** 2017-752 DC sur la loi ordinaire de 2017 (item 12), adresse de la 2019-790 DC (`_url_decision`).
4. **Affichage :** `gens-du-voyage-2018` (DLR5L14N36020), et les 4 écarts qui n'avaient pas d'état au catalogue.
5. **Tests attendus au vert :** `test_check_passe`, `test_un_etat_pour_chaque_texte_qualifie`, `donnees.test.ts`.

Garde-fous, inchangés :

- **Une qualification ne change jamais sans la réponse explicite de Max.** Tout écart de l'item 13 (amendement à retirer, à ajouter, sens,
  objet) va dans `source/relecture-xve-item13.md` avec une recommandation, pas dans `editorial.json` ni dans les brouillons. Un scrutin mal
  rattaché va au backlog. Une proposition encore ouverte sur le lot 6 : fin de `source/relecture-xve-lot6.md`.
- Commits par chemins nommés. Pousser ou lancer une étape de « Fin du cycle » (fusion dans `main`, release, D1, déploiement) seulement si
  Max l'a écrit explicitement, étape par étape.
- Rendre compte à Max de ce qui est fait, de ce qui échoue et de ce qui attend sa décision.

Si le plan B s'arrête (terminal fermé, plafond de 10 h), il reprend là où il en était :

```bash
cd .claude/worktrees/xve/pipeline && uv run python -c "
from pathlib import Path
from lvnd import sources
sources.PATIENCE_AVANT_SECOURS = 0
sources.download(Path('../data/raw'), ['an_amendements_15'], secours_max=600*60)"
```

### Fin du cycle : l'intégration d'un coup

Dans cet ordre, le même jour, sans publication depuis l'admin entre les étapes 3 et 5 : une publication écrirait un
`editorial.json` sans la XVe.

1. Verser `an_amendements_15` dans la release `donnees-figees`.
2. Fusionner `main` dans `xve`. `lvnd download`, `lvnd build`, `lvnd check`, tous les tests, `bash build.sh`.
3. Fusionner `xve` dans `main` : le site passe à la XVe en un seul déploiement.
4. Déployer l'admin (`admin/README.md`).
5. `lvnd sync-admin --remote --editorial` : D1 reçoit le catalogue et les qualifications, avec leur empreinte. La page
   « Publier » ne doit plus rien montrer de nouveau.
6. Vérifier le lendemain la passe quotidienne.
