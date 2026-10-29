# Admin

Qualification des textes et publication de `data/editorial.json`.
L'application est en SvelteKit (`adapter-cloudflare`), avec une base D1,
derrière Cloudflare Access. Conception, écrans et choix ouverts :
`docs/CONCEPTION.md`.

## Développement local

Aucun compte n'est nécessaire : wrangler émule D1 dans `admin/.wrangler/`,
et l'identité est `dev@localhost`.

```bash
cd admin
npm ci
npm run db:migrer                                   # schéma (migrations/)
(cd ../pipeline && uv run lvnd sync-admin --local --editorial)   # catalogue + qualifications publiées
npm run dev                                         # http://localhost:5173
```

`lvnd sync-admin` remplace le catalogue (textes, scrutins, groupes, grille)
à partir de `data/export/`. Avec `--editorial`, il ajoute les
qualifications d'`editorial.json` absentes de D1, sans jamais écraser un
brouillon. On peut le relancer après chaque `lvnd build`.

Contrôles :

```bash
npm run check          # svelte-check
npm test               # vitest, dont les tests croisés avec le pipeline et la publication sur D1 émulée
npm run format:check
```

## Mise en service (une fois)

Le compte Cloudflare doit être celui de la zone `technoperchoir.fr`.

1. Base D1 :
   ```bash
   npx wrangler login
   npx wrangler d1 create lvnd-admin      # reporter database_id dans wrangler.jsonc
   npm run db:migrer:distant
   (cd ../pipeline && uv run lvnd sync-admin --remote --editorial)
   ```
2. Jeton GitHub : un jeton _fine-grained_, limité au dépôt
   `m4xim1nus/leurs-voix-nos-droits`, avec la seule permission
   « Contents: read and write » et une expiration d'un an. Puis :
   ```bash
   npx wrangler secret put GITHUB_TOKEN
   ```
3. Domaine : ajouter une route personnalisée au Worker (dashboard
   Cloudflare, Workers, `lvnd-admin`, Domains & Routes), par exemple
   `admin.<sous-domaine du site>`. Aucune adresse `workers.dev` :
   `workers_dev` vaut `false`.
4. Cloudflare Access (Zero Trust, Access, Applications) : une application
   _self-hosted_ sur ce domaine. Politique « Allow » sur une liste de
   courriels, méthode de connexion « One-time PIN » (code par courriel).
   Reporter dans `wrangler.jsonc` :
   - `ACCESS_TEAM_DOMAIN` : `https://<équipe>.cloudflareaccess.com` ;
   - `ACCESS_AUD` : l'« Application Audience (AUD) Tag ».

   Sans ces deux valeurs, l'admin en ligne refuse toute requête : elle
   vérifie elle-même le jeton d'Access.

5. Déploiement : `npm run deploy`.

## Mettre à jour le catalogue en ligne

```bash
cd pipeline
uv run lvnd download && uv run lvnd build && uv run lvnd check
uv run lvnd sync-admin --remote
```

Un sync complet écrit environ 28 000 lignes dans D1 (limite gratuite :
100 000 par jour).
