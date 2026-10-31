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

### Items

1. [x] Sources XVe et XIVe, `LEGISLATURES`, rattachements figés, lignées de groupes, anomalies du dump dans `lvnd check`.
   Sur les mêmes dumps, rien ne change pour les XVIe, XVIIe et le Sénat, sauf 5 lignes de `textes.csv` enrichies de
   leurs votes XVe (aucun décisif modifié).
2. [ ] Amendements XVe : plan B en cours (dump bloqué par le serveur de l'AN, comme pour la XVIe). Puis seuil de
   `lvnd check`, et copie dans la release `donnees-figees` : **sans elle, la passe quotidienne échouerait après la
   fusion**, faute de pouvoir récupérer l'archive.
3. [ ] Temps de la passe quotidienne avec la XVe (60 min au plus, sans cache des `seance.parquet`) ; garde-fous de
   `donnees-quotidien.yml`.
4. [x] Site : vues par législature, XVe affichée dès qu'un de ses textes est qualifié ; périmètre et limites sur la
   page Méthodologie. À revoir avec de vraies qualifications, fiche député·e comprise.
5. [x] Contrôle croisé des positions XVe avec datan.fr (leurs-votes.fr ne couvre pas 2017-2022) : aucun écart réel.
   Section XVe de `docs/SOURCES.md`.
6. [ ] Tri : 265 textes avec un décisif XVe. 33 écartés par la règle 8 (conventions, résolutions), 76 par la règle 9
   (unanimes), 156 à trier (72 candidats par mots-clés, 84 sans). S'y ajoutent les lois adoptées par le 49.3 sans
   vote final (retraites 2020). Listes soumises à Max, comme aux lots de tri.
7. [ ] Qualifications, par lots thématiques. Lot 1 (libertés) : séparatisme, sécurité globale, anti-casseurs, SILT,
   terrorisme et renseignement 2021, responsabilité pénale 2022. Puis crise sanitaire, immigration, justice, social,
   environnement, santé.
8. [ ] Revoir l'écart du ticket restaurant étudiant (DLR5L15N41895) : écarté pour unanimité, il a un vote disputé en
   XVe (V3995, 34-14), que l'alerte `unanimite_contestee` signale désormais.
9. [ ] Décisions de `docs/A_VALIDER.md`.

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
