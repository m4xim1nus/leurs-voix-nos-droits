# Conception

Conception de l'admin (étape 3), puis du site public (étape 4, à venir).
Les choix A à F de l'admin ont été validés par Max le 29/10/2026 : à
chaque fois l'option recommandée (✅). Les autres options sont gardées
pour mémoire.

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
  versionné, donc une GitHub Action pourra un jour lancer ce sync sans
  dump (`BACKLOG.md`, mise à jour automatique). Un sync complet écrit
  environ 28 000 lignes, sous la limite gratuite de D1 (100 000 par jour).
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
   publication, avec leurs contrôles. Le bouton ouvre un commit. Liste
   des publications passées (date, auteur, lien vers le commit).
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

À concevoir à l'étape 4.
