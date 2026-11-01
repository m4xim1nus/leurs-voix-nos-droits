# Roadmap

Projet sans calendrier engageant. Ce fichier est le **plan opérationnel** :
il porte le cycle en cours, et seulement lui. Ce qui est livré est dans
`CHANGELOG.md`, les cycles à venir et les idées dans `BACKLOG.md`. Règles
de tenue : `CLAUDE.md`, section « Suivi ».

## Cycle en cours : Prise en main

**But** : que Max maîtrise de bout en bout les choix de méthode, l'admin et les actions programmées, et que le
projet soit prêt à être montré. Les supports produits servent d'abord à cela ; ce qui demande de discuter avec
celles et ceux qui reprendront le projet reste au cycle Passation.

Avant d'ouvrir le travail : vérifier la passe du 02/11/2026 et supprimer les branches (`BACKLOG.md`, « À trier »).

### Reste à faire, avec Max

1. **Revue des qualifications sensibles et de l'audit de cohérence** : fiche préparée, `source/revue-prise-en-main.md` (non versionnée). Puis requalifications par le circuit habituel, et règles nouvelles dans `docs/METHODO.md`.
2. **Premier essai du tutoriel** avec le contributeur qui a déjà accès (`docs/TUTORIEL_ADMIN.md`).
3. **Relecture commune à l'écran**, dont l'en-tête à cinq rubriques (proposition à valider), et essais Firefox, Safari et lecteur d'écran (limites de la v1.6.0).
4. **Recherche INPI** sur le nom, à la main : la base bloque les accès automatisés.
5. **Présentation** : à revoir après la revue, qui peut changer des choix qu'elle résume.
6. **Après fusion dans `main`** : `cd admin && npm run deploy`, car l'admin ne se déploie pas seule (formulaires du Sénat, alerte `ecart_revote`, lien Aide).

### Déjà fait dans ce cycle

- **Audit de cohérence** par agents, sans API : 199 textes et 620 écarts, rapports dans `source/audit-coherence/`.
- **Version `autre` du Sénat** : droits, étiquettes, sources et vigilance aux formulaires habituels (`EditeurDroits`).
- **Tutoriel de l'admin** (`docs/TUTORIEL_ADMIN.md`, lien « Aide »), et **page « qui tourne quand »** (`docs/EXPLOITATION.md`).
- **En-tête** à cinq rubriques et sous-onglets. La case de `/senat` disparaît : celle de l'en-tête donne aussi les sénateur·ices d'un code postal.
- **Recherche** : repli sur la saisie corrigée quand rien ne correspond (« Kasbarien »), signalé à l'écran.
- **`llms.txt` et dictionnaire des données** (`/donnees.md`), avec un test qui échoue si une colonne y manque.
- **Alerte `ecart_revote`** sur un texte écarté revoté. **Rattachement** : V6758 corrigé, seul cas trouvé, sans effet sur les scores.
- `/comparer` : un·e député·e face à un groupe se lit sur la seule législature de ce groupe, score global et droit par
  droit (règle 19, décision de Max du 01/11/2026). Nouvel export `scores_deputes_droits_legislatures.csv`.
