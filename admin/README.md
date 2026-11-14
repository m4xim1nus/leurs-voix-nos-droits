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
printf 'ACCESS_TEAM_DOMAIN=""\n' > .dev.vars         # sans Access en local (sinon 403 : wrangler.jsonc le déclare)
(cd ../pipeline && uv run lvnd sync-admin --local --editorial)   # catalogue + qualifications publiées
npm run dev                                         # http://localhost:5173
```

`lvnd sync-admin` met le catalogue (textes, scrutins, groupes, grille) à
jour à partir de `data/export/`, en n'écrivant que les différences avec D1
(`--complet` pour tout réécrire, `--simuler` pour compter sans écrire). Avec `--editorial`, il ajoute les
qualifications d'`editorial.json` absentes de D1, sans jamais écraser un
brouillon. On peut le relancer après chaque `lvnd build`.

Une nouvelle migration (`migrations/`) s'applique en ligne avant le prochain
`lvnd sync-admin --remote`, y compris celui de l'Action « Données AN » :
`npm run db:migrer:distant`. Sans cela, le sync échoue sur la table absente.

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

5. Premier déploiement : `npm run deploy`. Ensuite, voir « Déploiement ».

6. LLM (facultatif, page « LLM » de l'admin) : un secret qui chiffre la clé d'API dans D1, à poser
   à l'identique dans le Worker et dans les secrets du dépôt GitHub (l'Action des propositions le
   lit pour déchiffrer la clé) :
   ```bash
   openssl rand -base64 32                 # une valeur, gardée hors du dépôt
   npx wrangler secret put LLM_CHIFFREMENT
   gh secret set LLM_CHIFFREMENT
   ```
   Sans lui, l'admin fonctionne, mais refuse de saisir une clé. Changer la valeur rend la clé
   enregistrée illisible : la ressaisir. En local, ajouter `LLM_CHIFFREMENT="local"` à `.dev.vars`.

## Mettre à jour le catalogue en ligne

```bash
cd pipeline
uv run lvnd download && uv run lvnd build && uv run lvnd check
uv run lvnd sync-admin --remote
```

Le sync est incrémental : il lit D1, puis n'écrit que les lignes
ajoutées, modifiées ou disparues (quelques centaines par semaine). Un sync
`--complet` écrit environ 80 000 lignes, index compris, près de la limite
gratuite de D1 (100 000 par jour) : à réserver à une reconstruction.

## Déploiement

L'admin se déploie à la main, jamais depuis une Action : aucun secret de
déploiement n'est dans GitHub. Le titulaire du compte Cloudflare déploie
après `npx wrangler login`. Un co-mainteneur le fait avec un jeton d'API
personnel, sans accès au compte :

1. Le titulaire crée le jeton (Cloudflare, My Profile, API Tokens, Create
   Custom Token), au nom de la personne, avec une expiration :
   - Account (le seul compte de `technoperchoir.fr`) : « Workers Scripts :
     Edit » et « D1 : Edit » ;
   - Zone `technoperchoir.fr` : « Workers Routes : Edit » (domaine du
     Worker).

   Il le transmet par un canal chiffré, jamais par courriel ni dans le
   dépôt, et le révoque au départ de la personne.
2. Le co-mainteneur le pose dans `admin/.env`, ignoré par git :
   ```bash
   CLOUDFLARE_API_TOKEN=…
   CLOUDFLARE_ACCOUNT_ID=…   # l'identifiant du compte, donné avec le jeton
   ```

Déployer, depuis `main` à jour, sans modification locale, après la fusion
de la PR :

```bash
git switch main && git pull && git status   # rien à commiter
cd admin && npm ci
set -a && . ./.env && set +a                 # inutile après wrangler login
npm run db:migrer:distant                    # migrations d'abord : le code peut lire une table neuve
npm run deploy
```

Les secrets du Worker (`GITHUB_TOKEN`, `LLM_CHIFFREMENT`) ne sont pas
nécessaires : `wrangler deploy` garde ceux qui sont en place. Le jeton
donne la main sur tous les Workers et toutes les bases D1 du compte :
c'est la limite des jetons Cloudflare, qui ne se restreignent pas à un
seul Worker.
