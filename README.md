# Leurs voix, nos droits

Comment les parlementaires votent-ils sur les textes qui touchent aux
droits et libertés ? Libertés publiques, police et justice, vie privée,
droits des étrangers, discriminations, droits sociaux, environnement…

Chaque texte retenu est qualifié à la main : droits touchés, sens
(extension ou restriction), sources. Ses scrutins décisifs sont croisés
avec les votes des groupes et des députés de l'Assemblée nationale
depuis 2022, et, à part, avec ceux du Sénat. La méthodologie et les données sont publiques.

**État** : v1.3.0 en ligne sur [lvnd.technoperchoir.fr](https://lvnd.technoperchoir.fr)
(Assemblée nationale, XVIe et XVIIe législatures ; Sénat depuis juin 2022). Voir
[`CHANGELOG.md`](CHANGELOG.md) et [`ROADMAP.md`](ROADMAP.md).

## Sources

Données de vote : open data officiel de l'Assemblée nationale
([data.assemblee-nationale.fr](https://data.assemblee-nationale.fr)).

## Contribuer

Prérequis : Python 3.12 avec [uv](https://docs.astral.sh/uv/), Node 22.
La conduite du projet (règles, arborescence, commandes) est dans
[`CLAUDE.md`](CLAUDE.md), la méthode dans [`docs/METHODO.md`](docs/METHODO.md).

Trois niveaux, selon ce que l'on touche :

- **Site public** : il lit les données versionnées de `data/`, rien à
  télécharger.

  ```bash
  cd site && npm ci && npm run dev
  bash build.sh   # build complet, comme Cloudflare Pages → site/build/
  ```

- **Pipeline** : il part des dumps de l'Assemblée (≈ 2,8 Go dans
  `data/raw/`, non versionnés) et reconstruit `data/lvnd.sqlite` et
  `data/export/`.

  ```bash
  cd pipeline && uv sync
  uv run lvnd download && uv run lvnd build && uv run lvnd check
  uv run pytest
  ```

  Limite connue : le serveur de l'AN ne sert pas le dump des amendements
  de la XVIe (`an_amendements_16`), et `lvnd check` échoue sur cette
  seule ligne tant qu'il manque (`CHANGELOG.md`).

- **Admin en local** (D1 émulée) : il faut d'abord `data/lvnd.sqlite`
  (niveau précédent). Pour qualifier, l'admin en ligne suffit.

  ```bash
  cd admin && npm ci && npm run db:migrer
  cd ../pipeline && uv run lvnd sync-admin --local --editorial
  cd ../admin && npm run dev
  ```

Le dossier `source/` (cadrage privé, liste des termes interdits dans les
qualifications) n'est pas versionné : il se reçoit à part et se pose à
la racine du clone. Sans `source/termes_interdits.txt`, `lvnd check`
saute ce contrôle sans le signaler. Avant de pousser :
`npm run check && npm test && npm run format:check` dans `site/` et
`admin/`, et `uv run pytest` dans `pipeline/`.

## Licence

Code sous licence MIT. Les données dérivées sont publiées sous
[Licence Ouverte 2.0](https://www.etalab.gouv.fr/licence-ouverte-open-licence/).
