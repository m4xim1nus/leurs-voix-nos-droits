# Roadmap

Projet solo, sans calendrier engageant. Quatre étapes jusqu'à la v1, puis
des cycles courts. Chaque étape se termine par un **livrable relu par
Max** avant de passer à la suivante. Les idées non planifiées vont dans
`BACKLOG.md`.

## Étape 0 : cadrage ✅ (2026-10-29)

Cadrage privé et recherches dans `source/CADRAGE.md` (leurs-votes.fr,
découpage thématique de référence, textes candidats, direction visuelle).
Décisions dans `CLAUDE.md` : dépôt public, admin tout Cloudflare (D1 +
Access, publication par commit), périmètre AN XVIe-XVIIe. Squelette du
dépôt.

## Étape 1 : spike sources et grille ✅ (2026-10-29)

Verdict **GO** : l'open data AN suffit pour la v1 (`docs/SOURCES.md`).

- 1,97 M votes nominatifs (XVIe + XVIIe). Décision : tout versionner en CSV
  par législature et par mois ; `data/lvnd.sqlite` n'est pas versionné.
- Sur la XVIIe, 99,9 % des scrutins sur amendement sont rattachés à leur
  amendement, avec dossier, auteur et groupe.
- Les ventilations sont identiques à celles de leurs-votes.fr (22 531
  paires scrutin × groupe) et concordent avec datan.fr sur un échantillon.
- Code postal → circonscription : pas de table officielle directe. On la
  construit à partir de La Poste et du ministère de l'Intérieur ; 71 % des
  électeurs ont un député unique par code postal.
- PISTE : non. Décisions du Conseil constitutionnel et liens JO viennent
  des dossiers AN.
- Grille v0 et règles de qualification validées par Max
  (`pipeline/referentiels/droits.yaml`, `docs/METHODO.md`). Six textes
  témoins qualifiés et sourcés (`pipeline/referentiels/temoins.yaml`).

## Étape 2 : pipeline et méthode v0 ← *en cours (reste : XVIe)*

But : une base fiable des textes, scrutins et votes, et des règles de
calcul arrêtées.

- Package `lvnd` (`download` → `build` → `check`), qui écrit
  `data/lvnd.sqlite` (local) et `data/export/`, dont les votes nominatifs
  dans `votes/<législature>/<AAAA-MM>.csv`. `download` existe déjà, avec
  reprise automatique sur coupure.
- Reprendre de quifaitlaloi le parsing des scrutins, des dossiers et de
  l'AMO, ainsi que la correction des ventilations `PO0`. Porter dans le
  package le rattachement des amendements (`explo/rattachement_amendements.py`)
  et le **mesurer sur la XVIe**. Le dump de la XVIe n'a pas pu être
  téléchargé au spike : le serveur de l'AN coupait sans cesse.
- **Catalogue des candidats** : présélection des textes et scrutins par
  mots-clés (`referentiels/mots_cles.yaml`). Elle sert d'aide au tri dans
  l'admin, jamais de qualification automatique.
- **Scores** calculés depuis une qualification (`temoins.yaml` en
  attendant l'admin) : par député, par groupe et par droit. Les règles de
  `docs/METHODO.md` s'appliquent : scrutin décisif et amendements clés
  comptés, motions affichées.
- **Méthode v0** dans `docs/METHODO.md`, chaque règle **tranchée par
  Max** :
  - abstention et absences ;
  - pondération (un texte à vingt amendements ne doit pas écraser les
    autres) ;
  - votes du député quand il change de groupe ;
  - choix et sens des amendements clés des six textes témoins.
- **Livrable** : `docs/METHODO.md` v0, les scores des six textes témoins
  relus avec Max, `lvnd check` vert.

État au 29/10/2026 :

- ✅ `lvnd build` (≈ 25 s) et `lvnd check`. Exports dans `data/export/`
  (41 Mo, dont 26 Mo de votes en 44 fichiers mensuels).
- ✅ Correction `PO0`, amendements identiques, lignées de groupes
  (`referentiels/groupes.yaml`).
- ✅ Rattachement scrutin → dossier : 99,9 % en XVIIe. Pour les six
  témoins, le décisif proposé est bien celui de la qualification.
- ✅ Catalogue : 479 textes, dont 235 candidats par mots-clés
  (`mots_cles.yaml` en brouillon).
- ✅ Règles de calcul 14 à 19 validées, y compris absences, droits
  secondaires, score de groupe, cohésion et lignée UDR → UDDPLR.
- ✅ Amendements clés du narcotrafic (9) et de la justice des mineurs (4).
- ⏳ Dump des amendements de la XVIe : téléchargement par plages, lancé en
  processus détaché (journal : `data/raw/download_16.log`). Il est fini
  quand `an_amendements_16` figure dans `data/raw/manifeste.json`. Le
  29/10, le serveur de l'AN ne servait plus les plages de 1 Mio.
  `download` garde désormais chaque octet reçu, demande des plages de
  256 Kio et reprend un fichier partiel d'un lancement à l'autre. Ensuite :
  `lvnd build`, `lvnd check`, mesure du rattachement XVIe dans
  `docs/SOURCES.md`.
- ✅ Amendements clés de Kasbarian-Bergé (4, en 2e lecture). La règle 11
  est complétée : dernière lecture de l'AN où des suppressions ont été
  votées, et une source « cite » une mesure quand elle la met en cause.
- ⏳ Relecture des scores des six témoins avec Max.

## Étape 3 : admin en ligne ✅ (2026-10-29)

Admin SvelteKit + D1 sur `lvnd-admin.technoperchoir.fr`, derrière
Cloudflare Access (code par courriel). Publication par commit de
`data/editorial.json` via l'API GitHub. Conception et choix A à F validés :
`docs/CONCEPTION.md` ; mise en service : `admin/README.md`.

- `lvnd sync-admin` : catalogue vers D1 (`--brouillons`, `--valider` pour
  les lots de qualification).
- Contrôles identiques dans l'admin et `lvnd check`, tests croisés
  (sérialisation à l'octet près, scores de groupe, arrondi).
- Garde-fou : aucune source du commanditaire, liste privée de termes qui
  bloque la publication.
- Lot 1 : 21 textes préparés par Claude, relus et validés par Max
  (19 qualifiés, 2 écartés) ; avec les six témoins, 25 textes qualifiés.
  Règles 10 et 11 complétées à cette occasion.

## Étape 4 : site public v1 ← *en cours*

But : mise en ligne publique.

- Conception d'abord (`docs/CONCEPTION.md`) : récit, pages, direction
  visuelle inspirée de Bon Pote sans copie, cartes partageables.
- Pages (SvelteKit adapter-static + d3) :
  - accueil ;
  - une page par droit ;
  - fiche texte (avec ses scrutins) ;
  - fiche député ;
  - recherche par nom ou code postal ;
  - groupes ;
  - méthodologie ;
  - données téléchargeables.
- Fiche député : interpellation par `mailto:`.
- `build.sh`, CI de tests, Cloudflare Pages relié au dépôt, sous-domaine
  `technoperchoir.fr`. Recette sur téléphone.
- **Livrable** : site en ligne, tag `v1.0.0`, `CHANGELOG.md` créé.

Décisions de Max (29/10/2026) :

- ✅ Transparence (choix G) : la page Méthodologie dit que les
  qualifications sont préparées avec un assistant IA et validées par une
  personne. C'est écrit sur le site.
- ✅ Seuil de la v1 (choix H) : au moins une cinquantaine de textes
  qualifiés ; Max fixera le chiffre selon la vitesse de la qualification.
  D'ici là, bandeau « Site en préparation » (`site/src/lib/site.ts`,
  `OUVERT`).

État au 29/10/2026 (branche `etape-4`) :

- ✅ `lvnd scores` (choix F1) : scores recalculés depuis `data/export/` et
  `editorial.json` en ≈ 1 s, identiques à l'octet près à ceux de
  `lvnd build`. Ajoute la participation (règle 17) et les scores par
  texte.
- ✅ `lvnd annuaire` : code postal → circonscription (6 326 codes, repris
  du spike) et courriels des députés, dans `data/annuaire/`.
- ✅ Conception (`docs/CONCEPTION.md`, Site public).
- ✅ Site (`site/`) : accueil et recherche (code postal, nom), droits,
  textes, fiche texte, fiche député (« Lui écrire »), circonscriptions,
  groupes, méthodologie, données, cartes PNG partageables. 1 464 pages.
- ✅ `build.sh` et CI (tests et build du site).
- ✅ Choix I (score toujours affiché, avec son nombre de textes), J
  (participation : scrutins comptés pendant le mandat) et K
  (`lvnd.technoperchoir.fr`) validés par Max.
- ✅ Fusion dans `main` (29/10/2026). `lvnd build` appelle désormais
  `lvnd scores`, et la CI recalcule les scores avant les tests : la
  publication de l'admin la faisait échouer (scores versionnés périmés).
- ✅ Cloudflare Pages : projet `lvnd` relié au dépôt, production sur
  `main`, aperçus de `etape-4`. Domaine `lvnd.technoperchoir.fr` déclaré.
- ✅ En ligne sur `lvnd.technoperchoir.fr`. L'app GitHub de Cloudflare a
  accès au dépôt : chaque push sur `main`, donc chaque « Publier »,
  redéploie le site (vérifié le 29/10/2026).
- ✅ Recette sur téléphone par Max (29/10/2026).
- ✅ Backlog du site traité (29/10/2026) : textes adoptés sans opposition
  sur les fiches, page Comparer, fiche député allégée, typographie,
  interface sans numéros de règles, droits extrêmes sur les cartes.
- ⏳ Ouverture de la v1 au seuil de la décision H : `OUVERT = true` dans
  `site/src/lib/site.ts`, tag `v1.0.0`, `CHANGELOG.md`.
- ⏳ Livrable : site en ligne, tag `v1.0.0`, `CHANGELOG.md`.

## Qualification par lots (en continu, en parallèle de l'étape 4)

Procédure : `docs/QUALIFICATION.md`. Claude prépare, Max arbitre dans le
chat puis publie depuis l'admin.

- ✅ Lot 1 (21 textes, 29/10/2026).
- ✅ Lot de tri (29/10/2026) : sur 209 candidats, 144 écartés (texte
  d'organisation, hors grille, sans vote, décisif unanime, résolution,
  convention, corps électoral de Nouvelle-Calédonie) et 51 à qualifier
  (liste A et accès aux soins, `source/relecture-tri.md`). 14 n'ont pas
  encore de décisif. Soins palliatifs, décisif à 491-0, est écarté par la
  nouvelle règle 9. Règles 2, 8 et 9 complétées.
- ✅ Lot 2 (23 textes, 29/10/2026) : 17 validés, 6 écartés (fiche
  `source/relecture-lot2.md`). Règle 7 complétée (syndicats et instances
  du droit, avis du Conseil d'État ; pas de vigilance exigée sans critique
  admise), règle 8 (texte vidé avant le décisif), limite de la règle 14
  écrite.
- ✅ Lot 3 (21 textes, 29/10/2026) : 15 validés, 6 écartés (fiche
  `source/relecture-lot3.md`), dont 5 textes hors liste A que les
  mots-clés n'avaient pas repérés (logement, libertés). Règle 2 (choix
  d'une source d'énergie hors grille), règle 7 (instances consultatives
  indépendantes, syndicats de salariés ; pas la Cour des comptes), règle 9
  (article unique sans vote sur l'ensemble).
- ⏳ Lots suivants, d'une vingtaine de textes chacun, jusqu'au seuil de la
  v1, puis au fil de l'eau. Reste de la liste A : 12 textes, dont 5
  « faible », le PLFSS 2026 et trois textes d'adaptation au droit de l'UE.
  Ensuite, tri complémentaire des textes que les mots-clés ont ratés
  (`BACKLOG.md`). Aucun candidat `etrangers` avec vote final pour l'instant.
- ⏳ Les deux textes passés au 49.3 sans vote final (retraites 2023,
  PLF 2026) attendent la règle du décisif en cas de 49.3 (`BACKLOG.md`).

## Travail en parallèle (deux sessions Claude Code)

Deux copies de travail du même dépôt, pour que deux sessions ne modifient
jamais les mêmes fichiers non commités :

| Session | Dossier | Branche | Périmètre |
|---|---|---|---|
| Qualification et données | `~/dev/leurs-voix-nos-droits` | `main` | lots de qualification (`source/`, D1), fin de l'étape 2 (dump XVIe, `lvnd build/check`), `pipeline/` hors `lvnd scores`, `docs/METHODO.md`, `docs/SOURCES.md`, `docs/QUALIFICATION.md` |
| Site public (étape 4) | `~/dev/leurs-voix-nos-droits-site` (`git worktree`) | `etape-4` | `site/`, `build.sh`, `lvnd scores`, section « Site public » de `docs/CONCEPTION.md`, CI du site |

Règles :

- Au début de chaque session : `git pull` (sur `main`), ou `git fetch &&
  git merge origin/main` (sur `etape-4`). L'admin commite sur `main` à
  chaque publication.
- Chaque session commite seulement les fichiers de son périmètre, en les
  nommant (`git add <chemins>`, jamais `git add -A`), puis pousse.
- `ROADMAP.md` : chacune met à jour sa propre section. `BACKLOG.md` :
  on ajoute des lignes à la fin, sans réécrire les autres ; en cas de
  conflit, on garde les deux.
- La session « site » ne touche ni à D1 ni à `source/`, sauf pour lire
  `source/CADRAGE.md` (lien symbolique dans le worktree).
- Fusion de `etape-4` dans `main` : par avance rapide
  (`git merge origin/main`, tests, puis `git push origin etape-4:main`),
  après relecture par Max. Première fusion le 29/10/2026. Cloudflare Pages
  construit un aperçu de chaque push sur `etape-4`, et la production à
  chaque push sur `main` (dont chaque « Publier » de l'admin).

## Après la v1

Un cycle à la fois, nommé au moment de l'ouvrir. Pistes :

- **Sénat** : scrutins publics des sénateurs (Dosleg, déjà maîtrisé dans
  quifaitlaloi).
- **XVe** : 2017-2022 (sécurité globale, séparatisme, état d'urgence
  sanitaire).
- **Textes en cours** : suivi des textes avant leur adoption, et
  interpellation au bon moment.
- **Passation** : réécriture éditoriale, domaine définitif, comptes
  d'édition, transfert du compte Cloudflare et du dépôt.
