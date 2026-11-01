# Roadmap

Projet sans calendrier engageant. Ce fichier est le **plan opérationnel** :
il porte le cycle en cours, et seulement lui. Ce qui est livré est dans
`CHANGELOG.md`, les cycles à venir et les idées dans `BACKLOG.md`. Règles
de tenue : `CLAUDE.md`, section « Suivi ».

## Cycle en cours : Prise en main

**But** : que Max maîtrise de bout en bout les choix de méthode, l'admin et les actions programmées, et que le
projet soit prêt à être montré. Les supports produits servent d'abord à cela ; ce qui demande de discuter avec
celles et ceux qui reprendront le projet reste au cycle Passation.

### Reste à faire

1. **Publier** les 25 derniers textes validés de la revue (Max).
2. **Déploiement de l'admin** : fait le 01/11/2026.
3. **Premier essai du tutoriel** avec le contributeur qui a déjà accès (`docs/TUTORIEL_ADMIN.md`).
4. **Passe du 02/11/2026** à vérifier, puis suppression des branches (`BACKLOG.md`).
5. **Bento** : régénérer le PDF après publication (`docs/presentation/README.md`). Clôture du cycle ensuite.

### Déjà fait dans ce cycle

- **Audit de cohérence** par agents, sans API : 199 textes et 620 écarts, rapports dans `source/audit-coherence/`.
- **Version `autre` du Sénat** : droits, étiquettes, sources et vigilance aux formulaires habituels (`EditeurDroits`).
- **Tutoriel de l'admin** (`docs/TUTORIEL_ADMIN.md`, lien « Aide »), et **page « qui tourne quand »** (`docs/EXPLOITATION.md`).
- **En-tête** à cinq rubriques et sous-onglets. La case de `/senat` disparaît : celle de l'en-tête donne aussi les sénateur·ices d'un code postal.
- **Recherche** : repli sur la saisie corrigée quand rien ne correspond (« Kasbarien »), signalé à l'écran.
- **`llms.txt` et dictionnaire des données** (`/donnees.md`), avec un test qui échoue si une colonne y manque.
- **Alerte `ecart_revote`** sur un texte écarté revoté. **Rattachement** : V6758 corrigé, seul cas trouvé, sans effet sur les scores.
- **Revue avec Max** des qualifications sensibles et de l'audit : règles 4 et 11 précisées (`docs/METHODO.md`).
- **Relecture commune à l'écran**, dont l'en-tête, et **recherche INPI** sur le nom, sans résultat (Max, 01/11/2026).
- **Présentation** : bento A4 en PDF, `docs/presentation/`, hors du site et de l'admin.
- `/comparer` : un·e député·e face à un groupe se lit sur la seule législature de ce groupe, score global et droit par
  droit (règle 19, décision de Max du 01/11/2026). Nouvel export `scores_deputes_droits_legislatures.csv`.
