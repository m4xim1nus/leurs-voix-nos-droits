# Changelog

Format inspiré de [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/).
Les tags `v*` du dépôt suivent ces versions.

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
