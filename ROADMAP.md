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

### Méthode

1. **Audit de cohérence** : repérer les cas similaires tranchés différemment, avec des agents, sans API. Avant la
   revue, qu'il alimente.
2. **Revue avec Max des qualifications politiquement sensibles**, tranchées par une règle fixe ou par défaut :
   - choix du droit principal qui inverse les groupes favorables et défavorables : antisemitisme-enseignement-superieur (discriminations étend contre libertes restreint), abrogation-obligation-vaccinale-2023 (travail-protection-sociale étend, retenu, contre sante restreint) ;
   - energies-renouvelables-2023 et nucleaire-acceleration-2023, toutes deux `environnement` restreint par la règle 2 (choix d'énergie hors grille) : sur les renouvelables, RN, LR, LFI et GDR, qui ont voté contre, sont comptés favorables ;
   - exécution provisoire de l'inéligibilité (RN, UDR et DR comptés favorables), peine d'inéligibilité (DLR5L16N47056), corps électoral de Nouvelle-Calédonie (2024 et 2026), droit de visite des parlementaires dans les établissements sociaux et médico-sociaux (RN compté favorable) ;
   - purge des nullités (`restreint` par la règle 4 : seul LFI compté favorable), mortalité infantile (`sante` restreint sur les sociétés savantes : seuls 4 EPR comptés favorables).

### Admin

3. **Version `autre` du Sénat** : droits, vigilance et sources se saisissent en JSON sur la fiche (20 textes sur 95
   lus au Sénat). Les passer aux formulaires habituels, pour que le tutoriel n'enseigne pas le JSON.
4. **Tutoriel de l'admin** pour les futur·es rédacteur·ices : connexion par Access, qualifier un texte, contrôles,
   brouillon et publication. Premier essai avec le contributeur qui a déjà accès.

### Exploitation

5. **Page « qui tourne quand »** : passe quotidienne, dump hebdomadaire, tests, sync de l'admin, build. Pour chacun :
   son rôle, ce qui bloque un commit, quoi faire en cas d'échec.

### Présentation

6. **Présentation du projet et des choix de méthode retenus** : page « bento » ou PDF, en dernier, car elle résume
   les blocs précédents. Neutre dans tout ce qui est versionné ou publié (`CLAUDE.md`).

### Finitions avant de montrer

7. **En-tête** : 8 onglets, plus le titre et la recherche. Proposition, à valider à l'écran, en liens simples, sans
   menu déroulant ni changement d'URL : Droits, Textes (avec En cours), Groupes (avec Comparer), Sénat, Méthode (avec
   Données), avec des sous-onglets sur les pages regroupées. La case de `/senat` disparaît au profit de celle de
   l'en-tête, qui cherche déjà les sénateur·ices.
8. **Recherche** : tolérance aux fautes de frappe (« Kasbarien »), en repli quand une recherche ne donne rien.
9. **`llms.txt` et documentation des données** : pour interroger le site avec son propre outil, à ses frais.
10. **Alerte sur un texte écarté revoté** : un texte écarté pour un autre motif que l'unanimité (AGRASC, faute de
    source) peut être revoté sans qu'aucune alerte ne le signale.
11. **Rattachement scrutin → dossier** : V6758 (loi d'urgence agricole) reste rattaché à la loi organique « natifs »
    de Nouvelle-Calédonie (DLR5L17N52104), lu dans `objet.dossierLegislatif`. Sans effet sur les scores ; un script
    dira si d'autres scrutins sont touchés.
12. **Relecture commune à l'écran** avec Max, absente du cycle Relecture XVe, et essais Firefox, Safari et lecteur
    d'écran (limites de la v1.6.0).
13. **Recherche INPI** sur le nom, le choix restant à la passation.

### Déjà fait dans ce cycle

- `/comparer` : un·e député·e face à un groupe se lit sur la seule législature de ce groupe, score global et droit par
  droit (règle 19, décision de Max du 01/11/2026). Nouvel export `scores_deputes_droits_legislatures.csv`.
