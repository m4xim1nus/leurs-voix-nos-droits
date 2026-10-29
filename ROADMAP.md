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

## Étape 1 : spike sources et grille ← *en cours*

But : vérifier que les données suivent et que la grille tient sur des cas
réels. C'est le **go/no-go**. Scripts jetables dans `pipeline/explo/`.

- **Données AN** : reprendre le téléchargement de quifaitlaloi (scrutins,
  dossiers, acteurs et organes, XVIe et XVIIe). Mesurer le volume des
  votes nominatifs (≈ 1,37 M lignes pour la XVIIe), puis trancher : tout
  versionner sous forme compacte, ou seulement les scrutins candidats. Le
  critère : qualifier un nouveau scrutin dans l'admin ne doit pas exiger
  de relancer le pipeline.
- **Rattachement** : vérifier que chaque amendement mis aux voix se
  rattache à son dossier, avec son auteur et son groupe.
- **Code postal → circonscription** : trouver la table officielle
  (communes ↔ circonscriptions législatives) et repérer les communes à
  cheval sur plusieurs circonscriptions.
- **PISTE** : créer l'application, obtenir les clés et tester un appel.
  Verdict : l'API apporte-t-elle quelque chose (lien JO, décisions du
  Conseil constitutionnel), oui ou non ?
- **Grille v0** : valider avec Max les dix droits de `source/CADRAGE.md`
  §3. Les qualifier à la main sur **six textes témoins** (JO 2024,
  immigration 2024, Kasbarian-Bergé, narcotrafic, justice des mineurs,
  aide à mourir), dans un simple YAML. Pour chacun : droits touchés,
  sens, sources, puis scrutins retenus (ensemble, motion de censure,
  amendements clés) avec le sens d'un vote « pour ».
- **Contrôle croisé** : positions de groupe comparées à datan.fr et au
  `dataset.json` public de leurs-votes.fr sur les scrutins communs.
- **Livrable** : `docs/SOURCES.md`, la grille v0 validée
  (`pipeline/referentiels/droits.yaml`), les six textes témoins qualifiés
  et un verdict go/no-go.

## Étape 2 : pipeline et méthode v0

But : une base fiable des textes, scrutins et votes, et des règles de
calcul arrêtées.

- Package `lvnd` (`download` → `build` → `check`), qui écrit
  `data/lvnd.sqlite` et `data/export/`.
- **Catalogue des candidats** : présélection des textes et scrutins par
  mots-clés (`referentiels/mots_cles.yaml`). Elle sert d'aide au tri dans
  l'admin, jamais de qualification automatique.
- **Scores** calculés depuis une qualification (le YAML de l'étape 1 en
  attendant l'admin) : par député, par groupe et par droit.
- **Méthode v0** dans `docs/METHODO.md`, chaque règle **tranchée par
  Max** : abstention, absences, pondération (un texte à vingt amendements
  ne doit pas écraser les autres), votes du député quand il change de
  groupe.
- **Livrable** : `docs/METHODO.md` v0, les scores des six textes témoins
  relus avec Max, `lvnd check` vert.

## Étape 3 : admin en ligne

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
- **Livrable** : admin en ligne, les six textes témoins ressaisis, et une
  vingtaine de textes qualifiés par Max à travers elle.

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
