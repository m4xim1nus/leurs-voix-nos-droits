# Qualification par lots

Procédure suivie pour qualifier les textes au-delà des six témoins.
Elle a servi aux lots 1 à 6 et aux deux lots de tri (29/10/2026). Les règles de fond sont
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
   Pour **requalifier** un texte déjà validé ou écarté (règle nouvelle),
   ses brouillons vont dans un dossier à part, chargé avec
   `--brouillons ../source/brouillons-lotN-requalif --remplacer "requalification, lot N"`.
   Le texte repasse « à relire » et l'admin montre l'écart avec la
   version publiée. Celle-ci reste sur le site jusqu'à sa validation, même
   si d'autres textes sont publiés entre-temps.
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

**Un dossier neuf par chargement.** `--valider` et `--remplacer` prennent tous les
YAML du dossier. Vérifier avant que le nom n'est pas déjà pris, et que la page « Publier »
ne montre que les textes attendus. Le 30/10/2026, six écarts copiés dans un
`brouillons-tri` déjà rempli ont ainsi réécrit trois décisions plus récentes.
`--valider` affiche désormais la liste de ce qu'il écrit, et refuse d'écarter un texte
publié comme qualifié sans `--ecarter-publie`.

Le lot de tri (garder ou écarter des candidats en masse) suit le même
circuit. Ses brouillons ne portent que `statut: ecarte` et un
`motif_ecart` court, ou une simple liste « à qualifier » dans la fiche.

## Au fil de l'eau

Depuis le cycle « Au fil des votes », un nouveau vote se traite sans attendre
un lot : **un texte à la fois, dès l'alerte**. Rôles, règles et sources ne
changent pas, ni la validation par Max.

1. **L'alerte.** `lvnd check` (lignes `AVERTISSEMENT`) ou la file « À traiter »
   de l'admin :

   | Alerte | Ce qu'on fait |
   |---|---|
   | `vote_posterieur` | le nouveau vote devient le décisif (règle 9) : relire le sens sur le texte voté (règle 6) |
   | `unanimite_contestee` | revoir l'écart (règle 9) : qualifier, ou garder l'écart avec un motif à jour |
   | `premier_decisif` | qualifier, ou écarter avec son motif |
   | `inscrit` | rien à qualifier : le vote n'a pas eu lieu. On repère les sources utiles et on revient après le vote |

   Le mot est « inscrit », jamais « sera voté ». Aucun scrutin n'est retenu
   avant d'exister dans `data/export/scrutins.csv`.
2. **Le brouillon**, `source/brouillons-fil/<id>.yaml` (format de la consigne
   ci-dessous). Claude le prépare lui-même, sans agent ni lot. Un texte déjà
   qualifié repart de sa version publiée : on ne touche qu'à ce que le nouveau
   vote change, et on revérifie les sources sur le texte voté. Pour un texte
   composite (règle 4), le décompte des sources se refait après le vote.
3. **Le contrôle**, comme pour un lot (étape 3 du circuit).
4. **Le chargement « à relire ».** Texte nouveau : `--brouillons`. Texte déjà
   validé ou écarté : `--brouillons … --remplacer "requalification, vote du JJ/MM/AAAA"`.
   Le dossier ne contient que les YAML du texte en cours. La version publiée
   reste sur le site jusqu'à la validation.
5. **La fiche courte**, dans le chat, pas dans un fichier : scrutin et décompte,
   droit principal et sens proposé (avec ce qui a changé depuis le texte
   précédent), sources avec un extrait lu, points d'attention. Faute de source
   admise, la fiche le dit et le texte attend.
6. **La décision de Max**, texte par texte, puis la validation et la
   publication, comme aux étapes 6 à 8 du circuit. Le commentaire de validation
   dit : « validé par Max (au fil de l'eau, JJ/MM/AAAA) ».

Pour retirer un texte du site, on l'écarte avec son motif. Le repasser en
brouillon ne suffit pas : sa version publiée reste en ligne.

### Fiche de suivi, avant le vote

Pour un texte inscrit ou attendu, sans vote qualifié, que Max retient à la main
(les mots-clés ne font que présélectionner). Elle donne les droits touchés et
les sources publiques, **sans sens ni score, et sans aucun scrutin**.

1. **Le brouillon**, `source/brouillons-suivi/<id>.yaml` : `statut: a-suivre`, et
   pour chaque droit `{ code, sources, justification }`, sans `role` ni `sens`.
   La justification dit ce que le texte touche, sans dire s'il étend ou restreint.
   Les règles 2, 3 et 7 s'appliquent ; `scrutins` reste vide.
2. **Faute de source admise, la fiche de relecture le dit et le texte attend** :
   rien n'est publié sur lui. Une source peut porter sur la mesure (règle 7).
3. **Le circuit** est celui d'un texte au fil de l'eau : chargement « à relire »,
   décision de Max texte par texte, validation
   (`--brouillons … --valider "validé par Max (suivi, JJ/MM/AAAA)"`, statut
   `a-suivre` lu dans le YAML), puis « Publier ».
4. **Après le vote**, l'alerte `premier_decisif` reste affichée : on qualifie le
   texte ou on l'écarte, et sa fiche de suivi disparaît d'elle-même de `suivis`.

### Vote du Sénat (règles 23 à 28)

Le vote du Sénat s'ajoute à la qualification d'un texte, dans un bloc `senat`. Tant que l'admin ne
sait pas le lire (cycle Sénat, étape 3), les brouillons restent dans `source/brouillons-senat-*/`, sans
chargement dans D1 et sans validation.

```yaml
id: justice-mineurs              # id publié, ou nouvel id si le texte n'est pas qualifié
dossier_an: DLR5L17N50690
senat:
  version: meme                  # meme : texte du décisif de l'AN ; autre : version propre au Sénat ; seul : pas de décisif à l'AN
  scrutins:
    - { id: SN2024-289, role: decisif, pour: texte, objet: "ensemble, conclusions de la CMP (223-112)" }
    - { id: SN2024-243, role: ensemble, pour: texte, objet: "ensemble, 1re lecture (227-113)" }
  droits: []                     # version autre : droits, sens et sources propres, au format habituel
  etiquettes: []                 # version autre, comme droits, sources et vigilance
  vigilance: []
  sources: {}
  note: ""
relecture: { points_attention: [], extraits: [] }
```

Seul `role: decisif` est compté. Un décisif unanime, ou sans source admise sur sa version, reste en
`role: ensemble`, sans droits ni sens, et la `note` dit pourquoi. Un texte sans qualification à l'AN porte en plus les champs
habituels (`titre`, `resume`, `droits`, `sources`, `scrutins: []`), et ses droits valent pour le texte
voté au Sénat.

Les `scores_*.csv` ne changent qu'à la publication d'une qualification validée.
Tant que Max n'a pas validé, ils restent identiques à l'octet, même si un
nouveau vote est au catalogue.

## Consigne aux agents de recherche (à leur donner telle quelle)

Projet : **Leurs voix, nos droits** (`/home/max/dev/leurs-voix-nos-droits`). Le site montre comment
les députés votent sur les textes qui touchent aux droits et libertés. Chaque texte est
**qualifié à la main** : droits touchés, sens (étend / restreint), sources publiques, scrutins
retenus. Tu prépares des **brouillons** que Max (non juriste) relira et validera un par un : ton
travail doit être factuel, sourcé, vérifiable, et signaler franchement les points incertains.

### À lire d'abord (lecture seule, ne modifie aucun fichier du dépôt)

- `docs/METHODO.md` : règles 1 à 13 (qualification et scrutins) — **à appliquer strictement**,
  en particulier : 1 (point de vue des personnes), 2 (périmètre ; propriété, ordre public et choix
  d'une source d'énergie hors grille ; inégalité de revenu hors de `discriminations`, en vigilance ;
  droits civiques dans `citoyennete`, grille v1 : qui vote et
  qui est élu, conditions du vote, mais ni le mode de scrutin ni le régime des mandats), 3
  (recouvrements ; mesure qui ne vise que des détenus → droit en cause principal, `police-justice`
  secondaire), 4 (sens droit par droit, un droit principal ; corps électoral : `citoyennete` selon
  le droit de vote des personnes, `discriminations` restreint si une source y voit une atteinte aux
  droits d'un peuple autochtone ; sens lu par rapport au droit
  applicable au jour du vote, jurisprudence comprise (rétablir une règle abrogée par le Conseil
  constitutionnel restreint ; le droit du jour comprend son échéance légale : prolonger un dispositif
  protecteur étend) ; texte composite : sens des mesures que les
  sources citent le plus, la mesure opposée en vigilance), 5 (vigilance), 6 (on qualifie le texte
  soumis au scrutin décisif), 7 (sources admises, dont les instances consultatives indépendantes,
  l'ANSES, le HCFEA, l'UNAF (statut signalé), une association porteuse d'un dispositif pour en décrire
  un risque (signalée partie prenante), les syndicats représentatifs de salariés, leurs fédérations,
  leurs syndicats nationaux de branche affiliés et leurs unions confédérales de retraités, les syndicats et ordres
  du droit, de la santé et de l'enseignement, les avis du Conseil d'État ; une source peut porter
  sur la mesure plutôt que sur le texte ; **jamais** un rapport parlementaire, la Cour des comptes
  ni la position du Gouvernement ou d'un groupe ; si le texte **étend** un droit contesté, au
  moins une source critique en vigilance, et sinon la note dit « aucune critique trouvée parmi les
  sources admises »), 8 (non qualifiés → « écarté » : texte purement organisationnel, résolution,
  convention internationale, motion de censure spontanée, loi de finances de fin de gestion, texte vidé de toute mesure normative au
  scrutin décisif ; une réforme de structure mise en cause par une source admise au nom d'un droit de la grille
  reste qualifiable), 9 (décisif = dernier vote de l'AN sur l'ensemble ; vote sans scrutin public : le
  dernier scrutin public reste décisif, avec mention ; rejet d'une partie d'une loi de finances sans
  vote sur l'ensemble : affiché, pas décisif ; à défaut, pour un article
  unique, le vote sur l'article ou l'amendement adopté qui le supprime, voter pour allant alors
  contre le texte ; décisif sans aucune voix d'un côté → écarté ; texte adopté par 49.3 sans vote
  final : qualifié, compté dans aucun score, motions de censure en rôle `censure`), 10 (motions
  affichées, pas comptées), 11 (amendements clés : seulement suppression ou rétablissement d'un
  article dont la mesure est **mise en cause** par une source — une source favorable, une critique
  d'insuffisance ou une décision qui valide la mesure ne suffisent pas ; article mixte, au sens non
  univoque, ou dont les sources ne s'accordent pas sur le sens → non retenu ; **une seule lecture : la dernière lecture de l'AN où des suppressions
  ont été mises aux voix** ; un seul scrutin par article ; l'article qui est le seul du texte au
  décisif compte comme un article unique ; le sens se lit sur le contenu de
  l'article).
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
  reprend un texte cosigné, ne la cite pas. En revanche, une décision de
  justice qui nomme seulement l'organisation comme partie, ou un document
  qui emploie un sigle homonyme, n'est pas une publication de celle-ci :
  cite-le, sans jamais écrire le nom (`lvnd check` le refuserait). De même,
  le document d'une source admise qui nomme l'organisation (partie à un
  recours, constat cité en note) reste citable, pourvu que le passage cité
  n'en reprenne rien ; signale-le dans les points d'attention.
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

Pour une **fiche de suivi** (texte sans vote qualifié) : `statut: a-suivre`, `scrutins: []`, et pour
chaque droit `{ code, sources, justification }`, sans `role` ni `sens`. La justification dit ce que le
texte touche, sans dire s'il étend ou restreint. Sans source admise, ne rédige pas de fiche : dis-le dans
ton compte rendu. Vérifie aussi la liste des signataires d'un document collectif avant de le citer.

Règles de format :
- `objet` de chaque scrutin se termine par le décompte `(pour-contre)` exact du CSV.
- Retiens : le décisif (en principe `decisif_propose` ; vérifie la règle 9), les autres votes sur
  l'ensemble (`ensemble`), les motions de rejet (`motion`), et les amendements clés de la règle 11
  (0 si aucun ne remplit les conditions — c'est fréquent ; dis pourquoi dans `note`).
- Texte adopté par 49.3 sans vote final (règle 9) : pas de décisif ; retiens les motions de
  censure votées sur ce texte (`role: censure, pour: contre-texte`), même rattachées à un autre
  dossier du catalogue.
- Chaque droit a au moins une source ; toute clé citée est définie ; un seul droit principal.
- Texte non adopté ou sans scrutin décisif clair : applique la règle 9 et signale-le.

### Compte rendu final (ta réponse)

Pour chaque texte : l'id, le statut proposé, droit principal et sens en une ligne, le nombre de
scrutins comptés, et les points d'attention majeurs. Puis la liste de ce que tu n'as pas pu
vérifier. Réponds en français.
