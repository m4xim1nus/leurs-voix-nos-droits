# Roadmap

Projet sans calendrier engageant. Ce fichier est le **plan opérationnel** :
il porte le cycle en cours, et seulement lui. Ce qui est livré est dans
`CHANGELOG.md`, les cycles à venir et les idées dans `BACKLOG.md`. Règles
de tenue : `CLAUDE.md`, section « Suivi ».

## Cycle en cours : Sénat

**But : montrer le second vote de chaque texte, sans toucher à ce qui existe sur
l'Assemblée.** On voit comment les groupes du Sénat ont voté sur nos textes, on y
ajoute ce que le Sénat vote seul, et chacun·e retrouve ses sénateur·ices depuis son
code postal. Le site reste d'abord celui des député·es.

### Ce que le Sénat apporte (sondage du 31/10/2026, à confirmer au build)

- **Données** : 1 336 scrutins et 464 719 votes nominatifs depuis juin 2022 ; 348
  sénateur·ices en poste, 333 courriels publics. Dosleg (`votsen`, déjà téléchargé) et
  `ODSEN_GENERAL` / `ODSEN_HISTOGROUPES` (à ajouter) suffisent.
- **Sur les 104 textes qualifiés** :
  - 33 décisifs de l'AN ont un vote du Sénat sur les conclusions de CMP, donc sur le
    même texte (4 unanimes, 29 comptables) ;
  - 22 ont pour dernier vote du Sénat une 1re ou une 2e lecture, version à vérifier ;
  - 4 finissent par une question préalable (aide à mourir : 169-164) ;
  - 8 textes adoptés par 49.3 sans vote final ont un vote du Sénat ;
  - 37 n'ont aucun scrutin public du Sénat sur l'ensemble.
- **Hors des 104** : 98 lois votées en scrutin public sur l'ensemble au Sénat, ni
  qualifiées ni écartées, dont à vue de nez une vingtaine dans le périmètre.
- **Un vote de groupe** : presque chaque scrutin enregistre un vote pour les 348 sièges,
  97 % de ces votes sont exprimés, et 99,1 % suivent la majorité du groupe (simulation
  sur 29 décisifs). Le score d'un groupe est très parlant : de 7 (Les Indépendants) à 97
  (GEST) sur cette simulation. Le score individuel en dit beaucoup moins, et une
  participation ne dirait rien de la présence.

### Décisions de Max (31/10/2026)

- **Chaque vote se lit sur le texte voté.** Même texte que le décisif de l'AN (CMP,
  conforme) : le sens est repris. Autre version : sens relu et sourcé. Sans source
  admise : vote affiché, non compté.
- **Textes votés au seul Sénat** : triés, et qualifiés s'ils entrent dans la grille. Ils
  ne comptent que dans les scores du Sénat, avec la mention « pas de vote à
  l'Assemblée ».
- **Texte voté au Sénat et attendu à l'AN** : qualifié dès le vote du Sénat, sans attendre
  l'inscription à l'AN, pendant de la règle 21. Son sens se lit sur le texte voté par le
  Sénat, avec la mention « texte encore en navette, attendu à l'Assemblée ». Il compte
  dans les scores du Sénat, jamais dans ceux de l'AN avant un vote de l'AN. Après ce vote,
  chaque chambre garde son décisif, chacun lu sur son texte. Premier cas :
  casseurs-payeurs (229-105 le 27/10/2026), qui ne passe donc pas par une fiche de suivi.
- **Scores du Sénat** : décisif seul, pas d'amendements clés. Un texte adopté par 49.3 à
  l'AN compte au Sénat s'il y a eu un vote sur l'ensemble. Abstentions et non-votants
  hors calcul, position de groupe inchangée (règle 12). Motions affichées, non comptées,
  question préalable comprise. Décisif sans voix d'un côté affiché, non compté.
- **Sénateur·ices** : fiche avec un score « d'après les votes enregistrés à son nom »,
  écarts au groupe mis en avant, **aucun taux de participation**, explication du vote de
  groupe. Les groupes passent en tête de la page Sénat.

### Garde-fous

- **Accueil inchangé** (Max, 31/10/2026) : titre, introduction, recherche et contenus
  restent ceux de l'AN et des député·es, sans bloc ni phrase sur le Sénat. Le Sénat est
  accessible, pas mis au même niveau : une entrée de menu, un lien depuis les fiches.
- `scores_*.csv` et `participation.csv` de l'AN restent identiques à l'octet après
  l'ajout du Sénat : un test le vérifie. Les exports du Sénat sont des fichiers à part.
- `editorial.json` : ajout optionnel, comme `suivis`. Le format reste 1, et le fichier
  ne change d'aucun octet tant qu'aucune donnée du Sénat n'y est saisie.
- Aucun score ne mélange les deux chambres. Aucune comparaison de score entre un·e
  député·e et un·e sénateur·ice : les textes comptés diffèrent.
- Pas de correspondance entre les groupes des deux chambres : côte à côte, chacun sous
  son sigle, sans jugement de famille politique.
- Mêmes règles dures qu'à l'AN : open data officiel, source à côté du jugement, sources
  exclues refusées par `lvnd check` et l'admin.

### Le travail

**1. Données.** `lvnd` lit les votes nominatifs, les sénateur·ices et leurs groupes
datés (lignées dans `groupes.yaml`), et rattache chaque scrutin à son dossier AN par le
signet. Exports : votes mensuels versionnés, positions de groupe, sénateur·ices, annuaire
(code postal → département → sénateur·ices, courriels). La passe quotidienne et ses
garde-fous couvrent ces données. Contrôle croisé des ventilations avec les pages de
senat.fr, sur un échantillon. Les notes `scrbaspag` (erreurs matérielles) s'affichent
sans changer le décompte (règle 13). `senmatdel` et `votsenmar` sont à lire et à
documenter dans `docs/SOURCES.md`. Date de référence : le dump du jour, pas celui de
quifaitlaloi.

*Fait (31/10/2026) : `data/export/senat/`, `data/annuaire/cp_departements.csv`, contrôles de `lvnd check`, passe
quotidienne et son garde-fou, contrôle croisé sur 70 pages, `docs/SOURCES.md` (section « Votes du Sénat »). Un
élément reste à vérifier sur une vraie passe : le workflow quotidien, qui n'a pas encore tourné avec ces données.*

**2. Méthode et qualification.** Écrire les décisions ci-dessus en règles numérotées, et
faire valider par Max, avant toute publication :

- leur rédaction ;
- la période du score, sans législature au Sénat (proposition : depuis juin 2022, une
  seule période, un·e élu·e de 2026 affichant le peu de votes qu'il ou elle a) ;
- la mention pour un vote du Sénat sur un texte encore en navette (règle 21) ;
- la phrase publique sur le vote de groupe, après vérification de la pratique en vigueur
  (règlement du Sénat, sources officielles) : la seule source lue, Public Sénat, date
  d'avril 2025.

Ensuite, par le circuit de `docs/QUALIFICATION.md` : les textes de même version (reprise
du sens, vérifiée texte par texte), les versions différentes (relues et sourcées), le tri
des 98 lois, et les textes retenus, dont casseurs-payeurs. Celui-ci part du brouillon de
`source/brouillons-suivi-attente/`, à reprendre après lecture du texte adopté par le Sénat,
que ce brouillon n'a pas lu. Vérifier à la main chaque décisif proposé : le
classement automatique des scrutins n'est pas assez sûr pour décider seul.

*Fait (31/10/2026) : règles 23 à 28 validées par Max, 15 scrutins sans fiche rétablis (`referentiels/scrutins_senat.yaml`),
qualifications décidées par Max le même jour (fiche `source/relecture-senat.md`). Sur les 104 textes publiés : 55 votes
comptés, 12 affichés, 37 sans scrutin public du Sénat ni motion. Sur les 78 votés au Sénat : 21 comptés, 7 affichés sans
jugement, 49 écartés, et les ingérences étrangères (340-0), dont la fiche de suivi attend l'inscription à l'AN. Soit 76
décisifs. Rien n'est encore dans D1 : voir le début de l'étape 3.*

**3. Admin et site.**

- **Charger les décisions de l'étape 2.** Les brouillons sont dans `source/brouillons-senat-meme/`, `-versions/` et `-tri/`,
  et `source/outils/controle_senat.py` les contrôle. À prévoir :
  - le bloc `senat` dans `editorial.normaliser` et son pendant de l'admin, au même octet, absent quand il est vide ;
  - les YAML de `-meme` et `-versions` ne portent que `id`, `dossier_an` et `senat` : ils complètent le document publié, sans le
    remplacer, alors que `sync-admin --valider` remplace aujourd'hui tout le document ;
  - `valider` accepte un texte sans décisif de l'AN (`version: seul`) et un vote affiché sans droits ni sens ;
  - les textes de `-tri` absents de `textes.csv` (sans scrutin à l'AN) entrent au catalogue et dans `en_cours_etats` ;
  - validation : `--valider "validé par Max (Sénat, 31/10/2026)"`, puis « Publier » par Max. Les écarts ne passent que si le
    texte n'est pas déjà publié.
- **Scores du Sénat** (règle 26) : fichiers à part, dans `data/export/senat/`.
- **Admin** : scrutins et décisif du Sénat sur la fiche, contrôles identiques à
  `lvnd check` (test croisé à l'octet), aperçu des scores, textes sans dossier retenu à
  l'AN. Alerte, dans `lvnd check` et « À traiter », quand un texte est voté en scrutin
  public au Sénat sans être ni qualifié ni écarté, comme `premier_decisif` à l'AN.
- **Fiche texte** : l'AN d'abord, puis le vote du Sénat, groupes côte à côte, avec la
  version sur laquelle il porte ; « pas de scrutin public au Sénat » quand c'est le cas.
- **Sénat** : une page avec les groupes et leurs scores, droit par droit ; une fiche par
  sénateur·ice (département, groupes successifs, score, votes, écarts au groupe,
  « Lui écrire »).
- **Code postal** : le parcours de l'accueil ne change pas, il mène à la fiche du ou de
  la député·e. Cette fiche renvoie aux sénateur·ices du département, et la page Sénat a sa
  propre recherche par code postal.
- **Pages à revoir** : `/en-cours` (dernier vote du Sénat), `/textes` (filtre de chambre
  pour les textes du seul Sénat), méthodologie (la phrase « pas encore couverts » tombe),
  données, et le menu (entrée « Sénat », après celles de l'AN). La recherche par nom de
  l'accueil trouve aussi les sénateur·ices, signalé·es comme tel·les dans les résultats,
  sans changer son libellé.
- **Comparer** : deux sénateur·ices ou deux groupes du Sénat si l'existant s'y prête sans
  détour ; jamais d'une chambre à l'autre.

*Fait (31/10/2026, non commité ni déployé) : bloc `senat` à l'octet dans le pipeline et l'admin, chargement par complément, contrôles
croisés, migration `0004_senat.sql`, catalogue étendu aux dossiers votés au Sénat, alertes, scores à part (76 décisifs, chiffres
identiques à la simulation de la relecture), fiche admin et aperçu, fiche texte, pages `/senat` et `/senat/<slug>`, recherche, `/textes`,
`/en-cours`, méthodologie, données, menu. Accueil, `/groupes` et droits identiques avec et sans les données du Sénat, hors menu et pied de
page. Comparer n'est pas étendu au Sénat : l'existant ne s'y prête pas sans détour. Reste : migration en ligne, déploiement de l'admin,
validation dans D1, « Publier » par Max.*

### Hors cycle

Amendements clés du Sénat (environ 31 suppressions hors budgets et retraites, sur 16
textes), cartes partageables des sénateur·ices, correspondance entre groupes des deux
chambres, XVe législature.

### Terminé quand

- Les scores de l'AN sont identiques à l'octet, la CI est verte, `lvnd check` couvre le
  Sénat.
- Chaque texte qualifié dit ce que le Sénat a fait : vote compté, vote affiché, pas de
  scrutin public, pas encore examiné.
- Les 98 lois sont triées, les textes retenus qualifiés et publiés, casseurs-payeurs
  compris.
- Les règles sont validées, publiées sur la page Méthodologie, et le vote de groupe y est
  expliqué en clair.
- Un·e visiteur·se trouve ses sénateur·ices depuis la fiche de son ou sa député·e et par
  code postal sur la page Sénat, sur téléphone compris. L'accueil n'a pas changé.
