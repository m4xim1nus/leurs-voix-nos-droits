#!/usr/bin/env bash
# Build exécuté par Cloudflare Pages à chaque push sur main : construit le site statique dans
# site/build/ à partir de l'instantané versionné (data/export/, data/editorial.json,
# data/annuaire/). Aucun dump n'est téléchargé ici : l'open data se régénère en local
# (`lvnd download && lvnd build`), puis se commite (CLAUDE.md, décisions de cadrage).
#
# Seuls les scores sont recalculés (`lvnd scores`, choix F1 de docs/CONCEPTION.md) : une
# publication depuis l'admin, qui ne change que data/editorial.json, met ainsi le site à jour.
# Reproductible : `bash build.sh`.
set -euo pipefail
cd "$(dirname "$0")"
node --version

test -f data/editorial.json && test -f data/export/meta.json && test -f data/annuaire/codes_postaux.csv

echo "== Scores"
if ! command -v uv > /dev/null; then
  python3 -m pip install --quiet --user uv
  export PATH="$HOME/.local/bin:$PATH"
fi
(cd pipeline && uv run --quiet --no-dev lvnd scores)

echo "== Site"
cd site
npm ci --no-audit --no-fund
npm run build
echo "Fichiers dans site/build/ : $(find build -type f | wc -l)"
test -f build/index.html && test -f build/404.html && test -f build/_headers
test -f build/donnees/editorial.json && test -f build/recherche/deputes.json
