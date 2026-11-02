# Roadmap

Projet sans calendrier engageant. Ce fichier est le **plan opérationnel** :
il porte le cycle en cours, et seulement lui. Ce qui est livré est dans
`CHANGELOG.md`, les cycles à venir et les idées dans `BACKLOG.md`. Règles
de tenue : `CLAUDE.md`, section « Suivi ».

## Cycle en cours : Pré-qualification

Ouvert le 02/11/2026. **But** : que le traitement hebdomadaire ne parte plus d'une feuille blanche, et qu'il puisse tourner
sans Claude Code. Après chaque passe de données, un LLM appelé par API prépare une proposition pour chaque nouvelle alerte,
et une veille hebdomadaire signale les sources nouvelles. Tout arrive dans « À traiter », repensé pour cela.

**Garde-fous**, valables pour tout le cycle :

- le LLM **propose**, il ne valide ni ne publie jamais. Chaque proposition dit qu'elle vient de lui. Un cas que les règles ne
  prévoient pas remonte à un humain, sans règle inventée ;
- l'admin reste **entièrement utilisable sans LLM** : interrupteur coupé, clé absente ou expirée, plafond atteint, Action en
  échec. « À traiter » montre alors les alertes et les notes, comme aujourd'hui ;
- une proposition ne touche jamais une qualification publiée : elle est rangée à part, et seul un humain la charge ;
- aucun nom de la liste d'exclusion dans un prompt ; contrôles sans LLM avant qu'une proposition n'apparaisse.

**Architecture retenue.** Les appels partent d'une **Action GitHub à part**, lancée après chaque passe de données : un échec ou
un plafond atteint n'y touche pas. L'**admin pilote** : interrupteur, clé, plafond et consommation vivent dans D1, que l'Action
lit avant tout appel et où elle journalise chacun. Pas d'assistant dans l'admin (refusé le 30/10/2026) : son seul appel
direct à l'API est le test d'une clé saisie.

### Items

1. **Réglages LLM dans l'admin** (nouvelle page, migration D1 `0007`). Interrupteur général. Clé : saisie, testée par un
   appel sans coût (liste des modèles), stockée **chiffrée** (AES-GCM, secret `LLM_CHIFFREMENT` partagé par le Worker et
   l'Action), jamais réaffichée : seuls ses derniers caractères, la date et l'auteur de la saisie. Plafond mensuel en
   dollars, modèle. Consommation : journal des appels (tâche, texte, jetons, recherches web, coût estimé), total du mois,
   jauge du plafond. Le plafond de l'admin est un frein ; le vrai butoir est la limite de dépense du workspace dédié, dans la
   console Anthropic.
2. **`lvnd proposer`** (pipeline). Client API : lit l'interrupteur, la clé et le plafond dans D1, journalise chaque appel,
   s'arrête net au plafond. Prompt bâti depuis ce qui est versionné : consigne aux agents (`docs/QUALIFICATION.md`), règles de
   `docs/METHODO.md`, grille, témoins. Recherche par les outils web du fournisseur. Sortie : un brouillon au format habituel
   (YAML d'une entrée de `temoins.yaml`, plus `relecture`).
3. **Contrôles sans LLM**, avant toute proposition : `editorial.valider`, décomptes `(pour-contre)`, termes interdits
   (secret `TERMES_INTERDITS` du dépôt), chaque extrait retrouvé dans le document, URL qui répond. Porter dans le pipeline ce
   que font `source/outils/controle*.py`. Un échec écarte la proposition et le dit. Les signataires d'un document collectif,
   que le filtre de noms ne voit pas, deviennent un point d'attention systématique.
4. **Mesure, avant de brancher** : sur un échantillon de textes validés (droit principal, sens, décisif, sources admises),
   accord, stabilité entre deux passages, et erreurs sur les textes que la relecture de Max a corrigés (révisions de D1),
   l'accord brut étant flatté parce que Claude les a préparés. Rapport dans `source/`, coût par texte compris. **Max décide**
   ensuite quels types d'alerte reçoivent une proposition complète.
5. **Propositions sur les alertes** : Action `propositions.yml`, après chaque passe de données. Une proposition par nouvelle
   alerte, jamais recalculée : `premier_decisif`, `vote_sans_decisif` et `unanimite_contestee` → brouillon complet ;
   `vote_posterieur` et `lecture_posterieure` → requalification partant de la version publiée ; `inscrit` → fiche de suivi
   (droits touchés et sources, sans sens ni scrutin) ; alertes du Sénat → bloc `senat`. Table D1 `propositions` : alerte,
   document, résultat des contrôles, modèle, coût, statut (proposée, chargée, écartée, contrôle en échec).
6. **« À traiter » repensé** pour la séance hebdomadaire. Une ligne par texte, qui regroupe ses alertes, sa note interne et sa
   proposition : jugement proposé, écart avec la version publiée, sources avec leurs extraits, incertitudes. Deux gestes :
   **charger** (le texte passe « à relire », ou en requalification si publié ; la révision dit « proposition LLM chargée par
   … »), ou **écarter** la proposition (motif court, gardé pour la mesure). La validation et « Publier » ne changent pas.
   Ordre : échéance d'abord (texte inscrit à une date proche), puis date de l'alerte.
7. **Veille des sources**, une fois par semaine : textes suivis, qualifiés, et écartés faute de source (c'est là qu'une
   source nouvelle change la décision). Un nouveau document d'une source admise arrive dans « À traiter » en proposition de
   modification, source et extrait préremplis.
8. **Termes de recherche** proposés avec chaque texte nouvellement qualifié, aujourd'hui ajoutés à la main dans
   `termes_recherche.yaml`, hors de l'admin. À concevoir : champ d'`editorial.json` (sérialisé à l'identique dans le pipeline
   et l'admin) ou fichier à part.
9. **Relire `mots_cles.yaml`**, qui présélectionne les textes suivis : motifs larges (« eau », « soins », « violences »,
   « justice ») dont chaque faux positif coûterait un appel et une relecture.
10. **Documentation** : « Qui qualifie, et comment » sur la page Méthodologie, une fois les propositions en service ;
    `docs/EXPLOITATION.md` (nouvelle Action, plafond, échéance de la clé) ; `docs/QUALIFICATION.md` (circuit avec
    proposition) ; `/aide` de l'admin ; `admin/README.md` (secret `LLM_CHIFFREMENT`).

En fin de cycle, si le reste est en place : **résumés « facile à lire et à comprendre »** des textes qualifiés, générés hors
ligne et relus avant publication (nouveau champ d'`editorial.json`).

**À faire par Max**, au fil du cycle : créer un workspace dédié dans la console Anthropic, avec sa limite de dépense, et une
clé ; poser `LLM_CHIFFREMENT` (Worker et dépôt) et `TERMES_INTERDITS` (dépôt) ; appliquer les migrations
(`npm run db:migrer:distant`) et déployer l'admin (`npm run deploy`).

### Fait dans ce cycle

- Item 1 : page « LLM » de l'admin (migration `0007_llm.sql`) : interrupteur, clé testée puis chiffrée (AES-GCM, vecteur
  partagé avec le pipeline dans `pipeline/tests/fixtures/llm_vecteur.txt`), plafond mensuel (20 $ par défaut), modèle
  (Opus 5.5 par défaut, Sonnet 5.5 au choix), dépense du mois et journal des appels. Coupé par défaut. **À faire par
  Max** : `LLM_CHIFFREMENT` (Worker et dépôt, `admin/README.md`, étape 6), `npm run db:migrer:distant`, `npm run deploy`.
  Fait le 02/11/2026 : clé saisie, interrupteur coupé.
- Items 2 et 3 : `lvnd proposer DOSSIER…` (`lvnd/llm.py`, `proposer.py`, `controles.py`, `propositions.py`). Réglages et
  clé lus dans D1, plafond vérifié avant chaque requête (réserve de 1 $), chaque requête journalisée. Prompt : méthode,
  consigne, grille, témoins (≈ 80 000 caractères, en cache une heure), puis l'alerte, le dossier, ses scrutins et la
  version publiée. Recherche web (12 recherches, 20 lectures au plus), effort `high`. Brouillons dans
  `source/propositions/AAAA-MM-JJ/`, avec origine, coût et contrôles sous `relecture`. Contrôles : termes interdits
  (refus de tout appel sans la liste, lue aussi depuis le secret `TERMES_INTERDITS`), signataires des publications
  collectives, `editorial.valider`, décomptes, URL, **chaque extrait retrouvé dans son document**. `--prompt` écrit le
  prompt sans appel.
- Item 4 : mesure à blanc sur 5 textes (7 passages, 6,78 $), rapport dans `source/mesure-preq/RAPPORT.md`. 3 accords
  sur 5 (droit principal, sens, décisif), les 2 désaccords signalés comme incertains ; jugement stable d'un passage à
  l'autre. Réglages resserrés (effort `medium`, 12 pages de 30 000 jetons, 20 recherches) : environ 0,7 $ par
  proposition. Limite : la recherche de sources s'épuise vite là où elles sont rares. Décisions de Max : propositions
  sur tous les types d'alerte de l'Assemblée, le Sénat après un essai ; mots-clés inchangés pour l'instant (item 9),
  à rejuger sur un mois de dépense réelle.
- Items 5 et 6 : table `propositions` (migration `0008`), `lvnd proposer --alertes`, Action `propositions.yml` (après
  chaque passe de données, 5 propositions au plus), « À traiter » repensé (une carte par texte, proposition, charger ou
  écarter). Un crédit épuisé ou une clé refusée arrêtent la passe.
- Premier passage réel (02/11/2026, 3,89 $) : 4 propositions, toutes conformes aux contrôles ; 3 cas non prévus tranchés
  par Max (règles 7, 22, 25, 28). Décision de Max sur « À traiter » : plus de proposition automatique sur `inscrit`
  (rien à qualifier avant le vote), demande au LLM depuis la carte d'un texte (migration `0009`, traitée à la passe
  suivante, Sénat compris) ; page rangée en quatre sections par une règle fixe (prêt à relire, avec le badge « mise à
  jour mineure » ; question de méthode ; à faire à la main ; à venir) ; une phrase « action proposée » écrite par le
  LLM dans le même appel. Pas d'appel de classement.
- Item 8 : termes de recherche dans `editorial.json` (bloc `recherche`, décision de Max), saisis sur la fiche de l'admin et
  proposés par le LLM ; le YAML ne sert plus que de repli. **Reprise à faire** : déployer l'admin, puis
  `lvnd sync-admin --remote --recherche` et « Publier » (environ 200 textes modifiés d'un coup), puis retirer le YAML.
- Item 7 : veille « à l'envers » (décision de Max) : `lvnd veille`, flux de 36 sources admises
  (`referentiels/sources_veille.yaml`, brouillon **à valider par Max**), lus sans LLM ; un appel de rapprochement
  (0,24 $ à l'essai du 02/11/2026 : 115 publications, 4 correspondances pertinentes) ; une proposition par correspondance,
  3 au plus. Action `veille.yml` le lundi ; elle ne tourne qu'une fois la liste validée.
