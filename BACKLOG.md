# Backlog

File d'attente : les cycles à venir, les idées et les tâches refusées.
**Rien de ce qui est livré** : ce qui est fait sort d'ici (l'historique est
dans `CHANGELOG.md`, le cycle en cours, s'il y en a un, dans `ROADMAP.md`). Une ligne par
item :

```
- [TAG] description courte (origine, date)
```

**Tags** : `[ ]` à trier, `[→Codename]` rangé dans un cycle, `[creuser]`
à réfléchir avant d'arbitrer, `[refusé]` tranché négatif (trace gardée pour
ne pas re-débattre). **Origines** : `user:moi`, `claude`, `gh#N`.

On ajoute en fin de « À trier » en cours de session, et on trie en lot au
début de chaque cycle. Règles de tenue : `CLAUDE.md`, section « Suivi ».

---

## À trier

Rien à trier.

## Cycles candidats

Un cycle à la fois, choisi et nommé au moment de l'ouvrir.

### Passation

Ce qui ne se fait qu'avec celles et ceux qui reprennent le projet : réécriture éditoriale, domaine définitif, comptes d'édition, transfert du
compte Cloudflare et du dépôt.

- [creuser] Le nom « Leurs voix, nos droits » fait écho à « Leurs votes » (Bon Pote) : filiation assumée ou risque de confusion, à trancher à la passation ; recherche INPI faite par Max le 01/11/2026, sans résultat (claude, 2026-10-29)
- [creuser] Règle 7 : admettre les syndicats nationaux membres de Solidaires, qui y tiennent lieu de fédérations (SNJ) ? Retiré de la loi organique sur l'audiovisuel public au lot 6, à trancher à la passation (claude, 2026-10-29)
- [creuser] Règle 7 : un comité national de la CGT (privés d'emploi) vaut-il fédération ? Question ouverte sur Territoires zéro chômeur (DLR5L17N51962, écarté à l'unanimité, 2e lecture inscrite le 19/11/2026), à trancher avec la précédente, à la passation (claude, 2026-10-30)
- [→Passation] Réécrire pour le public les notes de méthode et les motifs d'écart des qualifications, qui citent les règles par leur numéro (181 notes et 512 motifs au 01/11/2026). Le site les replie déjà sous « Comment ce texte a été qualifié », numéros liés à la méthodologie. Bon candidat à un traitement par LLM, relu (user:moi, 2026-10-29)
- [→Passation] Rôles d'édition dans l'admin (rédacteur, valideur) : utile dès qu'il y a plusieurs personnes (un contributeur a accès à l'admin depuis le 29/10/2026) (claude, 2026-10-29)
- [→Passation] Revoir l'exclusion de sources posée le 29/10/2026 (`CLAUDE.md`, règles dures) : la lever ou la garder, et ce que cela change pour les qualifications (claude, 2026-11-01)
- [→Passation] Accord sur l'usage du fournisseur LLM (voir le cycle Pré-qualification), et transfert de la clé API (claude, 2026-11-01)
- [creuser] Quiz « qui vote comme vous ? » sur de vrais scrutins, comme leurs-votes.fr : à discuter à la passation, pour la campagne de 2027 (claude, 2026-10-29)

### Pré-qualification automatique

Son vrai gain vient quand le projet tourne sans Claude Code. Les Actions appellent un LLM par API : les
nouveaux textes et les nouvelles sources arrivent dans « À traiter » avec une
proposition, et la relecture ne part plus d'une feuille blanche. L'admin change
peu : mêmes écrans, même validation, même bouton « Publier ». Garde-fous : le
LLM propose et ne valide ni ne publie jamais ; chaque proposition dit qu'elle
vient de lui ; un cas non prévu remonte à un humain, sans règle inventée.

- [→Pré-qualification] Avant tout : mesurer l'accord avec des qualifications validées (droit principal, sens, décisif), la stabilité entre deux passages et le taux d'erreur sur les textes corrigés à la relecture, l'accord brut étant flatté parce que Claude les a préparées (claude, 2026-10-30)
- [→Pré-qualification] Après chaque passe de données, une proposition pour chaque nouvelle alerte de `en_cours_alertes.csv` : `premier_decisif` et `unanimite_contestee` donnent un brouillon complet ; `vote_posterieur`, une requalification ; `inscrit`, droits touchés et sources, sans sens ni scrutin. Les propositions déjà faites ne sont pas recalculées (user:moi et claude, 2026-10-30)
- [→Pré-qualification] Veille des sources, une fois par semaine, sur les textes suivis et qualifiés : nouveau document d'une source admise ; il arrive en proposition de modification, source et extrait préremplis (user:moi et claude, 2026-10-30)
- [→Pré-qualification] Une proposition sur un texte publié ne change ni son statut ni son contenu (table ou colonne à part, migration D1) : la file « À traiter » la montre, le relecteur l'accepte ou l'écarte. Une proposition sur un texte nouveau peut arriver « à relire » par le circuit de `sync-admin --brouillons` (claude, 2026-10-30)
- [→Pré-qualification] « À traiter » : afficher la proposition, l'écart avec la version publiée, les extraits et les incertitudes. Seul ajout au front (user:moi et claude, 2026-10-30)
- [→Pré-qualification] Contrôles sans LLM avant toute proposition : `editorial.valider`, décomptes, termes interdits, chaque extrait présent dans le document, URL qui répond. Un échec écarte la proposition et le dit (claude, 2026-10-30)
- [→Pré-qualification] Exclusions de sources : prompt sans aucun nom, via la liste privée ; ce filtre ne repère pas un texte cosigné qui ne reprend pas les noms exclus, à contrôler à part (lire les signataires) (claude, 2026-10-30)
- [→Pré-qualification] Clé API : secret GitHub de l'Action, workspace dédié, plafond de dépense ; un dépassement arrête les propositions, sans faire échouer la passe de données ; transfert à prévoir à la passation (claude, 2026-10-30)
- [→Pré-qualification] Mettre à jour « Qui qualifie, et comment » sur la page Méthodologie quand les propositions automatiques tournent, et confirmer auprès des futur·es utilisateur·ices que l'usage de ce fournisseur est accepté (claude, 2026-10-30)
- [→Pré-qualification] Étendre la veille des sources aux textes écartés faute de source : c'est là qu'une source nouvelle change la décision (user:moi et claude, 2026-11-01)
- [→Pré-qualification] Proposer les termes de recherche d'un texte nouvellement qualifié, ajoutés aujourd'hui à la main dans le YAML, hors de l'admin (claude, 2026-11-01)
- [→Pré-qualification] Relire `mots_cles.yaml` (brouillon), qui présélectionne les textes à suivre : motifs larges, sources de faux positifs (« eau », « soins », « violences », « justice »), dont chacun coûterait un appel et une relecture (claude, 2026-10-29)
- [→Pré-qualification] Résumés « facile à lire et à comprendre » des textes qualifiés, générés hors ligne par LLM et relus avant publication : nouveau champ d'`editorial.json`, à sérialiser à l'identique dans le pipeline et l'admin (claude, 2026-10-30)

## À creuser

- [creuser] `/textes` : combiner un mot et les filtres (« pass sanitaire » en XVe). La case de l'en-tête suffit pour l'instant ; si le besoin apparaît, réutiliser le même moteur et les mêmes termes plutôt qu'une seconde recherche sur le titre (user:moi et claude, 2026-11-01)
- [creuser] Eurodéputés (HowTheyVote.eu) : hors périmètre national, à garder en tête (claude, 2026-10-29)
- [creuser] Après la session close le 28/02/2027 : en cas de dissolution, une XVIIIe à ouvrir (`LEGISLATURES`, textes pendants à l'AN, à vérifier), et un bilan de la XVIIe pour la campagne (claude, 2026-10-30)
- [creuser] Routeur public de questions, seulement si un besoin en direct apparaît : renvoi vers des fiches ou des filtres d'une liste fermée, aucune phrase rédigée sur un élu (claude, 2026-10-30)

## Refusé

- [refusé] Correspondance entre les groupes des deux chambres : jugement au cas par cas, contraire à la règle fixe et à la règle 28 (décision de Max, 2026-11-01)
- [refusé] Interroger le catalogue de l'admin en langage naturel : peu d'utilisateurs, des filtres déjà là, et la même raison que l'assistant dans l'admin (user:moi et claude, 2026-11-01)
- [refusé] Sénat : compter au Sénat un texte écarté à l'AN pour unanimité et disputé au Sénat (nationalisation d'EDF, douane, commission d'évaluation de l'aide, textile, chlordécone, devoir conjugal, accès à l'accompagnement, Territoires zéro chômeur) : un texte écarté l'est pour les deux chambres, règle 28 (décision de Max, 2026-10-31)
- [refusé] Listes et « Prochains votes » : afficher la date de l'état. Le pied de page donne déjà la date des données sur chaque page (claude, 2026-10-31)
- [refusé] « Non conforme » affiché pour une non-conformité partielle (2026-911 DC) : libellé de l'open data, absent du site, où la fiche dit « non-conformité partielle » (claude, 2026-10-31)
- [refusé] Saisines irrecevables absentes du catalogue (2024-870 DC et 2024-871 DC) : manque de l'open data, qu'une qualification peut dire à la main (claude, 2026-10-31)
- [refusé] Assistant dans l'admin (bouton « Préparer un brouillon », chat d'édition, import d'une source depuis une URL ou un PDF, relecture à l'écran) : trop de changements dans l'expérience de l'admin, les appels LLM passent par les Actions (user:moi, 2026-10-30)
- [refusé] Chat libre sur le site public : erreur grave sur un député nommé, réponse invérifiable alors que chaque chiffre mène au scrutin officiel, questions révélant des opinions politiques envoyées à un tiers, coût sans plafond naturel, backend à ajouter à un site statique (user:moi et claude, 2026-10-30)
- [refusé] Cas « instrumentalise le sujet » (vote favorable mais texte de façade) : jugement au cas par cas, contraire à la règle fixe de la méthode (claude, 2026-10-29)
- [refusé] Suivre les textes dès leur dépôt : 2 462 dossiers de loi non promulgués en XVIIe au 29/10/2026, presque tous jamais examinés (claude, 2026-10-30)
- [refusé] Sens provisoire, score provisoire ou prévision de vote avant le vote : le texte change en navette (règle 6) (claude, 2026-10-30)
- [refusé] Compteur de marge d'un vote : 1 décisif qualifié sur 94 se joue à 10 voix ou moins (claude, 2026-10-30)
- [refusé] Newsletter, pétition ou formulaire d'envoi hébergé : stockage de données personnelles, contraire au ton factuel ; à revoir à la passation (claude, 2026-10-30)
- [refusé] Recherche par code postal, communes coupées : l'option A (tous les députés possibles, avec leurs communes) reste. Choisir son adresse (C) demanderait un service tiers à l'exécution ou une table de 490 Mo (claude, 2026-10-29)
- [refusé] `data/lvnd.sqlite` en identifiants entiers : 193 Mo, local et non versionné, la taille ne gêne pas (claude, 2026-10-29)
- [refusé] `lvnd annuaire` : repli sur la table MI 2017 pour les 8 couples code postal × commune sans circonscription. Sans objet : six villages détruits de Verdun (sans habitant, leur code postal est résolu par les autres communes), Monaco et Clipperton (claude, 2026-10-29)
