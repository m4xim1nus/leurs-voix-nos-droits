# Qualification par lots

Procédure suivie pour qualifier les textes au-delà des six témoins.
Elle a servi au lot 1 (21 textes, 29/10/2026). Les règles de fond sont
celles de `docs/METHODO.md`. Le circuit est celui de l'admin
(`docs/CONCEPTION.md`) : D1 sert de brouillon, la publication vaut commit.

## Rôles

- **Claude prépare** : choix des textes, recherche des sources (avec
  citations lues), proposition de jugement et de scrutins. Il contrôle
  ensuite chaque brouillon et rédige la fiche de relecture.
- **Max arbitre** : il relit la fiche et répond dans le chat, texte par
  texte (« ok », « écarter », « changer X »). Il tranche aussi les
  questions transversales, qui deviennent des règles de `METHODO.md`. Une
  qualification ne passe jamais à « validé » sans sa réponse explicite.
- **Max publie** : il clique sur « Publier » dans l'admin
  (https://lvnd-admin.technoperchoir.fr).

## Circuit d'un lot

1. **Choisir les textes.** Dans le catalogue (`data/export/textes.csv`),
   prendre les candidats par mots-clés, non encore qualifiés ni écartés.
   Les qualifications déjà dans D1 se lisent avec
   `npx wrangler d1 execute lvnd-admin --remote --command "select dossier_an, statut from qualifications"`,
   depuis `admin/`. Grouper par thème, cinq textes au plus par agent.
2. **Recherche.** Un agent par thème (outil Agent, en arrière-plan), à
   qui l'on donne la consigne ci-dessous et sa liste de dossiers. Chacun
   écrit `source/brouillons-lotN/<id>.yaml` (non versionné).
3. **Contrôle par Claude**, sur chaque brouillon :
   `editorial.valider` avec les infos du catalogue (dossier, étape,
   division, objet, pour, contre) ; décomptes `(pour-contre)` conformes ;
   `check.termes_interdits` vide ; URL qui répondent ; identifiants
   uniques. Corriger, ou renvoyer à l'agent.
4. **Chargement « à relire ».**
   `cd pipeline && uv run lvnd sync-admin --remote --brouillons ../source/brouillons-lotN`
   (puis `--local`). Cette commande ne réécrit pas le catalogue et
   n'écrase rien. Une proposition d'écart arrive elle aussi « à relire ».
5. **Fiche de relecture** : `source/relecture-lotN.md` (non versionnée,
   elle peut nommer le commanditaire). En tête : un tableau récapitulatif
   et les questions transversales, avec une recommandation chacune.
   Puis, par texte : jugement, scrutins comptés, sources, extraits lus,
   points d'attention, lien vers l'admin. Modèle : `source/relecture-lot1.md`.
6. **Décisions de Max**, dans le chat. Claude reporte les changements dans
   les YAML, puis les règles nouvelles dans `METHODO.md`, et dans les
   contrôles quand c'est possible (admin et pipeline à l'identique).
7. **Validation**, seulement sur réponse explicite de Max :
   `uv run lvnd sync-admin --remote --brouillons ../source/brouillons-lotN --valider "validé par Max (lot N, JJ/MM/AAAA)"`
   (puis `--local`). Les textes passent à « validé », ou « écarté » avec
   leur motif, et une révision en garde la trace.
8. **Publication** : Max clique sur « Publier ». Ensuite, `git pull` dans
   chaque copie de travail.

Le lot de tri (garder ou écarter des candidats en masse) suit le même
circuit. Ses brouillons ne portent que `statut: ecarte` et un
`motif_ecart` court, ou une simple liste « à qualifier » dans la fiche.

## Consigne aux agents de recherche (à leur donner telle quelle)

Projet : **Leurs voix, nos droits** (`/home/max/dev/leurs-voix-nos-droits`). Le site montre comment
les députés votent sur les textes qui touchent aux droits et libertés. Chaque texte est
**qualifié à la main** : droits touchés, sens (étend / restreint), sources publiques, scrutins
retenus. Tu prépares des **brouillons** que Max (non juriste) relira et validera un par un : ton
travail doit être factuel, sourcé, vérifiable, et signaler franchement les points incertains.

### À lire d'abord (lecture seule, ne modifie aucun fichier du dépôt)

- `docs/METHODO.md` : règles 1 à 13 (qualification et scrutins) — **à appliquer strictement**,
  en particulier : 1 (point de vue des personnes), 2 (périmètre ; propriété et ordre public hors
  grille), 3 (recouvrements), 4 (sens droit par droit, un droit principal), 5 (vigilance), 6
  (on qualifie le texte soumis au scrutin décisif), 7 (sources admises ; si le texte **étend** son
  droit principal, au moins une source critique en vigilance), 8 (texte purement organisationnel
  : non qualifié → « écarté »), 9 (décisif = dernier vote de l'AN sur l'ensemble), 10 (motions
  affichées, pas comptées), 11 (amendements clés : seulement suppression ou rétablissement d'un
  article dont la mesure est **mise en cause** par une source ; **une seule lecture : la dernière
  lecture de l'AN où des suppressions ont été mises aux voix** ; un seul scrutin par article ; le
  sens se lit sur le contenu de l'article).
- `pipeline/referentiels/droits.yaml` : la grille (codes de droits et d'étiquettes autorisés).
- `pipeline/referentiels/temoins.yaml` : **six exemples validés** — imite leur niveau d'exigence,
  leur ton et leur format.

### Données du dépôt (lecture seule)

- `data/export/textes.csv` : catalogue (colonne `id` = dossier AN, `decisif_propose`, loi,
  décision du Conseil constitutionnel `cc_decision`, `url_an`).
- `data/export/scrutins.csv` : tous les scrutins ; filtre `dossier_id` = le dossier. Colonnes
  utiles : `id`, `numero`, `date`, `titre`, `objet` (ensemble, amendement, article, motion_rejet…),
  `etape` (AN1, AN2, CMP, ANNLEC, ANLDEF…), `sort`, `pour`, `contre`. Le titre d'un scrutin sur
  amendement dit « l'amendement de suppression n° X … à l'article Y ».
- `data/export/positions_groupes.csv` : positions des groupes par scrutin, si utile.

### Recherche

- Sources primaires uniquement, consultées en ligne (WebFetch / WebSearch) : avis CNCDH, Défenseur
  des droits, CNIL, CGLPL, décision du Conseil constitutionnel (conseil-constitutionnel.fr),
  rapporteurs ONU, ONG reconnues (Amnesty, La Quadrature du Net, la Cimade… — cite l'ONG qui a publié l'analyse, sans préférence ; privilégie les autorités indépendantes quand elles se sont prononcées),
  ordres et sociétés savantes pour la santé ; textes de l'AN pour le contenu des articles.
- **N'invente jamais une URL, une date, un numéro d'avis ou une citation.** Chaque citation entre
  « » doit avoir été lue dans le document. Si tu n'as pas pu ouvrir un document, dis-le.
- **Aucune publication du commanditaire**, ni seule ni cosignée (communiqué
  collectif, tribune, collectif dont il est membre) : liste privée dans
  `source/termes_interdits.txt` (CLAUDE.md, règles dures). Si une analyse
  reprend un texte cosigné, ne la cite pas.
- Des sources de bords différents sont bienvenues ; si une source institutionnelle soutient le
  texte ou en relativise la portée, mentionne-le dans les points d'attention.

### Livrable : un fichier YAML par texte

Écris ``source/brouillons-lotN/<id>.yaml``
(`<id>` : identifiant lisible, minuscules et tirets, ex. `sren-2024`), au format d'une entrée de
`temoins.yaml`, **sans** `loi` ni `conseil_constitutionnel` en objet, mais avec :

```yaml
id: sren-2024
dossier_an: DLR5L16N47884
legislature: 16
titre: "Loi visant à sécuriser et réguler l'espace numérique"   # titre officiel de la loi
statut: a-relire            # ou « ecarte » (règle 8 ou hors grille), avec motif_ecart
motif_ecart: null
resume: "Une ou deux phrases factuelles : ce que fait le texte."
droits:
  - { code: vie-privee, role: principal, sens: restreint, sources: [cle1], justification: "…" }
etiquettes: []
vigilance: []               # { texte: "…", sources: [clé] }
conseil_constitutionnel: "Résumé factuel de la décision (censures, réserves), ou vide."
note: "Note de méthode publique : choix des scrutins, amendements écartés et pourquoi."
sources:
  cle1: { auteur: CNIL, titre: "…", date: 2023-05-01, url: "https://…" }
scrutins:
  - { id: VTANR5L16V3668, role: decisif, pour: texte, objet: "ensemble, … (pour-contre)" }
  - { id: VTANR5L16V…, role: motion, pour: contre-texte, objet: "motion de rejet préalable, … (pour-contre)" }
  - { id: VTANR5L16V…, role: amendement, pour: contre-texte, objet: "suppression de l'article …, … (pour-contre)" }
relecture:                  # pour Max, non publié
  points_attention: ["…"]   # incertitudes, choix discutables, sources fragiles
  extraits: ["clé1 : « citation courte lue dans la source »", "…"]
```

Règles de format :
- `objet` de chaque scrutin se termine par le décompte `(pour-contre)` exact du CSV.
- Retiens : le décisif (en principe `decisif_propose` ; vérifie la règle 9), les autres votes sur
  l'ensemble (`ensemble`), les motions de rejet (`motion`), et les amendements clés de la règle 11
  (0 si aucun ne remplit les conditions — c'est fréquent ; dis pourquoi dans `note`).
- Chaque droit a au moins une source ; toute clé citée est définie ; un seul droit principal.
- Texte non adopté ou sans scrutin décisif clair : applique la règle 9 et signale-le.

### Compte rendu final (ta réponse)

Pour chaque texte : l'id, le statut proposé, droit principal et sens en une ligne, le nombre de
scrutins comptés, et les points d'attention majeurs. Puis la liste de ce que tu n'as pas pu
vérifier. Réponds en français.
