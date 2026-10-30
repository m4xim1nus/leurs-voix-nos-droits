# Conception

Conception de l'admin (étape 3), puis du site public (étape 4).
Les choix A à F de l'admin et G à M du site ont été validés par Max le
29/10/2026 : à chaque fois l'option recommandée (✅). Les autres options
sont gardées pour mémoire.

## Admin

### Rôle

L'admin sert à **qualifier les textes** sans éditer de fichier. On y
choisit les droits touchés, leur sens et leurs sources, ainsi que les
scrutins retenus et leur sens. Le bouton **« Publier »** verse ensuite le
résultat dans le dépôt. L'admin ne calcule rien de public. Les scores
publiés sont toujours recalculés depuis `data/editorial.json` et les
votes nominatifs versionnés.

### Architecture

```
pipeline (local)                 Cloudflare                          dépôt git
────────────────                 ──────────                          ─────────
data/export/*.csv ──sync-admin──▶ D1 : catalogue (lecture seule)
data/editorial.json ─(amorçage)─▶ D1 : qualifications, révisions
                                   ▲
                       Access ──▶ admin/ (SvelteKit, Worker)
                                   │ « Publier »
                                   └──── API GitHub (commit) ──────▶ data/editorial.json
                                                                       │
                                               Cloudflare Pages ◀──────┘ (build du site)
```

- **Catalogue** : `lvnd sync-admin` lit `data/export/` (et non la base
  locale), puis remplace dans D1 les textes, les scrutins rattachés à un
  dossier, les groupes et la grille des droits. Le catalogue est
  versionné : l'Action hebdomadaire des données lance ce sync sans dump
  (`.github/workflows/donnees.yml`). Le premier sync a écrit 40 800
  lignes, index compris. Le sync est depuis incrémental : il n'écrit que
  ce qui a changé, loin de la limite gratuite de D1 (100 000 écritures
  par jour).
  Les positions de groupe sont rangées en JSON dans la ligne du scrutin :
  155 000 lignes de moins.
- **Qualifications** : une ligne par texte, avec un document JSON au
  format exact d'une entrée d'`editorial.json` et un statut. Chaque
  enregistrement ajoute une **révision** (document complet, auteur, date).
  L'historique de travail reste ainsi dans D1, et git garde l'historique
  publié.
- **Amorçage** : `lvnd sync-admin --editorial` copie dans D1 les
  qualifications d'`editorial.json` qui n'y sont pas encore (les six
  témoins au départ). Il n'écrase jamais un brouillon. D1 peut donc être
  reconstruite depuis git à tout moment.
- **Identité** : Cloudflare Access fournit le courriel de l'utilisateur.
  L'app vérifie elle-même le jeton d'Access (signature, audience,
  émetteur, expiration) : une adresse `*.workers.dev` ou de
  prévisualisation laissée sans politique Access ne donne donc rien.

### Format d'`editorial.json`

Il reprend celui de `pipeline/referentiels/temoins.yaml`, sans les
champs que l'open data fournit déjà (numéro de loi, NOR, décision du
Conseil constitutionnel) : ceux-là viennent du catalogue. Le
fichier est déterministe (clés et textes triés, indentation fixe) : une
publication produit un diff lisible.

```json
{
  "format": 1,
  "grille": 0,
  "textes": [
    {
      "id": "jo-2024",
      "dossier_an": "DLR5L16N46918",
      "titre": "Loi relative aux jeux Olympiques et Paralympiques de 2024",
      "resume": "",
      "droits": [{ "code": "vie-privee", "role": "principal", "sens": "restreint",
                   "sources": ["cnil-2022-118"], "justification": "…" }],
      "etiquettes": ["regime-exception"],
      "vigilance": [{ "texte": "…", "sources": [] }],
      "conseil_constitutionnel": "Censure de l'article 7 (cavalier)…",
      "sources": { "cnil-2022-118": { "auteur": "CNIL", "titre": "…", "date": "2023-01-04", "url": "…" } },
      "scrutins": [{ "id": "VTANR5L16V1409", "role": "decisif", "pour": "texte", "objet": "…" }]
    }
  ]
}
```

Le pipeline lit `data/editorial.json` pour les scores. `temoins.yaml`
reste la référence des contrôles de `lvnd check`.

Une liste `suivis` s'ajoute après `ecartes` dès qu'une fiche de suivi est
publiée : `id`, `dossier_an`, `legislature`, `titre`, `resume`, `droits`
(`code`, `sources`, `justification`, sans rôle ni sens), `note`, `sources`.
Absente tant qu'elle est vide, elle ne change donc aucun octet du fichier
actuel, et le format reste 1 : un lecteur qui l'ignore lit le reste sans
changement. Aucun score ne la lit. Pipeline et admin l'écrivent à l'identique,
vérifié sur `pipeline/tests/fixtures/editorial_suivis.json`.

### Écrans

1. **Textes** (accueil) : les 479 textes du catalogue, avec des filtres
   (législature, nature, candidats par mots-clés, droit candidat, statut
   de qualification, recherche dans le titre). Par défaut, on voit les
   textes ordinaires candidats.
2. **Fiche texte** :
   - en-tête open data : loi, décision du Conseil constitutionnel, liens
     AN et Légifrance, motifs des mots-clés ;
   - qualification : droits (code, rôle, sens, justification, sources),
     étiquettes, vigilance, sources, résumé, résumé de la décision du
     Conseil constitutionnel ;
   - scrutins du dossier, du plus récent au plus ancien, avec leur
     décompte et les positions de groupe (sigle, position, cohésion).
     Pour chacun : non retenu, ou rôle et sens. Le décisif proposé par le
     pipeline est signalé, et un amendement porte sa division, son
     auteur et son sort ;
   - aperçu du score de chaque groupe sur ce texte ;
   - contrôles bloquants et avertissements, statut, historique des
     révisions.
3. **Aperçu** : scores des groupes par droit sur l'ensemble des textes
   validés, ou validés et en brouillon, avant publication.
4. **Publier** : textes validés, nouveaux ou modifiés depuis la dernière
   publication, avec leurs contrôles. Le bouton ouvre un commit. Un texte
   déjà publié, repassé en brouillon ou « à relire », garde sa version
   publiée jusqu'à sa validation ; pour le retirer du site, on l'écarte.
   Liste des publications passées (date, auteur, lien vers le commit).
5. **Journal** : dernières révisions, tous textes confondus.

Les scores des groupes se calculent dans l'aperçu à partir des
ventilations officielles. Ils suivent les règles 14 à 19 et la lignée des
groupes, comme le pipeline. Un test croisé vérifie que l'aperçu redonne
`data/export/scores_groupes.csv`. Les scores des députés exigent les
votes nominatifs (près de 2 M de lignes) : ils n'apparaissent qu'après
publication.

### Contrôles

Les mêmes règles s'appliquent dans l'admin (`admin/src/lib/qualification.ts`)
et dans `lvnd check` :

- **Bloquants pour valider** : un et un seul droit principal ; codes de
  droits et d'étiquettes pris dans la grille ; au moins une source par
  droit ; toute source citée est définie, avec une URL ; un et un seul
  scrutin décisif ; tout scrutin retenu appartient au dossier ; un seul
  amendement clé par article et par lecture.
- **Avertissements** : un scrutin au sens `a-trancher` (il ne compte
  pas), un texte qui étend un droit sans source critique en vigilance
  (règle 7), un décisif qui diffère de celui que propose le pipeline, une
  source définie mais jamais citée.
- **Fiche de suivi** (statut `a-suivre`, bloquants) : au moins un droit touché,
  codes pris dans la grille, ni sens ni rôle, au moins une source par droit,
  toute source citée définie avec une URL, aucun scrutin retenu, et les termes
  interdits comme partout. Un texte déjà qualifié et publié ne peut pas
  repasser à suivre : il garde son sens.

### Choix (validés le 29/10/2026)

**A. Qui publie, et sous quel nom dans git** ✅ A1

Le dépôt est public, et un commit expose le nom et le courriel de son
auteur.

- A1 (**retenu**) : le commit est au nom du
  compte qui détient le jeton (`m4xim1nus`, déjà public comme
  propriétaire du dépôt). Le message dit seulement « Publié depuis
  l'admin », sans le courriel de la personne qui publie. Ce courriel
  reste dans le journal D1, qui est privé.
- A2 : commit au nom de la personne (courriel d'Access). La traçabilité
  est publique, mais le courriel aussi.
- A3 : identité dédiée (GitHub App ou compte robot). C'est la plus propre
  pour la passation, mais elle demande un compte de plus à gérer.

**B. Cycle de vie d'une qualification** ✅ B1

- B1 (**retenu**) : quatre statuts. `brouillon`, `a-relire`, `valide`
  et `ecarte` (texte examiné et non qualifié, par exemple
  organisationnel, règle 8). « Publier » prend **tous** les textes
  `valide`, en un seul commit.
- B2 : publication texte par texte (un commit chacun). Les commits sont
  plus fins, mais la page Méthodologie et les scores changeront plus
  souvent.
- Variante de B1, **les textes écartés** :
  - (**retenu**) les publier aussi, avec leur motif, dans une
    liste `ecartes` d'`editorial.json`. On voit ainsi ce qui a été
    examiné, et pourquoi on ne l'a pas retenu (transparence) ;
  - ou les garder privés.

**C. Bibliothèque des sources** ✅ C1

- C1 (**retenu pour la v1**) : sources propres à chaque texte, comme
  dans `temoins.yaml`. Un bouton « reprendre une source d'un autre
  texte » évite la ressaisie.
- C2 : une bibliothèque commune (un avis de la CNCDH sur la surveillance
  sert pour plusieurs textes). Elle évite les doublons, mais une
  modification touche alors plusieurs textes publiés.

**D. Amorçage des six témoins** ✅ D1

- D1 (**retenu**) : import depuis `editorial.json`, généré à partir
  de `temoins.yaml` (statut `valide`). La ressaisie ne prouve rien de plus
  que l'import, et le livrable reste la vingtaine de textes nouveaux
  qualifiés à travers l'admin.
- D2 : ressaisie à la main, comme test de l'ergonomie.

**E. Hébergement et adresse** ✅ E1

- E1 (**retenu**) : un Worker avec ses fichiers statiques (la cible
  actuelle d'`adapter-cloudflare`), sur `admin.<sous-domaine du site>`,
  derrière une application Access (code par courriel, politique : liste
  de courriels). Le Worker n'a pas de route `workers.dev`
  (`workers_dev = false`).
- E2 : projet Pages. Attention au piège noté pour wrangler 4.148
  (redirection vers Workers à la création).

**F. Calcul des scores publiés** ✅ F1 (s'applique à l'étape 4)

`build.sh` n'exécute aujourd'hui que Node. Or une publication ne change
que `editorial.json`, et les scores en dépendent.

- F1 (**retenu**) : une commande `lvnd scores` (Python, à écrire)
  recalcule les scores depuis `data/export/` et `editorial.json`, sans
  dump. Les députés se calculent depuis les votes nominatifs versionnés,
  les groupes depuis les ventilations, comme l'aperçu de l'admin (le
  test croisé montre que les deux méthodes concordent). `build.sh`
  l'exécute avant le build du site (`pip install uv`, ≈ 30 s de plus). Il
  n'y a qu'une implémentation de référence.
- F2 : le site recalcule en TypeScript au build. On aurait alors deux
  implémentations à garder synchrones, sous test croisé.
- F3 : une GitHub Action recalcule et commite les scores après chaque
  publication. Cela fait deux commits par publication, et une étape de
  plus qui peut casser.

### Mise en service (gestes de Max)

À faire une fois, avec le compte Cloudflare et le compte GitHub (détail
dans `admin/README.md`) :

1. `npx wrangler d1 create lvnd-admin`, puis reporter l'identifiant dans
   `admin/wrangler.jsonc`.
2. `npx wrangler d1 migrations apply lvnd-admin --remote`.
3. `cd pipeline && uv run lvnd sync-admin --remote --editorial`.
4. Jeton GitHub *fine-grained*, limité au dépôt, avec la permission
   « Contents: read and write » :
   `npx wrangler secret put GITHUB_TOKEN`.
5. Application Access sur le domaine de l'admin. Reporter l'audience
   (AUD) et le domaine d'équipe dans `admin/wrangler.jsonc`.
6. `npm run deploy` dans `admin/`.

## Site public

### Rôle et public

Le site répond à une question : **comment mon député, et chaque groupe,
votent-ils sur les textes qui touchent à nos droits ?** Il s'adresse à
quelqu'un qui n'a jamais lu un scrutin de l'AN. Il ne juge pas les
personnes : il montre des votes, la qualification de chaque texte et ses
sources. Chaque chiffre mène, en un ou deux clics, au scrutin officiel
qui le fonde.

Ton : factuel, phrases courtes, vocabulaire courant. Écriture inclusive
(demande de Max du 29/10/2026) : point médian pour les mentions génériques
(« votre député·e », « les député·es »), genre de la civilité publiée par
l'AN quand on parle d'une personne (« Députée depuis… »), tournure
épicène quand elle est plus simple (« Vous vivez hors de France »). Les
noms officiels restent tels quels (« Français établis hors de France »). On écrit « vote
favorable aux droits », jamais « bon vote » ; « le texte restreint la
vie privée », avec la source à côté, jamais « texte liberticide ».

### Parcours

1. **Mon député** (parcours principal). Code postal ou nom sur l'accueil,
   puis la fiche du député : score global et par droit (un clic sur un droit filtre ses votes), participation,
   puis ses votes texte par texte, chacun à côté de la position de son
   groupe. Bouton « Lui écrire » (`mailto:`).
2. **Un droit**. Depuis l'accueil, l'un des onze droits : les textes qui
   le touchent, dans quel sens et selon quelles sources, puis le score
   des groupes sur ce droit.
3. **Un texte**. Sa qualification sourcée, la décision du Conseil
   constitutionnel, ses scrutins (comptés ou affichés seulement) et le
   vote de chaque groupe, avec sa cohésion.
4. **Vérifier**. Méthodologie (règles fixes, numérotées comme dans
   `docs/METHODO.md`), textes examinés puis écartés, données
   téléchargeables.

### Pages

| Page | Adresse | Contenu |
|---|---|---|
| Accueil | `/` | recherche (code postal, nom), score global des groupes de la XVIIe, les onze droits, derniers textes qualifiés |
| Droit | `/droits/<code>` | libellé, textes (principal ou secondaire, sens), scores des groupes par législature |
| Textes | `/textes` | textes qualifiés (filtres : droit, sens, législature), textes écartés et leur motif |
| Fiche texte | `/textes/<id>` | droits, sens, justification et sources ; vigilance ; Conseil constitutionnel ; scrutins et positions de groupe ; score de chaque groupe sur ce texte ; liens AN et Légifrance |
| Textes en cours | `/en-cours` | textes retenus encore en navette, rangés par échéance (inscrit à une date, attendu à l'AN, au Sénat, en CMP, suite pas encore connue) : ordre du jour, sens lu sur le texte voté, dernier vote public de l'AN par groupe, mention si ce vote n'est pas encore qualifié |
| Fiche député | `/deputes/<slug>` | circonscription, groupes successifs, score global et par droit (un clic sur un droit filtre ses votes), participation, abstentions, votes sur chaque scrutin compté (les autres sont sur la fiche texte), textes adoptés sans opposition, « Lui écrire », carte partageable |
| Circonscription | `/circonscriptions/<dép>-<num>` | député en cours, ou « siège vacant », et ses prédécesseurs depuis 2022 |
| Groupes | `/groupes` | par législature : tableau groupe × droit, effectifs |
| Fiche groupe | `/groupes/<sigle>-<législature>` | score global, par droit et par texte (un clic sur un droit filtre ses textes), textes adoptés sans opposition, membres et leur score |
| Comparer | `/comparer?a=…&b=…` | deux députés, deux groupes, ou un député et son groupe : score, droit par droit, textes où ils s'écartent le plus ; deux règles par ligne (le premier en haut, curseur plein ; le second en bas, curseur creux), bandeau fixe qui les rappelle au défilement |
| Méthodologie | `/methodologie` | grille, règles 1 à 22, préparation des qualifications, code postal, sources |
| Données | `/donnees` | `editorial.json`, exports CSV, votes nominatifs, licence |

Le slug d'un député est `prenom-nom` en minuscules sans accents. En cas
d'homonymie, on ajoute le numéro d'acteur (`PA…`). Le slug d'un texte est
l'`id` de sa qualification (`narcotrafic`).

### Données

Le build ne télécharge rien. Il lit `data/export/`, `data/editorial.json`
et `data/annuaire/` (code postal, courriels), puis prérend chaque page.
Le navigateur ne reçoit que la page. Deux exceptions, des JSON statiques
chargés à la demande : l'index des noms (≈ 840 députés) et la table des
codes postaux, découpée par département.

- **Scores** : `build.sh` lance d'abord `lvnd scores` (choix F1). Le site
  n'en recalcule aucun : il affiche `scores_*.csv` et
  `participation.csv`. Seule dérivation : une liste filtrée sur un droit
  montre un texte sous l'angle de ce droit ; si son sens y est contraire
  à celui du droit principal, le score du texte devient 100 − score
  (règle 15, chaque vote favorable devenant défavorable). Une publication depuis l'admin met donc le site à
  jour sans la machine de Max.
- **Positions de groupe** : `positions_groupes.csv` (règle 12), telles
  quelles.
- **Annuaire** : `lvnd annuaire`, lancé en local depuis les dumps
  (`data/raw/circos/`, AMO), écrit `data/annuaire/`, versionné. Il ne
  change qu'avec le découpage, les communes ou les députés. Le
  rattachement code postal → circonscription reprend le spike
  (`docs/SOURCES.md`).

### Affichage des scores

- Un score s'écrit « 37 % de votes favorables aux droits », jamais seul :
  toujours avec le nombre de textes (« sur 6 textes ») et, pour un
  député, sa participation (« a pris part à 18 des 24 scrutins
  comptés ») et ses abstentions.
- La barre de score va de 0 à 100, sans couleur de parti. Le groupe garde
  sa couleur officielle, toujours avec son sigle.
- Un vote compté s'affiche avec son sens lu en clair : « Pour le texte,
  donc défavorable à la vie privée (le texte la restreint) ». C'est la
  règle 14 rendue lisible.
- Les scrutins affichés mais non comptés (autres lectures, motions) sont
  rangés à part, avec leur raison (règles 9 et 10).
- L'état d'un texte (`en_cours_etats.csv`) s'affiche sur sa fiche, datée du
  dump des dossiers (« État au… »), et dans les listes : un fait, jamais un
  jugement. Un vote compté sur un texte en navette porte la mention « vote de
  1re lecture, texte encore en navette » (la lecture est celle du scrutin), et
  le sens du texte se lit « sur le texte voté le… ». Un texte à l'arrêt affiche
  son état, sans cette mention.
- Le site affiche un bandeau tant que la v1 n'est pas ouverte : « Site en
  construction, N textes qualifiés ».
- Les textes écartés parce que leur décisif n'a eu aucune voix contre
  (règle 9) s'affichent sur les fiches député et groupe, avec le vote de
  chacun, hors des scores. Le site les reconnaît à leur motif, écrit par
  l'admin sur un modèle fixe (« Adopté sans aucune voix contre au scrutin
  décisif… »).
- L'interface ne cite pas les règles par leur numéro : elle dit la règle
  en clair. Les numéros restent sur la page Méthodologie, ancrés
  (`#regle-11`). Les notes de méthode des qualifications, qui les citent,
  sont repliées sous « Comment ce texte a été qualifié », chaque numéro
  lié à sa règle.
- Typographie : espaces insécables avant « : ; ! ? » et dans les
  guillemets, posées aussi à l'affichage des textes saisis dans l'admin.

### Direction visuelle

Inspirée de Bon Pote (chiffre clé d'abord, preuve à un clic, visuels
partageables, ton accessible), sans en reprendre la palette, les polices
ni la mise en page.

- **Registre** : l'affiche et la pancarte de manifestation, plus que le
  journal. Des titres en grotesque étroite très grasse, en minuscules,
  serrés ; tout le reste sobre.
- **Police** (libre, hébergée par le site) : Archivo seule, police
  variable à axe de chasse. Étroite et très grasse pour les titres et les
  chiffres clés, chasse normale pour le texte. Atkinson Hyperlegible Next,
  d'abord prévue pour le texte, a été écartée : son zéro barré gêne dans
  les dates (« 2Ø22 »).
- **Palette** : papier blanc pur (`#ffffff`), encre presque noire bleutée
  (`#15171c`), gris ardoise (`#5b606b`) et filets (`#dcdee3`). Deux
  couleurs de données seulement, jamais employées en décor : **bleu
  canard** (`#0b6e78`) pour « favorable aux droits » et **framboise**
  (`#b0325f`) pour « défavorable ». Elles restent distinctes pour les
  daltoniens et ne reprennent la couleur d'aucun parti. Ni rouge ni bleu
  roi : en France, ils se lisent gauche et droite. Abstention en gris
  (`#9ea3ab`).
- **L'élément marquant** : la **règle graduée** du score, un trait de
  0 à 100 où chaque groupe ou député est une marque à sa position, comme
  sur un instrument de mesure. On la retrouve partout (accueil, droit,
  fiche, carte partageable).
- Mise en page alignée à gauche, colonne de texte de 70 caractères au
  plus, tableaux qui défilent horizontalement sur téléphone. Mode sombre
  suivant le système. Aucune animation hors des actions de l'utilisateur.

### Cartes partageables

Une image PNG par député et par groupe, au format 1200 × 630 (aperçu de
lien, `og:image`) : nom, groupe, circonscription, score global sur la
règle graduée, trois droits les plus et les moins favorables, nombre de
textes, adresse de la fiche. Générées au build (SVG rendu en PNG par
`@resvg/resvg-js`), sans service tiers. resvg ne lit ni le WOFF2 ni les
axes variables : deux instances statiques d'Archivo en TTF sont rangées
dans `site/scripts/polices/`. La fiche propose « Télécharger l'image ».
La carte donne aussi le droit le plus et le moins favorable ; à égalité,
leur nombre (« 4 droits ») plutôt qu'un nom pris au hasard.

### Code postal

Saisie de cinq chiffres, puis résultat sans rechargement depuis la table
du département :

- une seule circonscription : on ouvre la fiche du député ;
- plusieurs (commune coupée, ou code postal à plusieurs communes) : la
  liste des députés possibles, avec les communes de chaque
  circonscription (option A du `BACKLOG.md`). L'adresse exacte (option C)
  attendra un cycle ;
- siège vacant : la fiche de la circonscription le dit, avec le dernier
  député.

Français de l'étranger : un lien vers les onze circonscriptions, en
attendant la table pays → circonscription (`BACKLOG.md`).

### Technique

- SvelteKit `adapter-static`, d3 pour les échelles, Node 22, copié de
  quifaitlaloi (`site/`, mêmes conventions de test et de format).
- Aucun tracker, aucun CDN tiers, CSP stricte (`static/_headers`).
- Accessibilité : contraste AA, focus visible, tableaux de données en vrai
  `<table>`, chaque graphique doublé d'un texte.
- `build.sh` : `lvnd scores`, puis `npm ci && npm run build` dans
  `site/` (≈ 45 s en local, ≈ 4 000 fichiers dont 860 cartes, sous la limite de 20 000
  de Pages). Il installe uv s'il manque (`pip install --user uv`). La CI
  lance les tests du site et un build complet.
- Les scores par texte (fiche texte, fiche député) viennent aussi de
  `lvnd scores` (`scores_groupes_textes.csv`, `scores_deputes_textes.csv`).
  Un test du site vérifie que les votes favorables relus vote par vote sur
  une fiche redonnent ceux de `scores_deputes.csv`.

### Mise en service

Faite le 29/10/2026 par l'API Cloudflare (jeton de wrangler), sur le modèle
du projet quifaitlaloi :

- projet Pages `lvnd` (`lvnd.pages.dev`) relié à
  `m4xim1nus/leurs-voix-nos-droits` ; production sur `main`, aperçus pour
  la seule branche `etape-4` ; build `bash build.sh`, sortie `site/build`,
  `NODE_VERSION=22`, image de build v3 ;
- domaine `lvnd.technoperchoir.fr` (choix K) déclaré sur le projet.

Deux gestes de Max, faits le 29/10/2026 :

1. Donner accès au dépôt à l'application GitHub de Cloudflare, installée
   pour une sélection de dépôts (quifaitlaloi, prenoms) : sur GitHub,
   Settings, Applications, « Cloudflare Workers and Pages », Configure,
   Repository access, ajouter `leurs-voix-nos-droits`. Sans cela, aucun
   push ne déclenche de build (le premier déploiement a été lancé à la
   main, par l'API).
2. L'enregistrement `CNAME lvnd → lvnd.pages.dev` (proxifié) dans la zone
   `technoperchoir.fr`, le jeton de wrangler n'ayant pas de droit sur le
   DNS. Dans le tableau de bord : Workers & Pages, `lvnd`, Custom domains,
   « Activate domain » le crée.

Chaque push sur `main` reconstruit le site, donc chaque « Publier » de
l'admin : en quelques minutes, sans passer par la machine de Max.

### Choix

**G. Dire que les qualifications sont préparées avec un assistant IA** ✅
G1 (validé par Max le 29/10/2026)

- G1 (**retenu**) : oui. La page Méthodologie dit que chaque
  qualification est préparée avec un assistant IA (Claude, d'Anthropic),
  qui rassemble les sources et propose droits, sens et scrutins, puis
  relue, corrigée au besoin et validée par une personne avant
  publication. Aucune n'est publiée sans cette validation.
- G2 : non.

**H. Seuil d'ouverture de la v1** ✅ H1 (validé par Max le 29/10/2026)

- H1 (**retenu**) : au moins une cinquantaine de textes qualifiés. Max
  fixera le chiffre exact selon la vitesse de la qualification. D'ici là,
  le site tourne avec le bandeau « en construction ».

**I. Seuil d'affichage d'un score** ✅ I1 (validé par Max le 29/10/2026)

Avec peu de textes, un score sur un droit repose sur un ou deux votes.

- I1 (**retenu**) : toujours afficher le score, avec son nombre de
  textes. Une règle fixe et simple, sans score caché.
- I2 : ne pas afficher un score fondé sur un seul texte (« un seul texte,
  voir le vote »).

**J. Participation** ✅ J1 (validé par Max le 29/10/2026)

Règle 17 : le taux de participation s'affiche à côté du score. Définition
proposée, codée dans `lvnd scores` :

- J1 (**retenu**) : part des scrutins comptés, tenus pendant le
  mandat du député, où il a voté pour, contre ou s'est abstenu.
  Non-votant ou absent : il n'y a pas pris part. Chaque scrutin pèse 1.
  Sur les six témoins, la médiane est de 33 % : les amendements se votent
  en séance ordinaire, où l'on est peu nombreux.
- J2 : les décisifs seulement. Le taux serait plus haut et plus parlant,
  mais il dirait moins sur les amendements clés comptés dans le score.

**K. Sous-domaine** ✅ K1 (validé par Max le 29/10/2026)

- K1 (**retenu**) : `lvnd.technoperchoir.fr`, court et cohérent avec
  l'admin (`lvnd-admin.technoperchoir.fr`).
- K2 : `droits.technoperchoir.fr`, plus parlant pour le public.


**L. Contestation d'une qualification** ✅ L1 (validé par Max le 29/10/2026)

- L1 (**retenu**) : un lien « Contester cette qualification » sur chaque
  fiche texte, qui ouvre un courriel prérempli (titre, adresse de la
  fiche) vers une adresse dédiée. Rien à héberger, aucune donnée
  personnelle stockée. L'adresse se règle dans `site/src/lib/site.ts`
  (`CONTESTATION`) ; vide, le lien est masqué.
- L2 : formulaire stocké dans D1, lu dans l'admin (Turnstile contre le
  spam, mention RGPD). À reprendre à la passation.
- L3 : issue GitHub préremplie (exige un compte GitHub).

**M. Mise à jour des données AN** ✅ M1 (validé par Max le 29/10/2026)

- M1 (**retenu**) : Action GitHub hebdomadaire
  (`.github/workflows/donnees.yml`, lundi 4 h UTC, ou à la main) :
  `lvnd download` (archives en cache d'une semaine à l'autre, partielles
  comprises), `lvnd build`, `lvnd check`, commit de `data/export/` si tout
  passe (le site se redéploie), puis `lvnd sync-admin --remote`, devenu
  incrémental (quelques centaines de lignes écrites au lieu de 80 000).
  Cette dernière étape exige deux secrets GitHub : `CLOUDFLARE_API_TOKEN`
  (jeton « D1 : Edit » du compte) et `CLOUDFLARE_ACCOUNT_ID`. Sans eux,
  elle est sautée.
- M2 : à la main, d'après une procédure.
- M3 : Action sans l'admin.
