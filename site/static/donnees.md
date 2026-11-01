# Dictionnaire des données

Fichiers de <https://lvnd.technoperchoir.fr/donnees>, tous sous `/donnees/` : CSV en UTF-8, séparateur virgule, avec en-tête. Une
cellule vide signifie « sans objet » ou « inconnu ». Licence Ouverte 2.0. Les règles citées sont celles de la
[méthodologie](https://lvnd.technoperchoir.fr/methodologie).

Les votes viennent de l'open data de l'Assemblée nationale et du Sénat. Les qualifications sont saisies à la main et citent leurs
sources. Les scores en sont calculés, selon les règles 14 à 19 et 26.

## Relier les fichiers

- **Texte** : `textes.csv`, colonne `id` (dossier de l'Assemblée, `DLR5L17N…`). Dans `editorial.json`, c'est `dossier_an`. L'`id` d'une qualification (`narcotrafic`) est le `texte_id` des fichiers de scores.
- **Scrutin** : `scrutins.csv`, colonne `id` (`VTANR5L17V…`), et `senat/scrutins.csv` (`SN2024-289`).
- **Député·e** : `deputes.csv`, colonne `id` (`PA…`), nommée `acteur_id` ailleurs. Sans le préfixe `PA` dans les votes nominatifs.
- **Groupe** : `groupes.csv`, colonne `id` (`PO…`). Une `lignee` réunit les organes successifs d'un même groupe, et les scores de groupe sont par lignée (règle 19).
- **Droit** : colonne `droit` des scores, code de la grille (`libertes`, `police-justice`…) ou `global`, qui prend le droit principal de chaque texte (règle 15).

## Qualifications : `editorial.json`

Format JSON, trois listes.

- `textes` : `id`, `dossier_an`, `legislature`, `titre`, `resume`, `droits` (`code`, `role` principal ou secondaire, `sens` etend ou restreint, `sources`, `justification`), `etiquettes`, `vigilance` (`texte`, `sources`), `conseil_constitutionnel`, `note`, `sources` (clé → `auteur`, `titre`, `date`, `url`), `scrutins` (`id`, `role`, `pour`, `objet`) et, s'il y a lieu, `senat` (`version`, `scrutins`, `droits`, `etiquettes`, `vigilance`, `sources`, `note`).
- `ecartes` : `dossier_an`, `legislature`, `titre`, `motif`.
- `suivis` : fiches d'un texte avant le vote (règle 22), sans sens ni scrutin.

Rôle d'un scrutin : `decisif` et `amendement` sont comptés ; `ensemble`, `motion`, `article` et `censure` sont affichés. `pour` vaut `texte` si voter pour va dans le sens du texte, `contre-texte` sinon.

## Assemblée nationale : votes

### `textes.csv`

- `id`, `legislature`, `titre` ; `procedure`, `initiative` ; `url_an`
- `loi`, `date_loi`, `nor`, `url_loi` : loi promulguée
- `cc_decision`, `cc_sens`, `cc_url` : décision du Conseil constitutionnel
- `n_scrutins`, `n_amendements`, `n_ensemble` : décomptes
- `decisif_propose` : scrutin que le pipeline propose comme décisif (règle 9), avant toute relecture
- `premier_scrutin`, `dernier_scrutin` : dates
- `nature` : ordinaire, organique, constitutionnelle, budget, convention, resolution
- `droits_candidats`, `etiquettes_candidates`, `motifs` : présélection par mots-clés, jamais un jugement

### `scrutins.csv`

- `id`, `legislature`, `numero`, `date`, `seance`, `titre`
- `type_vote` : SPO ordinaire, SPS solennel, MOC motion de censure
- `objet` : ensemble, article_unique, article, amendement, suppression_article_unique, motion_rejet, motion_renvoi, motion_censure, partie, resolution, declaration, autre
- `sort`, `pour`, `contre`, `abstention`, `non_votants`, `votants`, `exprimes`, `requis`, `demandeur`
- `dossier_objet` : dossier indiqué par le dump ; `dossier_id` : dossier retenu ; `etape` : lecture (AN1, CMP…) ; `rattachement` : comment il a été trouvé
- `amendement_id` : lien vers `amendements.csv`

### `positions_groupes.csv`

- `scrutin_id`, `groupe_id`, `membres`, `pour`, `contre`, `abstention`, `non_votants`
- `position` : pour, contre, abstention (l'abstention l'emporte sur les deux), partage, absent (règle 12)
- `cohesion` : part des votants du groupe qui ont voté comme la position, de 0 à 1

### `amendements.csv`

- `id`, `dossier_id`, `texte_id` (texte de loi examiné), `numero`, `sous_amendement`
- `type_auteur`, `auteur_id`, `groupe_id`, `division` (article visé), `depot`, `sort`
- `discussion` : identifiant de la discussion commune ; `rang_identique` : place parmi des amendements identiques

### `deputes.csv`

- `id`, `civ`, `prenom`, `nom`, `nom_tri`

### `mandats.csv`

- `id`, `acteur_id`, `legislature`, `departement`, `num_departement`, `num_circo`, `debut`, `fin`, `cause_mandat`, `cause_fin`

### `appartenances.csv`

- `acteur_id`, `groupe_id`, `legislature`, `debut`, `fin`, `qualite`

### `groupes.csv`

- `id`, `lignee`, `legislature`, `sigle`, `nom`, `date_debut`, `date_fin`, `couleur`

### `mises_au_point.csv`

- `scrutin_id`, `acteur_id`, `position` : affichées, pas comptées (règle 13)

### `votes/<législature>/<AAAA-MM>.csv`

- `scrutin` : numéro dans la législature ; `acteur` : identifiant sans `PA` ; `position` : P pour, C contre, A abstention, N non-votant

## Assemblée nationale : scores

Colonnes communes : `votes_favorables`, `votes_defavorables`, `abstentions`, `non_votants` ; `n_textes` : textes comptés ; `score` : de 0 à 100, part pondérée des votes favorables parmi les votes comptés (règle 15), vide sans vote compté.

### `scores_scrutins.csv`

- `texte_id`, `scrutin_id`, `role` (decisif, amendement), `droit`, `droit_role`, `sens`, `poids` (règle 18)
- `favorable` : le vote favorable aux droits sur ce scrutin, pour ou contre (règle 14)

### `scores_deputes.csv`

- `acteur_id`, `droit`, et les colonnes communes

### `scores_deputes_textes.csv`

- `acteur_id`, `texte_id`, et les colonnes communes

### `scores_deputes_legislatures.csv`

- `acteur_id`, `legislature`, et les colonnes communes

### `scores_deputes_droits_legislatures.csv`

- `acteur_id`, `legislature`, `droit`, et les colonnes communes

### `scores_groupes.csv`

- `lignee`, `droit`, et les colonnes communes

### `scores_groupes_textes.csv`

- `lignee`, `texte_id`, et les colonnes communes

### `participation.csv`

- `acteur_id`, `scrutins` (scrutins comptés pendant son mandat), `votes`, `non_votants`, `taux` (en %)

## Textes en cours

Ces fichiers n'entrent dans aucun score (règle 20).

### `en_cours.csv`

- `id`, `statut`, `motif_ecart`, `titre`, `titre_dossier`, `type`, `sous_type`, `initiative`, `procedure_an`, `date_depot`
- `date_derniere_lecture`, `issue_derniere_lecture`, `date_derniere_activite`
- `attente`, `attente_etape`, `attente_chambre`, `attente_type_lecture`, `seance_inscrite`
- `legislature`, `dossier_an`, `signet_senat`, `loicod_senat`, `etat_dosleg`, `url_an`, `url_senat`, `procedure_acceleree`

### `en_cours_lectures.csv`

- `id`, `texte_id`, `dossier`, `etape`, `chambre`, `type_lecture`, `date`, `statut_code`, `statut`, `issue`, `decision_deduite`, `art_49_3`, `mode_adoption`, `scrutin_id`, `rattachement`, `decision_dosleg`

### `en_cours_evenements.csv`

- `texte_id`, `date`, `etape`, `scrutin_id`, `detail`, `type` (procédure accélérée, CMP, 49.3, saisine…)

### `en_cours_etats.csv`

- `id`, `etat` : loi, adopte (pas encore promulgué), en_navette, a_l_arret, rejete, retire, hors_navette (résolution, engagement de responsabilité), avant_vote
- `attente`, `attente_chambre`, `date_derniere_lecture`, `issue_derniere_lecture`, `date_derniere_activite`, `seance_inscrite`

### `en_cours_agenda.csv`

- `point_id`, `dossier_id`, `date`, `heure`, `instance` (seance, commission), `organe_id`, `organe`, `etat`, `type_point`, `objet`, `procedure`

### `en_cours_alertes.csv`

- `id`, `type`, `dossier_id`, `scrutin_id`, `date`, `titre`, `detail` : ce qu'un nouveau vote ou une inscription demande de relire

## Recherche et annuaire

### `termes_recherche.csv`

- `cle` (id d'une qualification ou dossier d'un écart), `type` (terme, surnom), `terme` : cherchés, jamais affichés

### `pays_circonscriptions.csv`

- `pays`, `circo`, `hors_tableau` (absent du tableau du code électoral), `alias` (séparés par `|`)

### `annuaire/codes_postaux.csv`

- `cp`, `insee`, `commune`, `circo`, `part` : part de la commune dans la circonscription, de 0 à 1

### `annuaire/contacts.csv`

- `acteur_id`, `courriel`, `site`

### `annuaire/cp_departements.csv`

- `cp`, `departement`

## Sénat

Fichiers à part, sous `senat/`, depuis juin 2017. Aucune correspondance avec les groupes de l'Assemblée (règle 28). Votes enregistrés au nom de chaque sénateur·ice, qui ne disent pas qui était présent (règle 27).

### `senat/scrutins.csv`

- `id`, `session`, `numero`, `date`, `titre`, `objet`, `sort`, `pour`, `contre`, `abstention`, `non_votants`, `votants`, `exprimes`, `requis`
- `pour_scr`, `contre_scr` : décomptes de la feuille de scrutin
- `loicod`, `signet`, `lecture`, `dossier_id`, `note`, `url`

### `senat/positions_groupes.csv`

- `scrutin_id`, `groupe_id`, `membres`, `pour`, `contre`, `abstention`, `non_votants`, `position`, `cohesion`

### `senat/senateurs.csv`

- `id`, `civ`, `prenom`, `nom`, `etat`, `type_appartenance`, `circonscription`, `departement`, `courriel`

### `senat/mandats.csv`

- `senateur_id`, `debut`, `fin`, `motif_debut`, `motif_fin`

### `senat/appartenances.csv`

- `senateur_id`, `groupe_id`, `debut`, `fin`

### `senat/groupes.csv`

- `id`, `sigle`, `nom`

### `senat/mises_au_point.csv`

- `scrutin_id`, `ordre`, `texte`, `url`

### `senat/scores_scrutins.csv`

- `texte_id`, `scrutin_id`, `role`, `droit`, `droit_role`, `sens`, `poids`, `favorable`

### `senat/scores_senateurs.csv`

- `senateur_id`, `droit`, et les colonnes communes

### `senat/scores_senateurs_periodes.csv`

- `senateur_id`, `periode` (`2017-2022` ou `depuis-2022`), `droit`, et les colonnes communes

### `senat/scores_senateurs_textes.csv`

- `senateur_id`, `texte_id`, et les colonnes communes

### `senat/scores_groupes.csv`

- `groupe_id`, `periode` (`2017-2022` ou `depuis-2022`), `droit`, et les colonnes communes

### `senat/scores_groupes_textes.csv`

- `groupe_id`, `texte_id`, et les colonnes communes

### `senat/votes/<AAAA-MM>.csv`

- `scrutin` : session-numéro ; `senateur` : matricule ; `position` : P, C, A, N ; `statut`, `delegue_a`, `mise_au_point`
