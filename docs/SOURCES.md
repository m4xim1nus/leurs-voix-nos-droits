# Sources

Fiche des sources de données de Leurs voix, nos droits, établie au spike de
l'étape 1 (téléchargements du 29/10/2026). Scripts d'exploration :
`pipeline/explo/`.

## Verdict : GO côté données (29/10/2026)

L'open data AN suffit pour la v1. La grille v0 et les règles qui en
découlent ont été validées par Max le 29/10/2026 (`docs/METHODO.md`).

- **Votes** : 1,97 M votes nominatifs (XVIe + XVIIe), soit 1,4 à 33 Mo
  selon le format. Tout versionner est faisable.
- **Rattachement** : 99,9 % des scrutins sur amendement de la XVIIe sont
  rattachés à leur amendement, avec dossier, auteur et groupe.
- **Contrôle croisé** : ventilations identiques à celles de leurs-votes.fr
  sur 22 531 paires scrutin × groupe. Positions conformes à datan.fr sur
  l'échantillon. Les écarts viennent tous de la règle de position, pas des
  données.
- **Code postal** : pas de table officielle directe. Elle se construit
  depuis des sources officielles, et 71 % des électeurs ont un député
  unique par code postal.
- **Conseil constitutionnel et JO** : présents dans les dossiers AN. PISTE
  n'est pas nécessaire.
- **Textes témoins** : les six se retrouvent dans les dumps, de 3 scrutins
  (immigration) à 931 (aide à mourir), et leur qualification sourcée
  recoupe les dossiers AN (`explo/verifier_temoins.py`).

## Inventaire

| Source | URL | Volume (zip → brut) | Rôle |
|---|---|---|---|
| Scrutins AN XVIIe | `data.assemblee-nationale.fr/static/openData/repository/17/loi/scrutins/Scrutins.json.zip` | 28 Mo → 224 Mo, 9 200 scrutins | votes nominatifs, ventilés par groupe |
| Scrutins AN XVIe | `…/16/loi/scrutins/Scrutins.json.zip` | 10 Mo → 83 Mo, 4 105 scrutins (figé le 28/06/2024) | idem |
| Dossiers législatifs AN XVIIe, XVIe | `…/{17,16}/loi/dossiers_legislatifs/Dossiers_Legislatifs.json.zip` | 11 + 9 Mo → 70 + 57 Mo | chaîne des actes, Conseil constitutionnel, promulgation |
| Amendements AN XVIIe | `…/17/loi/amendements_div_legis/Amendements.json.zip` | 348 Mo → 1,6 Go, 142 579 fichiers | auteur, groupe de l'auteur, dossier, séance |
| Amendements AN XVIe | `…/16/loi/amendements_div_legis/Amendements.json.zip` | 363 Mo (figé le 28/06/2024) | idem |
| Acteurs et organes AN (historique) | `…/17/amo/tous_acteurs_mandats_organes_xi_legislature/AMO30_tous_acteurs_tous_mandats_tous_organes_historique.json.zip` | 14 Mo | sigles des groupes, mandats, circonscriptions |
| Scrutins AN XVe | `…/15/loi/scrutins/Scrutins_XV.json.zip` | 9 Mo → 72 Mo, 4 417 scrutins (figé le 09/06/2022) | idem |
| Dossiers législatifs AN XVe | `…/15/loi/dossiers_legislatifs/Dossiers_Legislatifs_XV.json.zip` | 15 Mo → 94 Mo, 4 980 dossiers (figé le 09/06/2022) | idem |
| Dossiers législatifs AN XIVe | `…/14/loi/dossiers_legislatifs/Dossiers_Legislatifs_XIV.json.zip` | 2,6 Mo, un seul fichier JSON | les 11 dossiers ouverts avant juin 2017 et votés en XVe |
| Amendements AN XVe | `…/15/loi/amendements_legis/Amendements_XV.json.zip` | 649 Mo (figé le 09/06/2022) ; serveur bridé, plan B | auteur, groupe de l'auteur, dossier, séance |
| Agenda de l'AN | `…/17/vp/reunions/Agenda.json.zip` | 8,6 Mo → 42 Mo, 8 174 réunions (quotidien) | points de séance et de commission à venir (`lvnd/agenda.py`) |
| Dosleg (Sénat) | `data.senat.fr/data/dosleg/dosleg.zip` | 16 Mo → 122 Mo (quotidien) | décisions de séance, séances, activité et état des dossiers ; scrutins publics et votes nominatifs (`lvnd/senat.py`) |
| Sénateurs (Sénat) | `data.senat.fr/data/senateurs/ODSEN_GENERAL.csv` | 0,4 Mo (quotidien) | identité, circonscription, courriel public, groupe actuel |
| Groupes des sénateurs | `…/ODSEN_HISTOGROUPES.csv` | 0,6 Mo (quotidien) | appartenances datées |
| Mandats des sénateurs | `…/ODSEN_ELUSEN.csv` | 0,5 Mo (quotidien) | mandats datés |

`lvnd download` (`pipeline/lvnd/sources.py`, repris de quifaitlaloi)
télécharge et extrait ces dumps dans `data/raw/` et tient un manifeste
(URL, `Last-Modified`, taille, sha256). Le serveur de l'AN, derrière un
CDN (OVH), coupe souvent la connexion au milieu des dumps d'amendements.
Une reprise d'un seul tenant (`Range: bytes=N-`) renvoie ensuite `206`
sans aucun octet, plusieurs fois de suite, alors qu'un bloc de 1 Mio
demandé à la même position finit par être servi. Après une coupure,
`download` continue donc par blocs, et reprend un fichier partiel d'un
lancement à l'autre (`If-Range` garantit que le fichier n'a pas changé).
Le service est intermittent : depuis le 29/10/2026 vers 18 h, ce serveur ne
sert plus aucune plage au-delà d'environ 1 Mo sur les dumps d'amendements.

**Plan B des amendements** (`pipeline/lvnd/secours.py`). Après 20 minutes sans
aucun octet, et s'il n'existe pas d'archive plus ancienne, `download` récupère
un à un les amendements mis aux voix sur le site de l'AN, autre serveur
officiel (`www.assemblee-nationale.fr/dyn/opendata/<uid>.json`), au même
format. Le manifeste note `mode: secours`, et chaque lancement suivant retente
le dump, qui remplace tout. Les scrutins, dossiers et acteurs n'ont pas
d'équivalent à l'unité (404 ou 500 sur les identifiants testés).

**Limite** : ni les amendements identiques, que rien ne permet de lister sans
le dump, ni les amendements non mis aux voix. Les scores n'en dépendent pas et
le site n'affiche que les amendements votés ; seul `amendements.csv` est
moins complet.

## Votes nominatifs : volume et stockage

`explo/volume_votes.py` :

| | Scrutins | Votes nominatifs | Députés |
|---|---|---|---|
| XVIe | 4 105 | 602 911 | 617 |
| XVIIe (au 28/10/2026) | 9 200 | 1 369 581 | 652 |
| **Total** | 13 305 | **1 972 492** | |

Les « votes nominatifs » sont les pour, contre, abstentions et non-votants
déclarés. Les absents n'y figurent pas : on les obtient par différence avec
l'effectif du groupe (`nombreMembresGroupe`).

Taille de l'ensemble selon le format (identifiants entiers) :

| Format | Taille |
|---|---|
| CSV brut | 33,5 Mo |
| CSV gzip | 6,0 Mo |
| Parquet zstd | 1,4 Mo |
| SQLite (`without rowid`) | 27,7 Mo |
| JSON, une ligne par scrutin et position | 14,5 Mo (1,5 Mo gzip) |

**Décision (validée par Max le 29/10/2026)** : versionner *tous* les votes
nominatifs, en CSV compact (identifiants entiers, trié), un fichier par
législature et par mois (`data/export/votes/17/2026-10.csv`, environ
0,7 Mo).

- Le build du site peut alors calculer le score de n'importe quel scrutin
  qualifié dans l'admin, sans relancer le pipeline. C'est le critère fixé.
- Un fichier par mois garde des diffs git courts : une mise à jour ne
  touche que le mois en cours, et la XVIe est figée.
- Le stockage git reste modeste : environ 6 Mo compressés pour l'ensemble.

En revanche, `data/lvnd.sqlite` n'est pas versionné. Ce fichier binaire de 28 Mo serait réécrit à chaque build, et
l'historique du dépôt gonflerait vite. La base se régénère en local depuis
l'export. Le Parquet (1,4 Mo) est plus compact, mais binaire lui aussi :
diffs illisibles, et une bibliothèque de plus côté Node.

Les **mises au point** (un député déclare après coup qu'il voulait voter
autrement) sont publiées à part (`miseAuPoint`). Elles ne modifient pas le
résultat officiel : 1 904 en XVIe, 3 295 en XVIIe (le spike en comptait
moins, faute de lire les blocs rangés en liste). Elles sont affichées, pas
comptées (`docs/METHODO.md`).

## Rattachement des scrutins sur amendement

`explo/rattachement_amendements.py`. Le scrutin ne donne que son intitulé
(« l'amendement n° 1762 de M. Le Coq … à l'article 2 du projet de loi de
finances pour 2025 »). Le lien `objet.dossierLegislatif` n'existe qu'à
partir de mars 2026 : c'est la même limite que pour les scrutins de
lecture dans quifaitlaloi. Les amendements, eux, sont rangés par dossier
(`json/<dossier>/<texte>/<amendement>.json`). Chacun porte son auteur
(`acteurRef`), le groupe de l'auteur au dépôt (`groupePolitiqueRef`) et,
une fois sur deux, sa séance de discussion (`seanceDiscussionRef`).

Règle, dans l'ordre :

1. même séance (`seanceRef` du scrutin = `seanceDiscussionRef` de
   l'amendement) et même numéro ;
2. sinon : même numéro, amendement de séance publique déposé dans les
   120 jours avant le scrutin, nom de l'auteur de l'intitulé présent parmi
   les signataires. Si plusieurs dossiers restent en lice, on garde celui
   dont le titre ressemble le plus à l'intitulé.

Pièges de l'intitulé :

- au PLF, les amendements sont numérotés `I-1762` (première partie) dans le
  dump, mais « n° 1762 » dans l'intitulé du scrutin : on les indexe sous les
  deux formes ;
- les variantes sont nombreuses (« l'amendement de suppression n° », « de
  rétablissement », « (2ème rect.) », « n°17 » sans espace, et même la
  coquille « n° de 2102 »).

XVIIe :

| | Scrutins | Part |
|---|---|---|
| Scrutins sur amendement ou sous-amendement | 7 897 | |
| 1. séance + numéro | 7 424 | 94,0 % |
| 2. numéro + auteur + date | 468 | 5,9 % |
| non rattachés | 5 | 0,1 % |
| **Rattachés** | **7 892** | **99,9 %** |
| dont auteur député, avec son groupe | 7 613 | |
| dont amendements du Gouvernement | 279 | |
| dont désaccords avec `objet.dossierLegislatif` | 19 | |

Les 19 désaccords viennent de dossiers rapprochés ou fusionnés à l'AN : un
amendement est rangé sous un dossier, et le scrutin pointe vers l'autre.
Quand `objet.dossierLegislatif` existe, il prime. Le dump range aussi
170 amendements sous un dossier nommé `incorrect_data`. On les rattache
quand même, par leur texte (`texteLegislatifRef`).

Le scrutin qui porte sur « l'amendement n° X et les amendements identiques
suivants » est rattaché au premier amendement, donc à son seul auteur. Les
auteurs des amendements identiques, souvent d'autres groupes, se
retrouvent par `discussionIdentique` (même discussion, même texte) :
l'export `amendements.csv` contient les amendements mis aux voix et leurs
identiques.

**Mesure sur la XVIe (30/10/2026), par le plan B** : 3 159 scrutins sur
amendement rattachés sur 3 173 (99,6 %), en 6 036 requêtes. Faute de dump pour
référence, contrôle par l'article nommé dans l'intitulé et le sort du vote :
9 articles différents sur 2 712 comparables (0,33 %) et aucun sort différent sur
3 152, contre 0,45 % et 0,09 % en XVIIe avec le dump. Six scrutins gagnent un
dossier, aucun n'en change.

XVIe : *mesure en attente*. Le serveur de l'AN coupe sans cesse le
téléchargement du dump (363 Mo) : 10, 18, 161 puis 14 Mo reçus selon les
essais, avec des reprises qui renvoient `206` sans aucun octet. Le format
est le même que pour la XVIIe.

## Rattachement des scrutins aux dossiers (étape 2)

`lvnd/textes.py`. Le dossier d'un scrutin se lit, dans l'ordre :

1. `objet.dossierLegislatif` (depuis mars 2026) ;
2. `voteRefs` d'une décision du dossier (rare : 260 scrutins de la XVIIe
   sur 9 200). Une motion de censure citée à la fois par le texte et par son
   engagement de responsabilité va à l'engagement, dossier sans mesure propre ;
   le texte qualifié l'affiche avec le rôle `censure` ;
3. l'amendement mis aux voix, sauf s'il est contredit par le référentiel, ou
   par un autre dossier débattu ce jour-là dont le titre est nettement plus
   proche : le même numéro existe dans un autre texte, l'amendement est refusé ;
4. la séance du scrutin, parmi les dossiers qui y sont débattus. Quand
   plusieurs dossiers partagent la séance, on départage par le titre (au
   moins la moitié des mots significatifs) et par la mention « loi
   organique ».

XVIIe : 9 195 scrutins rattachés sur 9 200 (99,9 %). Pour les six textes
témoins, le scrutin décisif proposé (dernier vote de l'AN sur l'ensemble)
est celui que la qualification retient.

## Dosleg : où en est un texte au Sénat

`lvnd/senat.py`, adapté de quifaitlaloi. Le dump est un SQL PostgreSQL
(`dosleg.sql`), lu table par table en 1,3 s. Au 30/10/2026 : 12 495 dossiers,
6 561 décisions de séance, 7 214 séances, 1 321 scrutins publics depuis la
XVIe.

Il sert parce que le dossier AN enregistre les décisions du Sénat avec
retard : casseurs-payeurs, voté le 27/10/2026, n'y figurait pas le 28/10.
On lit, pour une lecture du Sénat sans décision dans le dossier AN : le texte
adopté ou rejeté en séance (table `oritxt`), à défaut le décompte du scrutin
public de la même lecture.

Le statut des décisions du Sénat dans le dossier AN n'est pas
toujours fiable (« modifié » pour un texte voté conforme) : l'adoption
définitive se lit aussi dans Dosleg (`oritxtado = D`).

## Votes du Sénat

`lvnd build` écrit `data/export/senat/`, à part des exports de l'AN, que rien de
ce dossier n'alimente : `scrutins`, `positions_groupes`, `senateurs`, `groupes`,
`appartenances`, `mandats`, `mises_au_point`, et les votes
`votes/<AAAA-MM>.csv`. `lvnd annuaire` y ajoute
`data/annuaire/cp_departements.csv` (code postal → département). Aucun score
n'est encore calculé. Au 01/11/2026, depuis le 27/06/2017 : 2 243 scrutins,
780 054 votes, 746 sénateur·ices dont 348 en poste
(`Non public` n'est pas exporté).

**Scrutins sans fiche.** 26 scrutins depuis 2017 ont leurs votes dans `votsen` et
pas de ligne dans `scr`, dont le vote sur l'ensemble des lois de finances pour
2020, 2023, 2024, 2025 et 2026 (SN2019-59, SN2022-94, SN2023-98, SN2024-175, SN2025-125). Le
contrôle croisé du 31/10/2026, parti de `scr`, ne pouvait pas les voir. Leur date
et leur intitulé sont lus sur senat.fr et rangés dans
`referentiels/scrutins_senat.yaml` ; leurs votes restent ceux de Dosleg. `lvnd check`
signale tout nouveau cas par un `AVERTISSEMENT`.

**Table `votsen`.** Une ligne par siège et par scrutin (347 ou 348 lignes), sans
doublon, toutes dans un mandat de `ODSEN_ELUSEN`.

- `posvotcod` : 1 pour, 2 contre, 3 abstention, 4 non-votant.
- `stavotidt` (table `stavot`) : exporté en clair dans `statut`, s'il y en a un.
  Président·e de séance (1 321 lignes, dont 39 avec une position), membre du
  gouvernement (228), déport (1).
- `senmatdel` : **délégation de vote** (ordonnance n° 58-1066). La colonne est
  portée par la ligne de celui ou celle qui **reçoit** la délégation et nomme
  celui ou celle qui l'a donnée : la page de SN2022-51 donne « Joël Labbé à
  Thomas Dossus », et `senmatdel` = Labbé est sur la ligne de Dossus. L'export
  renverse le lien : `delegue_a` est sur la ligne de Labbé et nomme Dossus. Les
  1 680 délégations portent sur 35 scrutins.
- `votsenmar` : `*` (1 675 lignes, 334 scrutins) reprend l'étoile de la liste
  officielle : le ou la sénateur·ice a fait une mise au point. 333 de ces
  scrutins ont un texte dans `corscr`, le dernier (SN2022-131) dans `scrbaspag`.
  Valeur vide sur 5 lignes, sans étoile sur la page : ignorée.
- `corscr` (mises au point, 591 lignes) et `scrbaspag` (erreur matérielle : une
  seule depuis 2022, SN2022-131) sont exportés tels quels. Ils ne changent aucun
  décompte (règle 13).

**Décompte : la liste nominative, pas la table `scr`.** Sur 206 scrutins, `scr` s'écarte de
`votsen` d'une ou deux voix : 197 entre 2017 et 2021, surtout de 2017 à 2019, et 9 depuis (SN2024-93,
SN2024-196, SN2025-25, -26, -27, -28, -56, -232 et -293). La page de senat.fr donne chaque fois le chiffre de
la liste nominative (SN2024-93 : 115-205, `scr` 114-206). L'export compte donc
sur `votsen` et garde `pour_scr` et `contre_scr` pour la trace. Aucun de ces
écarts ne change le sort du scrutin, ce que `lvnd check` vérifie. `senat.scrutins`,
qui ne sert qu'à dater une décision du Sénat pour les textes en cours, reste sur
`scr`.

**Groupes.** `ODSEN_HISTOGROUPES`, à la date du vote. Le code reste le même
quand le groupe change de nom (`UMP`, `SOC`, `UC`, `LREM`, `RTLI`, `CRC`…), donc
pas de lignée à déclarer (`referentiels/groupes.yaml`). Le fichier ne donne que le
nom actuel. Le sigle affiché est lu sur les membres en poste (`ODSEN_GENERAL`).
`AUCUN`, quelques jours après un renouvellement (179 lignes du 01 au 04/10/2026),
n'est ni un groupe ni le groupe des non-inscrits (`NI`) : il est retiré, et les
périodes qu'il coupe sont réunies. Aucun vote ne tombe dans ces jours-là. Une fin
d'appartenance postérieure au dump est une erreur de saisie (Fouassin, 27/11/2029) :
la période reste en cours. UNT, créé le 05/10/2026, ne continue aucun groupe.
Le groupe écologiste (`ECO`) se dissout le 29/06/2017, sans vote après cette date. Hervé Poher n'a plus
d'appartenance dans le fichier jusqu'à la fin de son mandat, le 01/10/2017, alors que les pages des
scrutins le rangent au groupe socialiste : période ajoutée dans `senat.APPARTENANCES_MANQUANTES`.

**Contrôle croisé** (`explo/controle_senat.py`, 31/10/2026) : 70 pages de senat.fr
(les 9 écarts, SN2022-131, 60 scrutins tirés au sort dont 30 sur l'ensemble) :
totaux et 635 lignes scrutin × groupe, **aucun écart**. Toutes les délégations de
SN2022-51 ont aussi été comparées à la page.
Le 01/11/2026, pour 2017-2022 : 247 pages (les 197 écarts, une note, 60 tirés au sort dont 30 sur
l'ensemble), totaux et 1 979 lignes scrutin × groupe, **aucun écart** une fois Hervé Poher rattaché.
Le libellé « La République En Marche », sans « Groupe », a été ajouté au lecteur de pages.

**Rattachement** : scrutin → `date_seance` → lecture → `loi` → signet → dossier AN
(`senatChemin`), à défaut la date de la loi (`parcours.classer`). Un dossier du
Sénat peut correspondre à plusieurs dossiers AN : on retient la loi, puis le plus
avancé (`parcours.dossier_par_loi`). 2 181 scrutins sur 2 243 sont rattachés. Depuis 2022, les
34 autres : 4 déclarations du Gouvernement, 25 sur des résolutions (`ppr…`) ou une motion, et 5 sur `pjl25-801`,
en 1re lecture le 07/07/2026, sans dossier à l'AN au 31/10/2026.

**Classement des scrutins** : `objet` reprend `texte.objet_scrutin`, non vérifié au
Sénat texte par texte. Il ne suffit pas à désigner un décisif (`ROADMAP.md`).

## État de chaque texte

`lvnd/parcours.py` et `lvnd/encours.py`, adaptés de quifaitlaloi
(`docs/METHODO.md` §17 de ce dépôt-là). Le dossier AN sert d'ossature ; Dosleg
complète les décisions du Sénat, les séances et l'état des dossiers. Trois
fichiers suivent le périmètre de quifaitlaloi (voté en séance depuis le début
de la XVIIe, ni promulgué ni adopté définitivement), un quatrième couvre tout
le catalogue :

| Export | Contenu |
|---|---|
| `en_cours.csv` | textes en cours, et écartés avec leur `motif_ecart` (pour l'audit) |
| `en_cours_lectures.csv` | leurs lectures votées : issue, scrutin décisif à l'AN, mode |
| `en_cours_evenements.csv` | procédure accélérée, 49.3, CMP, saisine du Conseil constitutionnel… |
| `en_cours_etats.csv` | un état par texte du catalogue, y compris la XVIe |

`etat` vaut : `loi` ; `adopte` (pas encore promulgué) ; `en_navette`, avec
`attente` et `attente_chambre` ; `avant_vote` (aucune lecture conclue en
séance) ; `hors_navette` (résolution, engagement de la responsabilité : aucune
lecture) ; `a_l_arret` (aucun acte depuis 12 mois) ; `rejete` ; `retire` ;
`caduc` ; `fusionne`. La date de référence est celle du téléchargement du dump
des dossiers de la XVIIe (`meta.json`, `en_cours.date_reference`) : le build
reste reproductible.

Ces fichiers n'entrent dans aucun score : après leur ajout, `scores_*.csv`,
`participation.csv`, `scrutins.csv` et `textes.csv` sont restés identiques à
l'octet.

Au 29/10/2026 : 127 textes en cours, 48 écartés à l'arrêt, 30 rejetés. Sur
les 96 textes qualifiés : 69 lois, 11 en navette, 8 à l'arrêt, 6 retirés,
2 rejetés.

**Contrôle croisé** avec l'export de quifaitlaloi du 28/10/2026 : mêmes motifs
d'écart et, à l'AN, mêmes scrutins décisifs et mêmes modes sur les 204 textes
communs. Les écarts tiennent au dump plus récent d'un jour : un texte voté le
29/10 (accord UE-Vietnam), deux étapes ouvertes depuis, une séance du Sénat
passée à la suivante.

**Agenda de l'AN** (`lvnd/agenda.py`, `en_cours_agenda.csv`). Une ligne par
point de séance ou de commission à venir et par dossier. On écarte les réunions
et les points annulés ou supprimés, ainsi que les réunions d'initiative
parlementaire (colloques, groupes d'études) et les points sans dossier. `etat`
vaut `confirme` ou `eventuel`, et un point confirmé dans une réunion éventuelle
reste éventuel. Au 30/10/2026 : 102 points, jusqu'au 25/11 (horizon d'environ
trois semaines en séance), sur 16 dossiers en séance.

Le mot est **« inscrit »**, jamais « sera voté » : sept textes sont inscrits le
seul 19/11/2026, et une niche ne les examine pas toujours tous. `seance_inscrite`
donne la première séance à venir, dans l'agenda, le dossier AN ou Dosleg. Une
date d'agenda compte aussi comme activité pour la règle des 12 mois.

**Catalogue élargi.** `textes.csv` et D1 reçoivent aussi les textes en cours
ou inscrits sans scrutin public à l'AN : 82 au 30/10/2026, sur 561 textes
(`n_scrutins` à 0, `decisif_propose` vide), dont casseurs-payeurs. Les 479
lignes précédentes sont inchangées.

- `lvnd check` : aucun effet sur les témoins ni sur les qualifications ; un
  contrôle vérifie qu'aucun texte qualifié n'est sans scrutin.
- Admin : le filtre par défaut n'affiche que les textes avec au moins un
  scrutin public (ou déjà saisis), car les autres n'ont rien à qualifier ; le
  nouveau filtre « Scrutin public à l'AN » les montre.
- Site : aucun effet, il ne lit le catalogue que pour les textes qualifiés ou
  écartés.
- `sync-admin` : 82 lignes de plus au premier sync incrémental, 0 ensuite à
  export égal.

**Alertes** (`lvnd/alertes.py`, `en_cours_alertes.csv`). Des avertissements,
affichés par `lvnd check` et par la file « À traiter » de l'admin. Ils ne font
jamais échouer le contrôle : un nouveau vote ne doit pas bloquer l'Action.

| Type | Quand | Au 30/10/2026 |
|---|---|---|
| `vote_posterieur` | vote sur l'ensemble après le décisif (ou la motion de censure) retenu d'un texte qualifié ; sans l'un ni l'autre (texte qualifié sur le vote du Sénat), après son dernier scrutin retenu, ou tout vote sur l'ensemble s'il n'en retient aucun à l'AN | 0 |
| `lecture_posterieure` | lecture de l'AN close après ce même repère sans scrutin public sur l'ensemble (main levée, motion de rejet), sur un texte qualifié, tant que la qualification ne retient pas son scrutin et que sa note n'en cite pas la date | 2 (02/11/2026) |
| `unanimite_contestee` | texte écarté pour unanimité dont le décisif proposé a des voix des deux côtés | 0 |
| `ecart_revote` | texte écarté pour un autre motif, revoté à l'AN après le 01/11/2026, sans que son motif cite ce vote | 0 |
| `premier_decisif` | décisif proposé sur un texte ni qualifié ni écarté | 0 |
| `vote_sans_decisif` | lecture de l'AN close sans décisif proposé sur un texte ni qualifié, ni écarté, ni à l'arrêt : rejet d'une partie, vote sans scrutin public | 3 (01/11/2026) |
| `inscrit` | texte ni qualifié ni écarté, inscrit **en séance** (pas en commission) | 14 |

L'admin retire ce que D1 a déjà pris en compte, même avant publication : une
saisie sur le texte, le scrutin retenu dans sa qualification, ou la fin de son
écart.

Limites, reprises de quifaitlaloi : un texte voté au Sénat sans dossier AN n'est
pas dans ces exports (ses votes sont dans `senat/scrutins.csv`, sans `dossier_id`) ; `transmis` se déduit de la Constitution, pas d'un acte ; un
texte adopté conforme par la seconde chambre peut rester quelques jours « en
navette ». Les lectures du Sénat n'ont ni scrutin ni mode (`NON_RENSEIGNE`) :
ses votes sont dans `data/export/senat/`. Les 49.3 de la XVIe n'ont pas de scrutin miroir
ici (motions sans `voteRefs`) : leur mode reste `ART_49_3`.

## Build local et exports

`lvnd build` est déterministe : sur les dumps qui ont produit les exports versionnés, il les redonne à l'octet près, sauf
`meta.json` (vérifié le 01/11/2026 sur les 97 fichiers de votes et le reste). Les écarts viennent donc de `data/raw/`, dont la
date diffère de celle du cache de la CI. Cette différence est normale : aucun code ne la corrige. Pour ne changer qu'une partie
des exports :

1. `lvnd download --leger`, pour rapprocher `data/raw/` de la CI, puis `lvnd build` et `lvnd check` ;
2. `git diff --stat data/export/` : l'écart doit s'expliquer par le changement voulu et par les votes parus depuis la dernière passe ;
3. commiter en nommant les fichiers voulus, puis `git restore data/export/` pour le reste, `meta.json` compris : la passe
   quotidienne suivante rattrape les données du jour.

Tout écart sur `scores_*.csv` ou `participation.csv` sans qualification nouvelle est à comprendre avant de commiter.

## Mise à jour : passe quotidienne et données figées

Deux Actions. `donnees-quotidien.yml` (chaque jour, 5 h UTC) rafraîchit les dossiers
de la XVIIe, ses scrutins, l'agenda et Dosleg avec `lvnd download --leger`. Les autres archives
viennent du cache de l'Action, ou de la release `donnees-figees` si elles manquent, sans attendre le dump de l'AN. `donnees.yml` (lundi) rafraîchit le reste ; si un dump
d'amendements est injoignable, l'archive précédente sert, sans échec ; à défaut, voir
ci-dessous.

**Amendements de la XVIe.** Le dump de l'AN reste bloqué depuis le 29/10/2026. Le
résultat du plan B (les seuls amendements mis aux voix, sans leurs identiques) est gardé
dans la release `donnees-figees` du dépôt (`lvnd archiver an_amendements_16`), pour ne pas
refaire ses milliers de requêtes. `lvnd download` essaie dans l'ordre : le dump de l'AN (20
minutes sans aucun octet), cette copie (`mode: figee` au manifeste), puis le plan B. Le
dump remplace tout dès qu'il passe, ce que retente chaque lancement de `donnees.yml`.
La passe quotidienne ne le retente pas : elle réutilise l'archive déjà là.

Garde-fous de la passe quotidienne : rien n'est commité si un score change sans
qualification nouvelle, si `amendements.csv` perd des lignes ou si `lvnd check` échoue. La
date seule (`meta.json`) ne déclenche pas de commit.

L'archive des amendements de la XVIIe pouvant dater d'une semaine, `lvnd check` ne compte pas
dans son taux de rattachement les scrutins des 14 derniers jours. Essai du 30/10/2026
sur une archive de la veille : 157 nouveaux scrutins, 107 pas encore rattachés, tous du 29/10,
et `scores_*.csv` identiques à l'octet.

## Groupes : renommages et ventilations

- Un groupe qui change de nom reçoit un nouvel organe. Les ventilations des
  scrutins mêlent alors l'ancien et le nouveau, sans jamais les mettre dans
  un même scrutin. Le groupe socialiste de la XVIe apparaît sous PO830170
  dès le 14/12/2022, alors que l'AMO ne fait commencer ce nouvel organe
  que le 19/10/2023, et sous PO800496 jusqu'au 14/03/2024. Les lignées
  sont tenues dans `referentiels/groupes.yaml`.
- Une fois les lignées réunies, il reste 592 votes (33 députés) ventilés
  dans un groupe que l'AMO ne donne pas au député à la date. Ce sont des
  décalages de quelques jours, en début de législature ou lors d'un
  changement de groupe. La ventilation officielle fait foi.
- Le 21/06/2023, sur 4 scrutins (`V1927`, `V1929`, `V1930`, `V1948`), la
  ventilation de GDR-NUPES compte un vote de plus que sa liste
  nominative. L'anomalie vient du dump, et `lvnd check` la signale.

## Contrôle croisé

**leurs-votes.fr** (`dataset.json` public du 15/10/2026, 1 949 entrées,
`explo/controle_croise.py`) :

- 1 948 scrutins retrouvés dans les dumps. Le 1 949e est le vote du
  Congrès sur l'IVG, hors dump AN.
- Sur **22 531 paires scrutin × groupe, les décomptes (pour, contre,
  abstention, autres) sont identiques**, sans exception.
- 4 scrutins du 02/12/2024 (`V491`, `V493`, `V494`, `V501`) ont des
  ventilations sans organe (`PO0`). L'anomalie est connue, et quifaitlaloi
  la corrige par les mandats des votants.
- Les positions diffèrent par la règle, jamais par les données.
  leurs-votes.fr retient la majorité parmi les votants, abstention
  comprise, et laisse la position vide en cas d'égalité.
  - Sur 1 082 positions « abstention », 657 concernent des groupes sans
    aucun exprimé.
  - Pour les 425 autres, notre règle (majorité parmi les exprimés) donne
    « pour », « contre » ou « égalité ».

**datan.fr** (`explo/controle_datan.py`). Pas de positions par scrutin en
open data : les jeux de datan sur data.gouv.fr ne décrivent que les
députés et les groupes. On lit donc les pages de vote, sur un échantillon
aléatoire de 40 scrutins (graine fixe, une requête par seconde) :

- 426 paires scrutin × groupe (hors non-inscrits, que datan n'affiche
  pas) : **426 concordent** avec la majorité parmi les votants, abstention
  comprise ;
- 13 (3 %) diffèrent de notre règle des exprimés : ce sont des groupes
  majoritairement abstentionnistes, que datan n'affiche ni pour ni contre.

Conclusion : les ventilations de l'open data AN sont fiables, et les deux
outils retiennent la même règle de position, différente de la nôtre.
L'écart touche environ 3 % des positions de groupe. La page méthodologie
devra l'expliquer.

## Conseil constitutionnel et Journal officiel : PISTE utile ?

Les dossiers AN contiennent déjà :

- `CC-CONCLUSION` : sens de la décision (`Conforme`, `Partiellement
  conforme`…), numéro, année et URL sur conseil-constitutionnel.fr (testée :
  200) ;
- `PROM-PUB` : numéro de la loi, date, numéro du JO et **NOR**.

Le lien `urlLegifrance` fourni (`/WAspad/UnTexteDeJorf?numjo=…`) est
ancien. Le lien **ELI** se construit à partir de la date de la loi et du
NOR, et il fonctionne :
`https://www.legifrance.gouv.fr/eli/loi/2024/1/26/IOMV2236472L/jo/texte`
→ loi n° 2024-42.

**Verdict PISTE : non, pour la v1.** Les deux besoins envisagés
(décisions du Conseil constitutionnel, lien vers le JO) sont couverts par
l'open data AN. L'API ne servirait qu'au texte consolidé ou article par
article, hors périmètre. Ne pas créer l'application évite aussi d'avoir un
secret de plus à gérer. Verdict confirmé par Max le 29/10/2026.

## Code postal → circonscription

`explo/circos.py` (≈ 10 s ; `uv run --with openpyxl --with xlrd python
explo/circos.py`). **Aucune table officielle « code postal →
circonscription » n'existe.** On l'obtient en deux jointures, code postal →
communes (La Poste), puis commune → circonscription(s) (ministère de
l'Intérieur).

| Source | Producteur | Rôle |
|---|---|---|
| [Législatives 2024, 1er tour, par bureau de vote](https://www.data.gouv.fr/datasets/elections-legislatives-des-30-juin-et-7-juillet-2024-resultats-definitifs-du-1er-tour) | Ministère de l'Intérieur | commune × bureau → circo (70 102 bureaux) |
| [Législatives 2022, 1er tour, par bureau](https://www.data.gouv.fr/datasets/elections-legislatives-des-12-et-19-juin-2022-resultats-du-1er-tour) | Ministère de l'Intérieur | contrôle : porte la colonne circo, contrairement à 2024 |
| [Base officielle des codes postaux](https://www.data.gouv.fr/datasets/base-officielle-des-codes-postaux) | La Poste | code postal → communes (39 192 lignes, Latin-1) |
| [Code officiel géographique 2026](https://www.data.gouv.fr/datasets/code-officiel-geographique-1) | Insee | ramener les codes communes au COG en vigueur (fusions) |
| [Bureaux de vote et adresses de leurs électeurs](https://www.data.gouv.fr/datasets/bureaux-de-vote-et-adresses-de-leurs-electeurs) (REU, sept. 2022) | Insee | arrondissements PLM ; adresse → bureau (490 Mo) |
| [Table communes × cantons × circos](https://www.data.gouv.fr/datasets/circonscriptions-legislatives-table-de-correspondance-des-communes-et-des-cantons-pour-les-elections-legislatives-de-2012-et-sa-mise-a-jour-pour-les-elections-legislatives-2017) (2012, 2017) | Ministère de l'Intérieur | contrôle et repli uniquement (jamais mise à jour depuis 2017) |

Toutes ces sources sont sous Licence Ouverte. Le découpage juridique, lui,
est fixé par le code électoral (tableau n° 1 annexé, art. L. 125) : les
résultats électoraux n'en sont qu'un reflet, ce que la page méthodologie
devra dire.

**Piège** : le fichier 2024 par bureau n'a pas de colonne circonscription.
On la retrouve en comparant la liste des candidats de chaque bureau à celle
des 577 circos. Les 70 102 bureaux sont tous rattachés, et le résultat
recoupe 2022 : 35 244 couples commune × circo contre 35 262. Les écarts
s'expliquent tous par des fusions de communes.

**Chiffres** :

- 151 communes ou arrondissements sont à cheval sur plusieurs circos
  (14,4 % des inscrits). Parmi eux :
  - 13 arrondissements de Paris sur 20, 5 de Lyon sur 9, 5 de Marseille
    sur 16 ;
  - 82 communes, dont Toulouse, Nantes, Montpellier et Lille sur 5
    circos ;
  - 47 communes nouvelles, dont 43 coupées du fait de la fusion et
    4 à cheval sur deux départements.
- 6 326 codes postaux :

  | Cas | Codes postaux | Électeurs (estimés) |
  |---|---|---|
  | 1 seule circo | 5 352 | 71 % |
  | plusieurs circos, choisir la commune suffit | 719 | 13 % |
  | commune coupée, mais ce code postal n'en touche qu'une circo | 64 | 2 % |
  | il faut l'adresse, ou afficher plusieurs députés | 191 | 14 % |

- Outre-mer : complet. Les codes de l'AN (971 à 977, 986 à 988) sont
  alignés sur l'Insee, et Saint-Barthélemy et Saint-Martin partagent la
  circo 977.
- Français de l'étranger : 11 circos (code AN `099`), sans code postal. La
  table pays → circo est dans `pipeline/referentiels/pays_circonscriptions.yaml`,
  d'après le tableau n° 1 ter annexé au code électoral (art. L. 330-1), inchangé
  depuis l'ordonnance n° 2009-935 d'après Légifrance (relu le 01/11/2026). Le
  tableau date : Serbie, Monténégro, Kosovo, Soudan du Sud, Taïwan et Territoires
  palestiniens n'y sont pas nommés, et sont rattachés d'après le poste consulaire.
- Circo → député (AMO) : 577 sur 577 pour la XVIe comme pour la XVIIe,
  sur la clé `(numDepartement, numCirco)`. Les codes département de l'AN
  ont deux chiffres en métropole, plus `2A`, `2B`, `971` à `977`, `986` à
  `988` et `099`.
  - 75 circos de la XVIIe ont eu plusieurs députés successifs : chaque vote
    va au titulaire à la date du scrutin.
  - 3 sièges n'ont aucun mandat en cours au 28/10/2026 (10-02, 17-05,
    33-11, mandats achevés le 30/09/2026) : il faut prévoir un état
    « siège vacant ».

Points à surveiller à chaque build :

- ramener les codes communes au COG en vigueur (fusions du 1er janvier) ;
- tenir une courte liste de cas manuels (`02899` Cormicy, `98601`
  Wallis-et-Futuna, 4 communes du Cantal rétablies en 2025) ;
- vérifier le bureau n° 1 de Lyon (386 inscrits), sans arrondissement
  identifiable.

## XVe législature : ce qui diffère

Mesures du 31/10/2026, cycle XVe.

- **Dates.** Scrutins du 04/07/2017 au 24/02/2022, 472 631 votes nominatifs, 2 581 mises au point, 366 député·es qui
  n'ont siégé qu'en XVe, 17 organes de groupe (`referentiels/groupes.yaml` les réunit en lignées).
- **Effet sur le reste.** Sur les mêmes dumps, ajouter la XVe ne change rien aux XVIe, XVIIe et au Sénat, scores et
  votes compris, sauf 5 lignes de `textes.csv` qui gagnent leurs votes XVe, sans changement de décisif.
- **Dossiers de la XIVe.** Le dump de la XVe ne contient pas les dossiers ouverts avant juin 2017, même votés
  ensuite : 11 d'entre eux portent des votes de la XVe. Ils viennent du dump de la XIVe, arrêté à juin 2017, et leur
  loi est saisie dans `referentiels/rattachements.yaml`, avec le numéro et la date lus dans Dosleg. Ils n'ont pas de
  NOR, donc pas de lien vers Légifrance.
- **Rattachements figés.** 75 scrutins sont rattachés à la main dans ce même référentiel, qui prime sur la proximité dans
  la séance. Il corrige aussi deux champs du catalogue (`catalogue:`) : le titre de la programmation de la recherche et le sens
  de la décision 2021-817 DC. Sa section `corrections:` prime sur tout, y compris sur `objet.dossierLegislatif` du dump, quand
  celui-ci désigne un autre texte que celui que nomme le scrutin (V6758, en XVIIe : seul cas trouvé par
  `pipeline/explo/rattachement_objet.py` le 01/11/2026).
- **Déclarations du Gouvernement** (art. 49 ou 50-1). Elles ne vont qu'à leur propre dossier (procédure 11), quand il existe :
  le texte débattu le même jour ne les reçoit plus (règle corrigée le 01/11/2026). Les autres restent sans dossier.
- **Intitulés.** Pour V45, V738 et V1612, le titre du scrutin ne cite pas le même article que la division de l'amendement (6 et
  7, 4 et 5, 1 et 2). Les deux viennent de l'open data, rien ne permet de trancher sans lecture, et aucune qualification ne les retient.
- **Ventilations incomplètes** (`lvnd check`, listes fermées). 13 scrutins dont le décompte officiel dépasse la somme
  des groupes : un groupe manque, le plus souvent le MoDem (46 voix), et rien ne permet de reconstruire ses votes. Le
  seul vote sur l'ensemble touché de façon notable est V2816 (loi organique sur la dette sociale). 17 ventilations
  comptent une voix de plus que leur liste nominative, 15 pour le MoDem en septembre et octobre 2020, 2 pour LaREM.
- **Contrôle croisé.** leurs-votes.fr ne couvre pas 2017-2022. datan.fr, 40 scrutins tirés au sort (graine fixe), 327
  paires scrutin × groupe hors non-inscrits : 322 concordent. Les 5 autres ne sont pas des erreurs : 3 égalités à une
  voix dans un petit groupe, que datan affiche d'un côté, et 2 écarts de libellé sur les organes UDI successifs.
- **Amendements** (mesure du 01/11/2026). Le dump plafonne à 11 Ko/s : ils viennent du plan B, avec 3 069 scrutins
  rattachés à leur amendement sur 3 124 (98,2 %, seuil de `lvnd check` à 98 %, contre 99,5 % ailleurs). 49 des 55 autres n'ont
  pas d'amendement lisible : 404 sur tous les identifiants essayés, ou numéro factice dans le titre (« n° XXX »). Pour les 6
  derniers, l'amendement trouvé portait le même numéro dans un autre texte : il est refusé. Les amendements clés retenus sont
  contrôlés sur leur dispositif, sauf V446 et V2886, qui reposent sur le titre et le PDF ou le compte rendu.

