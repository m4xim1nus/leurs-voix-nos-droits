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

## Étape 2 : pipeline et méthode v0 ← *en cours*

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

## Étape 3 : admin en ligne ← *en cours*

But : qualifier les textes ailleurs que dans un fichier, et publier sans
passer par la machine de Max.

- App SvelteKit `admin/` (adapter-cloudflare) avec une base D1, derrière
  Cloudflare Access.
- `lvnd sync-admin` pousse le catalogue (textes, scrutins, positions de
  groupe) dans D1.
- Écrans :
  - liste des candidats, avec filtres ;
  - fiche texte : droits, sens, résumé, sources, statut brouillon ou
    publié ;
  - choix des scrutins retenus et de leur sens, avec les positions de
    groupe affichées ;
  - aperçu du score.
- **« Publier »** : export de D1 → `data/editorial.json`, commit par l'API
  GitHub, puis rebuild du site. Chaque modification garde son auteur et
  sa date.
- **Livrable** : admin en ligne, les six textes témoins importés (choix D1), et une
  vingtaine de textes qualifiés par Max à travers elle.

État au 29/10/2026 (conception : `docs/CONCEPTION.md`) :

- ✅ `data/editorial.json` (format 1, généré depuis `temoins.yaml`). Le
  pipeline le lit pour les scores, et `lvnd check` contrôle chaque
  qualification.
- ✅ `lvnd sync-admin` : catalogue et qualifications publiées vers D1
  (locale ou distante).
- ✅ App `admin/` : liste des textes, fiche texte (qualification, scrutins
  avec positions de groupe, aperçu du score, contrôles, historique),
  aperçu des scores, publication par l'API GitHub, journal. Elle vérifie
  elle-même le jeton d'Access. Testée en local sur D1 émulée.
- ✅ Tests croisés pipeline ↔ admin : sérialisation d'`editorial.json` à
  l'octet près, scores de groupe identiques.
- ✅ Choix A à F de `docs/CONCEPTION.md` validés par Max.
- ✅ Mise en service : dépôt public sur GitHub, D1 en ligne, admin sur
  `lvnd-admin.technoperchoir.fr` derrière Cloudflare Access (code par
  courriel), publication testée.
- ⏳ Vingtaine de textes : brouillons préparés par Claude (recherche et
  sources), chargés « à relire », validés un par un par Max.

## Étape 4 : site public v1

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
