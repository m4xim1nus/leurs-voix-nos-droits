# Roadmap

Projet sans calendrier engageant. Ce fichier est le **plan opérationnel** :
il porte le cycle en cours, et seulement lui. Ce qui est livré est dans
`CHANGELOG.md`, les cycles à venir et les idées dans `BACKLOG.md`. Règles
de tenue : `CLAUDE.md`, section « Suivi ».

## Cycle en cours : Recherche

Ouvert le 01/11/2026. Le but : une case de recherche sur toutes les pages, qui trouve les élu·es, les textes et sa circonscription depuis
l'étranger. Index statique chargé à la demande, sans serveur : aucune requête de recherche ne quitte le navigateur. Le travail se fait sur la
branche `recherche`, à la demande de Max (01/11/2026), qui garde la dernière validation avant la fusion dans `main` et la clôture.

### Décisions d'ouverture (prises par Claude en l'absence de Max, à confirmer à la validation)

- **Termes courants** : YAML dans `pipeline/referentiels/`, comme le recommandait le backlog. Ne touche ni la sérialisation d'`editorial.json`, ni
  l'admin, ni D1.
- **Surnoms de lois** : seulement ceux d'usage public, comme clé de recherche, sans affichage.

Les points à trancher avant la fusion sont dans `docs/A_VALIDER.md`.

### Garde-fous

- Rien ne change dans les scores ni dans `data/editorial.json`.
- Aucun CDN, aucun service tiers, aucune requête de recherche envoyée à un serveur en dehors des JSON statiques du site.
- Les termes et surnoms passent par le contrôle des termes interdits de `lvnd check`.

### Items

1. [x] **Pays → circonscription** : table du code électoral (tableau annexé, art. L. 330-1) en référentiel, vérifiée à la source.
2. [x] **Termes courants et surnoms** : référentiel, export, contrôles, puis saisie pour les textes qualifiés et les écartés connus.
3. [x] **Moteur et index** : index statique (élu·es, textes qualifiés, écartés avec leur motif, pays), moteur testé, hors scrutins et justifications.
4. [x] **Case dans l'en-tête**, sur toutes les pages, et page de résultats complète.
5. [ ] **Relecture** : mesure sur les termes témoins, à l'écran, poids de l'index, documentation. Faite par Claude le 01/11/2026 sur le build
   complet (bureau et mobile, Chromium) ; reste la relecture de Max et ses arbitrages.
