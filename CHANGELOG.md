# Changelog

Format inspiré de [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/).
Les tags `v*` du dépôt suivent ces versions.

## [1.3.0] — 2026-10-31

Cycle Sénat : le second vote de chaque texte. Le site montre comment les groupes du
Sénat ont voté sur les textes qualifiés, ajoute ce que le Sénat vote seul, et chacun·e
retrouve ses sénateur·ices. Aucun score ne mélange les deux chambres : `scores_*.csv` et
`participation.csv` de l'AN sont identiques à l'octet. 132 textes qualifiés, 417 écartés.

### Ajouté

- **Données** : 1 336 scrutins publics du Sénat et 464 719 votes nominatifs depuis juin
  2022, sénateur·ices et groupes datés, à part dans `data/export/senat/`, avec un code postal
  → département dans `data/annuaire/`. Contrôles de `lvnd check`, passe quotidienne et son
  garde-fou.
- **Méthode** : règles 23 à 28 (décisif du Sénat, lecture sur le texte voté, texte du seul
  Sénat, scores, vote de groupe, deux chambres séparées), publiées sur la page Méthodologie.
- **Qualifications** : 95 votes du Sénat lus sur les textes qualifiés, dont 76 décisifs comptés
  et 19 affichés. 28 textes votés au seul Sénat, casseurs-payeurs compris, dont 21 comptés
  et 7 affichés sans jugement. 49 textes écartés au tri. 37 textes publiés n'ont aucun bloc Sénat, ni
  scrutin public sur l'ensemble ni motion.
- **Scores du Sénat** : décisif seul, une seule période depuis le 28/06/2022, fichiers à part.
- **Site** : section « Au Sénat » sur chaque fiche texte, `/senat` (les groupes d'abord,
  droit par droit, le vote de groupe expliqué, recherche par code postal), `/senat/<slug>`
  (score « d'après les votes enregistrés à son nom », écarts au groupe, « Lui écrire », aucun
  taux de participation), filtre de chambre sur `/textes`, dernier vote du Sénat sur `/en-cours`,
  lien depuis la fiche député·e, sénateur·ices dans la recherche par nom.
- **Admin** : scrutins et décisif du Sénat sur la fiche, contrôles identiques à `lvnd check`
  (test croisé à l'octet), aperçu des scores, textes sans vote à l'AN, alertes
  `senat_premier_vote` et `senat_vote_posterieur` dans « À traiter ». Migration `0004_senat.sql`.

### Modifié

- Le catalogue s'étend aux dossiers votés au Sénat sur l'ensemble, même sans scrutin à l'AN.
- Le contenu de l'accueil ne change pas. Le menu gagne une entrée « Sénat », le pied de page cite
  l'open data du Sénat, et la recherche par nom y trouve aussi les sénateur·ices.

### Limites connues

- Le score individuel d'un·e sénateur·ice dit peu de choses : presque tous les votes suivent le groupe,
  et ils ne disent pas qui était présent (règle 27).
- Passe quotidienne pas encore observée avec ces données, à vérifier le 01/11/2026.
- Comparer ne couvre pas le Sénat. Pas d'amendements clés du Sénat, ni de cartes partageables
  des sénateur·ices.
- Dans l'admin, les droits d'une version « autre » du Sénat se saisissent en JSON.
- La fiche de suivi des ingérences étrangères (340-0) attend l'inscription à l'AN : son alerte
  reste ouverte.

## [1.2.0] — 2026-10-30

Cycle Stock des lois de finances : les six lois de finances adoptées par 49.3
sans vote final figurent sur le site, avec leurs motions de censure. Elles ne
comptent dans aucun score (règle 9) : `scores_*.csv` et `participation.csv` sont
identiques à l'octet avec ou sans elles. 104 textes qualifiés, 368 écartés.

### Ajouté

- **Six qualifications** : PLF 2023, 2024 et 2025, PLFSS 2023, 2024 et 2025, avec
  leurs 29 motions de censure, attribuées une à une d'après la page du dossier de
  l'AN et le compte rendu de la séance du vote. V2610 et V2989 portent sur la
  programmation des finances publiques : non retenues.
- **Deux textes au fil de l'eau** : corps de fonctionnaires pour les AESH et parcours
  de soins des victimes de violences sexuelles, votés le 29/10/2026, comptés dans
  les scores.
- **Méthode** : la formation professionnelle dans `travail-protection-sociale`
  (règle 2) ; la CIIVISE et les unions confédérales de retraités parmi les sources
  (règle 7).

### Modifié

- Cinq dossiers d'engagement de responsabilité écartés : leurs motions s'affichent
  avec le texte qualifié (PLFSS 2025 et PLF 2026).

### Limites connues

- Sources rares pour 2022-2023. Le PLF 2024 repose sur une seule source admise, un
  avis de la CNIL postérieur au vote et portant sur le décret d'application. Le
  PLFSS 2023 repose surtout sur des sources qui portent sur le projet. Le PLF 2025
  repose sur une seule mesure et sur des sources syndicales.
- Des mesures restent hors jugement faute de source admise trouvée (AAH à Mayotte,
  crédits de l'AME).
- Lois promulguées non lues sur Légifrance (accès refusé) : les articles viennent des
  textes adoptés par l'AN, comparés aux décisions du Conseil constitutionnel.

## [1.1.0] — 2026-10-30

Cycles Reliquat XVIe et Au fil des votes : les amendements de la XVIe sont
là, les données se mettent à jour chaque jour, et le site montre où en est
chaque texte, avant et après le vote. Scores inchangés (96 textes qualifiés).

### Ajouté

- **Amendements de la XVIe** : `lvnd download` essaie le dump de l'AN (20
  minutes sans octet, il abandonne), puis une archive antérieure, puis une copie
  figée dans la release `donnees-figees`, puis un plan B qui lit chaque
  amendement voté sur le site de l'AN. 3 159 scrutins sur amendement rattachés
  sur 3 173 (99,6 %). Le dump revenu remplace le tout (`docs/SOURCES.md`).
- **État de chaque texte** : source `senat_dosleg` (décisions du Sénat, pas de
  votes de sénateur·ices), parcours, agenda de l'AN (« inscrit », jamais « sera
  voté »), catalogue élargi aux textes en cours ou inscrits sans scrutin public
  à l'AN (559 textes). Exports `en_cours*.csv`, sans effet sur les scores.
- **Alertes** dans `lvnd check` et la file « À traiter » de l'admin : vote
  postérieur au décisif, unanimité contestée, premier décisif, texte inscrit.
- **Mise à jour quotidienne** : Action `donnees-quotidien.yml` (dossiers et scrutins
  de la XVIIe, agenda, Dosleg ; les gros dumps viennent du cache ou de la release).
  Elle ne commite rien si un score change sans qualification nouvelle ou si
  `amendements.csv` perd des lignes. L'Action hebdomadaire est réparée.
- **Site** : page `/en-cours` rangée par échéance, état sur les fiches et dans
  les listes, mention « vote de 1re lecture, texte encore en navette »,
  « Prochains votes » sur la fiche député·e, flux RSS et iCal statiques.
- **Fiches de suivi** : statut `a-suivre` dans l'admin et liste `suivis` de
  `editorial.json` : droits touchés et sources, sans sens, score ni scrutin.
  Deux fiches publiées (relance du logement, régularisation des travailleurs
  sans-papiers).
- **Méthode** : règles 20 à 22 (état d'un texte, texte qualifié en navette, fiche
  de suivi) et compléments à la règle 9, validés par Max. Circuit « au fil de
  l'eau » dans `docs/QUALIFICATION.md`.

### Modifié

- 363 textes écartés (6 de plus, tri de la file) ; titres débarrassés des
  mentions « (non promulgué) » et « (rejetée) », que l'état remplace.

### Corrigé

- Une publication faite avant la validation d'une requalification laisse la
  version publiée sur le site. `sync-admin --brouillons` ajoute une révision à
  un texte qui en a déjà une.

### Limites connues

- Tant que le dump de la XVIe reste injoignable, `amendements.csv` n'a pour cette
  législature que les amendements mis aux voix, sans leurs identiques ni les
  amendements non votés. 14 scrutins restent sans amendement. Sur la XVIe, l'article
  lu diffère dans 9 cas sur 2 712 (0,33 %) de celui de l'intitulé.
- L'Action hebdomadaire retente ce dump avant de prendre la release : 32 minutes de
  plus le 30/10/2026.
- `lvnd check` retire du taux de la XVIe ses derniers scrutins (3 041 sur 3 053
  affichés), par un délai de 14 jours pensé pour une législature en cours.
- Le suivi au fil des votes continue en fonctionnement courant (`BACKLOG.md`).
- Le Sénat (votes) et la XVe législature ne sont pas couverts ; les lois de finances
  2023 à 2025 ne sont pas encore qualifiées.

## [1.0.0] — 2026-10-29

Première version publique, en ligne sur
[lvnd.technoperchoir.fr](https://lvnd.technoperchoir.fr). Assemblée
nationale, XVIe et XVIIe législatures (depuis juin 2022).

### Ajouté

- **Pipeline `lvnd`** (Python 3.12, uv, polars) : `download` → `build` →
  `check`, à partir de l'open data de l'AN seul. 1,97 M votes nominatifs
  versionnés en CSV mensuels (`data/export/votes/`), correction des
  ventilations `PO0`, lignées de groupes, rattachement des scrutins aux
  dossiers (99,9 % en XVIIe) et aux amendements, catalogue des candidats
  par mots-clés (aide au tri, jamais de qualification automatique).
- **Méthode** (`docs/METHODO.md`, page Méthodologie) : grille v1 de douze
  droits et deux étiquettes, dix-neuf règles fixes validées une à une
  (qualification, scrutins retenus, position de groupe, calcul des
  scores). Abstentions et absences hors calcul, chaque texte pèse 1,
  texte adopté par 49.3 qualifié sans être compté.
- **Qualifications** : 96 textes qualifiés et sourcés (six textes témoins
  et six lots), 357 textes examinés puis écartés avec leur motif.
  Préparées avec un assistant IA, validées par une personne (dit sur le
  site).
- **Scores** (`lvnd scores`) : par député·e, par groupe, par droit et par
  texte, avec participation et cohésion ; recalculés en ≈ 1 s depuis
  `data/export/` et `data/editorial.json`.
- **Annuaire** (`lvnd annuaire`) : code postal → circonscription
  (6 326 codes, La Poste × résultats des législatives 2024) et courriels
  des député·es.
- **Admin** (`admin/`, SvelteKit + D1 derrière Cloudflare Access) :
  saisie des qualifications, contrôles identiques à `lvnd check`, garde-fou
  sur les sources, diff publié/brouillon, bouton « Publier » qui commite
  `data/editorial.json` via l'API GitHub. `lvnd sync-admin` pousse le
  catalogue dans D1.
- **Site public** (`site/`, SvelteKit adapter-static + d3) : accueil et
  recherche par code postal ou par nom, pages par droit, textes et fiches
  texte, fiches député·e (« Lui écrire » par courriel), circonscriptions,
  groupes, Comparer, méthodologie, données téléchargeables, cartes PNG
  partageables. Contestation d'une qualification par courriel. Aucun
  traceur, aucun CDN tiers.
- **Déploiement** : `build.sh` (aucun téléchargement), Cloudflare Pages
  sur `main` (chaque publication de l'admin redéploie le site), CI des
  tests, Action hebdomadaire de mise à jour des données.

### Déroulé

Quatre étapes et six lots de qualification, du 29/10/2026. Chaque règle
de méthode a été validée par Max (`docs/METHODO.md` date chacune).

- **Étape 0, cadrage** : dépôt public, admin tout Cloudflare (D1 et
  Access, publication par commit), périmètre AN XVIe-XVIIe.
- **Étape 1, spike** : verdict GO, l'open data de l'AN suffit
  (`docs/SOURCES.md`). Ventilations identiques à celles de leurs-votes.fr
  (22 531 paires scrutin × groupe), concordantes avec datan.fr sur un
  échantillon. Pas de table officielle code postal → circonscription :
  71 % des électeurs ont un député unique par code postal. PISTE écarté
  (Conseil constitutionnel et JO viennent des dossiers AN). Grille v0,
  règles 1 à 13, six textes témoins.
- **Étape 2, pipeline et méthode** : `lvnd build` (≈ 25 s) et
  `lvnd check`, rattachement scrutin → dossier à 99,9 % en XVIIe (votes de
  CMP de la XVIe compris), catalogue de 479 textes. Règles de calcul 14 à
  19, amendements clés du narcotrafic, de la justice des mineurs et de
  Kasbarian-Bergé. Reste le dump des amendements de la XVIe (limites
  ci-dessous).
- **Étape 3, admin** : `lvnd-admin.technoperchoir.fr`, choix A à F
  (`docs/CONCEPTION.md`), tests croisés pipeline/admin (sérialisation à
  l'octet près, scores, arrondi).
- **Étape 4, site** : choix G à K (transparence sur l'IA, seuil
  d'ouverture, score toujours affiché avec son nombre de textes,
  participation, domaine), recette sur téléphone, grille v1
  (`citoyennete`), règle du 49.3, écriture inclusive.
- **Qualification** (`docs/QUALIFICATION.md` : Claude prépare, Max
  arbitre et publie) : lot 1 (19 qualifiés), deux tris des candidats
  (144 puis 176 écartés, dont les motions de censure spontanées), lots 2 à
  6 (17, 15, 14, 16 et 10 validés). Le vivier de la v1 est épuisé.

### Limites connues

- **Étape 2 encore ouverte** : le dump des amendements de la XVIe
  (`an_amendements_16`) n'a pas pu être téléchargé, le serveur de l'AN
  coupant les transferts. Le rattachement des scrutins sur amendement de
  la XVIe n'est donc pas mesuré (`docs/SOURCES.md`). Les scrutins et votes
  de la XVIe sont complets ; ses scrutins sur amendement sont rattachés à
  leur dossier par la séance, sans l'amendement ni son auteur.
- Le Sénat et la XVe législature ne sont pas couverts.
- Les lois de finances adoptées par 49.3 sans vote final (PLF et PLFSS
  2023 à 2025) ne sont pas encore qualifiées.
- Les textes de la liste C attendent un vote final pour être qualifiés
  (`BACKLOG.md`).
