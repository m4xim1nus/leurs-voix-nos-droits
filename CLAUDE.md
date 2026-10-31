# CLAUDE.md

Guide pour Claude Code dans ce dépôt.

## Le projet

**Leurs voix, nos droits** montre comment les parlementaires votent sur
les textes qui touchent aux **droits et libertés** : libertés publiques,
police et justice, vie privée, droits des étrangers, discriminations,
droits sociaux, environnement, etc. Chaque texte retenu est **qualifié à
la main** : quels droits il touche, s'il les étend ou les restreint, et
sur quelles sources s'appuie ce jugement. Ses scrutins décisifs sont
ensuite croisés avec les votes des groupes et des députés.

Le modèle est leurs-votes.fr (Bon Pote, 2026). On s'en distingue sur
quatre points : on part du **texte** plutôt que de l'amendement isolé,
les règles de calcul sont **fixes et publiques**, chaque qualification
cite ses sources, et l'on peut chercher son député **par code postal**.

Le cadrage privé est dans `source/CADRAGE.md`, non versionné :
commanditaire, recherches du 29/10/2026, grille des droits v0, textes
témoins. En cas d'écart avec ce fichier, il prime.

## Décisions de cadrage (2026-10-29)

- **Phase « perso »** : dépôt GitHub public `m4xim1nus/leurs-voix-nos-droits`,
  site public sur un sous-domaine `technoperchoir.fr` (à choisir à
  l'étape 4). **Aucune mention du commanditaire** dans ce qui est
  versionné, publié ou commité : code, docs, site, messages de commit.
  Une passation (réécriture éditoriale, domaine définitif) viendra plus
  tard.
- **Stack alignée sur quifaitlaloi** (`~/dev/quifaitlaloi`) : Python 3.12
  + uv + polars → SQLite + JSON, site SvelteKit adapter-static + d3,
  Node 22. On copie et on adapte son code de téléchargement et de parsing
  AN (scrutins, dossiers, acteurs et organes, positions de groupe, 49.3 →
  motion de censure), sans dépendance entre les deux dépôts. En cas de
  doute sur une convention (build.sh, CI, tests), copier quifaitlaloi.
- **Deux couches de données** :
  - *open data*, produite en local par le pipeline : instantané versionné
    dans `data/` ;
  - *éditoriale* (qualifications), saisie dans l'**admin en ligne**.
- **Admin tout Cloudflare** : app SvelteKit (`admin/`, adapter-cloudflare),
  base **D1**, accès protégé par **Cloudflare Access** (code par
  courriel, pas de comptes à gérer). Le pipeline pousse le catalogue des
  textes et scrutins dans D1. L'admin y écrit les qualifications. Le
  bouton **« Publier »** commite l'export éditorial
  (`data/editorial.json`) dans le dépôt via l'API GitHub, ce qui relance
  le build du site public. D1 sert de brouillon, git garde l'historique
  publié, et chaque publication devient un diff lisible. Le NAS a été
  écarté : il dépend de la connexion de la maison et se transfère mal.
- **Site public** : Cloudflare Pages relié au dépôt. Son build ne
  télécharge rien : il lit `data/` (open data et `editorial.json`).
- **Périmètre v1** : Assemblée nationale, XVIe et XVIIe législatures
  (depuis juin 2022, comme leurs-votes.fr). Le Sénat et la XVe viennent
  ensuite, en cycles.
- **PISTE / Légifrance** : identifiants de compte dans `source/`. Le spike
  dira si l'API apporte quelque chose (texte au JO, décisions du Conseil
  constitutionnel) ; sinon, on s'en passe.

## Règles dures

- **Données de vote** : uniquement l'open data officiel (AN, puis Sénat).
  datan.fr et leurs-votes.fr servent au **contrôle croisé**, jamais de
  source primaire.
- **Qualifications** : chaque texte qualifié cite au moins une source
  publique (avis de la CNCDH ou du Défenseur des droits, décision du
  Conseil constitutionnel, analyse d'une ONG). Le site affiche la source
  à côté du jugement.
- **Choix sensibles validés par Max** : grille des droits, règles de
  calcul (abstention, absences, pondération des scrutins), sens d'un
  scrutin. On ne les tranche jamais seul, et ils figurent sur la page
  méthodologie. On préfère une règle fixe à un jugement au cas par cas.
- La position d'un groupe est sa position **majoritaire parmi les
  exprimés**, toujours affichée avec sa cohésion (règle de quifaitlaloi).
- Une abstention n'est **jamais** comptée comme un vote contre en
  silence. Son traitement suit la règle publiée.
- **Sources** : aucune publication du commanditaire n'est citée, ni seule
  ni cosignée (communiqué collectif, tribune, collectif dont il est
  membre). Décision de Max du 29/10/2026, à revoir à la passation. Les
  noms à exclure sont dans `source/CADRAGE.md` et
  `source/termes_interdits.txt` ; `lvnd check` et l'admin (secret
  `TERMES_INTERDITS`) refusent toute qualification qui les contient.
- Site public : **ton factuel**, méthodologie auditable, lisible par un
  non-spécialiste. Direction visuelle inspirée de Bon Pote **sans copie**
  (palette, polices et mise en page propres).
- FOSS, aucun tracker, aucun CDN tiers. Aucun secret dans le dépôt : les
  clés (PISTE, jeton GitHub de l'admin) vont dans `.env` ou dans les
  secrets Cloudflare.

## Arborescence

```
source/              cadrage privé + identifiants (non versionné)
data/raw/            dumps téléchargés (cache local, non versionné)
data/lvnd.sqlite     base open data (régénérée en local, non versionnée)
data/export/         JSON + CSV pour le site, l'admin et le téléchargement (versionnés),
                     dont tous les votes nominatifs : votes/<législature>/<AAAA-MM>.csv
                     et, à part, le Sénat : senat/ (votes : senat/votes/<AAAA-MM>.csv)
data/editorial.json  qualifications publiées, écrit par l'admin (versionné)
data/annuaire/       code postal → circonscription et département, courriels des députés (lvnd annuaire, versionné)
docs/SOURCES.md      fiche des sources (étape 1)
docs/METHODO.md      grille des droits et règles de calcul, base de la page Méthodologie
docs/CONCEPTION.md   conception du site public et de l'admin
docs/A_VALIDER.md    décisions préparées, en attente de Max (vidé au fil des arbitrages)
docs/QUALIFICATION.md  qualification par lots : rôles, circuit, consigne aux agents
pipeline/lvnd/       package Python (CLI download / build / check / editorial / scores / annuaire / sync-admin)
pipeline/explo/      scripts jetables (spike)
pipeline/referentiels/  YAML maintenus à la main (droits, mots-clés, groupes)
pipeline/tests/      pytest, dont les textes témoins
site/                site public : SvelteKit adapter-static + d3
admin/               admin : SvelteKit adapter-cloudflare + D1, derrière Cloudflare Access
                     (schéma dans admin/migrations/, mise en service dans admin/README.md)
build.sh             build Cloudflare Pages du site public (lvnd scores, puis le site ; aucun téléchargement)
```

`data/editorial.json` a le même format que `temoins.yaml`, sans les champs
que l'open data fournit. Le pipeline et l'admin le sérialisent à l'octet
près de la même façon, et un test croisé le vérifie. Tant que l'admin n'a
rien publié, il est généré depuis `temoins.yaml` (`lvnd editorial`).

## Suivi

Trois fichiers se partagent le suivi, sans recouvrement :

| Fichier | Rôle | Quand l'éditer |
|---|---|---|
| `ROADMAP.md` | Le **cycle en cours**, et lui seul : but, items détaillés, et ce qui est déjà fait *dans ce cycle*. Rien des cycles passés. | Pendant le cycle, et à chaque rotation. |
| `BACKLOG.md` | Les **cycles candidats**, les idées à trier ou à creuser, les tâches **refusées**. Rien de livré. Une ligne par item, `- [TAG] description (origine, date)`. | En cours de session : tout retour capté y va d'abord (fin de « À trier »). Tri en lot au début d'un cycle. |
| `CHANGELOG.md` | L'**historique** : ce qui a été livré, version par version (Keep a Changelog). | À chaque tag `v*`, et seulement là. |

Les cycles portent un nom court (Reliquat XVIe, Sénat, Passation…), jamais
un numéro de version ; la version se choisit au tag, d'après ce qui a été
livré.

**Rotation d'un cycle** (quand Max dit de le fermer) :

1. Écrire l'entrée de `CHANGELOG.md` (version, date, ce qui a été livré,
   limites connues), puis poser le tag.
2. Retirer de `BACKLOG.md` les items livrés par le cycle.
3. Remplacer le contenu de `ROADMAP.md` par le cycle suivant, choisi par
   Max parmi les cycles candidats, détaillé depuis ses items `[→Nom]`.

On travaille sur `main`. En début de session : `git pull`, car l'admin
commite sur `main` à chaque publication. On commite en nommant les
fichiers (`git add <chemins>`, jamais `git add -A`).

## Commandes

```bash
cd pipeline && uv sync              # environnement Python
cd pipeline && uv run lvnd download # dumps AN → data/raw/        (étape 2)
cd pipeline && uv run lvnd build    # → data/lvnd.sqlite + data/export/
cd pipeline && uv run lvnd check    # invariants, textes témoins, qualifications
cd pipeline && uv run pytest
cd pipeline && uv run lvnd scores   # scores seuls, depuis data/export/ et editorial.json (build.sh)
cd pipeline && uv run lvnd annuaire # data/raw/circos/ + AMO → data/annuaire/
cd pipeline && uv run lvnd sync-admin --local --editorial   # catalogue → D1 de l'admin (--remote en ligne)

cd admin && npm ci && npm run db:migrer && npm run dev     # admin en local (D1 émulée)
cd admin && npm run check && npm test && npm run format:check

cd site && npm ci && npm run dev    # site en local (copie data/ dans static/donnees/)
cd site && npm run check && npm test && npm run format:check
bash build.sh                       # build complet, comme Cloudflare Pages → site/build/
```
