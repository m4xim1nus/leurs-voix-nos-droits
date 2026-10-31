# Backlog

File d'attente : les cycles à venir, les idées et les tâches refusées.
**Rien de ce qui est livré** : ce qui est fait sort d'ici (l'historique est
dans `CHANGELOG.md`, le cycle en cours dans `ROADMAP.md`). Une ligne par
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

- [ ] Alertes : aucune ne signale un texte rejeté par le rejet d'une partie (PLFSS 2027, V9097) ni un vote sur l'ensemble sans scrutin public ; `etat` les suit, pas `lvnd check` (claude, 2026-10-30)
- [ ] `lvnd check` : le délai de 14 jours (`DELAI_AMENDEMENTS`) retire à tort du taux de la XVIe ses derniers scrutins (3 041/3 053 affichés, au lieu de 3 159/3 173), alors que cette législature est figée (claude, 2026-10-30)
- [ ] `lvnd download` : `--leger` retente le dump de l'AN pour les amendements de la XVIe quand ils viennent du plan B (mode `secours`, pas de zip local), jusqu'à 20 minutes de blocage ; un `.part` repris alors que l'AN a publié un nouveau fichier échoue (« taille X, attendu Y ») et reste à supprimer à la main (claude, 2026-10-30)
- [ ] `lvnd download --leger` en local, quand les amendements de la XVIe ne viennent que du plan B (`unitaire`, sans zip) : il retente le dump de l'AN au lieu de réutiliser ce qui est là, et reste bloqué. Sans effet en CI, qui a la copie de la release (claude, 2026-10-31)
- [ ] Sénat : `lvnd build` en local réécrit les exports de l'AN quand `data/raw/` diffère de la copie de la CI. Pour ne changer que le Sénat, restaurer ces fichiers avant de commiter (claude, 2026-10-31)
- [ ] Admin, version `autre` du Sénat : droits, vigilance et sources se saisissent en JSON sur la fiche, pas avec les formulaires habituels (claude, 2026-10-31)
- [ ] Fiche député·e : « Prochains votes » ne liste pas les textes du seul Sénat attendus à l'AN (casseurs-payeurs), pour ne rien changer aux vues de l'AN pendant le cycle Sénat (claude, 2026-10-31)
- [ ] Vérifier le 01/11/2026 que la passe quotidienne (`donnees-quotidien.yml`, 5 h UTC) tourne bien : première avec le Sénat publié. Garde-fou du Sénat, sync de l'admin, alertes du Sénat ramenées à une dans « À traiter » (ingérences étrangères). Correction après le cycle si besoin (user:moi, 2026-10-31)
- [ ] Cycle Sénat, hors cycle : amendements clés du Sénat (environ 31 suppressions hors budgets et retraites, sur 16 textes), cartes partageables des sénateur·ices, Comparer pour le Sénat, correspondance entre groupes des deux chambres (claude, 2026-10-31)

## Textes à surveiller

Ce que les alertes de `lvnd check` et d'« À traiter » ne signalent pas. Le reste se traite à l'alerte, un texte à la fois (« Au fil de l'eau » de `docs/QUALIFICATION.md`).

- [ ] PLFSS 2027 (DLR5L17N54951) : rejeté à l'AN par le rejet d'une partie, aucune alerte tant que celle du point « À trier » n'existe pas (claude, 2026-10-30)
- [ ] Territoires zéro chômeur (DLR5L17N51962, écarté à 96-0) : commission le 10/11, 2e lecture inscrite le 19/11/2026 ; alerte seulement si le vote n'est plus unanime. Règle 7 : un comité national de la CGT (privés d'emploi) vaut-il fédération ? Aucune source récente lue, à trancher si une position paraît (claude, 2026-10-30)
- [ ] Réforme de l'audiovisuel public (DLR5L16N47697) : à l'arrêt depuis juillet 2025, à suivre avant tout vote final, fiche de suivi possible (user:moi, 2026-10-29)
- [ ] Fiche de suivi prête dans `source/brouillons-suivi-attente/`, à charger dès l'inscription : ingérences étrangères (DLR5L17N54703). Casseurs-payeurs (DLR5L17N54925) est qualifié au cycle Sénat, sans fiche (décision de Max, 31/10/2026) (claude, 2026-10-30)
- [ ] AGRASC (DLR5L17N53159, écarté au lot 6) : CMP convoquée le 29/10/2026 ; si l'AN vote ses conclusions, ce vote devient le décisif, revoir l'écart. Au prochain passage, actualiser le motif, qui ne cite pas les articles 5 et 5 bis A (décision de Max, 30/10/2026) (claude, 2026-10-29)

## Cycles candidats

Un cycle à la fois, choisi et nommé au moment de l'ouvrir.

### XVe

2017-2022 : sécurité globale, séparatisme, état d'urgence sanitaire.

- [→XVe] Ouvrir le cycle par les textes `libertes` (séparatisme, sécurité globale, anti-casseurs) (user:moi, 2026-10-29)

### Passation

Réécriture éditoriale, domaine définitif, comptes d'édition, transfert du
compte Cloudflare et du dépôt.

- [creuser] Le nom « Leurs voix, nos droits » fait écho à « Leurs votes » (Bon Pote) : filiation assumée ou risque de confusion, à trancher avant la passation ; recherche INPI non faite (claude, 2026-10-29)
- [creuser] Règle 7 : admettre les syndicats nationaux membres de Solidaires, qui y tiennent lieu de fédérations (SNJ) ? Retiré de la loi organique sur l'audiovisuel public au lot 6, à trancher à la passation (claude, 2026-10-29)
- [→Passation] Une fois tout qualifié : réécrire pour le public les notes de méthode et les motifs d'écart des qualifications, qui citent les règles par leur numéro (≈ 60 notes, ≈ 50 motifs). Le site les replie déjà sous « Comment ce texte a été qualifié », numéros liés à la méthodologie (user:moi, 2026-10-29)
- [→Passation] Revoir les qualifications politiquement sensibles, tranchées par une règle fixe ou par défaut :
  - choix du droit principal qui inverse les groupes favorables et défavorables : antisemitisme-enseignement-superieur (discriminations étend contre libertes restreint), abrogation-obligation-vaccinale-2023 (travail-protection-sociale étend, retenu, contre sante restreint) ;
  - energies-renouvelables-2023 et nucleaire-acceleration-2023, toutes deux `environnement` restreint par la règle 2 (choix d'énergie hors grille) : sur les renouvelables, RN, LR, LFI et GDR, qui ont voté contre, sont comptés favorables ;
  - exécution provisoire de l'inéligibilité (RN, UDR et DR comptés favorables), peine d'inéligibilité (DLR5L16N47056), corps électoral de Nouvelle-Calédonie (2024 et 2026), droit de visite des parlementaires dans les établissements sociaux et médico-sociaux (RN compté favorable) ;
  - purge des nullités (`restreint` par la règle 4 : seul LFI compté favorable), mortalité infantile (`sante` restreint sur les sociétés savantes : seuls 4 EPR comptés favorables)
  (user:moi et claude, 2026-10-29)
- [→Passation] Rôles d'édition dans l'admin (rédacteur, valideur) : utile dès qu'il y a plusieurs personnes (un contributeur a accès à l'admin depuis le 29/10/2026) (claude, 2026-10-29)
- [→Passation] Tutoriel de l'admin pour les futur·es rédacteur·ices (connexion par Access, qualifier un texte, contrôles, brouillon et publication) (user:moi, 2026-10-29)
- [→Passation] Présentation du projet et des choix de méthode retenus : page « bento » ou PDF (user:moi, 2026-10-29)

### Pré-qualification automatique

Non prioritaire, cycle à part. Les Actions appellent un LLM par API : les
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
- [→Pré-qualification] Audit de cohérence : repérer les cas similaires tranchés différemment, avant la revue des qualifications sensibles (claude, 2026-10-30)
- [→Pré-qualification] Mettre à jour « Qui qualifie, et comment » sur la page Méthodologie quand les propositions automatiques tournent, et confirmer auprès des futur·es utilisateur·ices que l'usage de ce fournisseur est accepté (claude, 2026-10-30)

## À creuser

- [creuser] Rattachement scrutin → dossier : V4239 (amendement au PLF 2026) est rattaché à la simplification de l'urbanisme (DLR5L17N51852), V6758 (loi d'urgence agricole) à la loi organique « natifs » de Nouvelle-Calédonie (DLR5L17N52104). Non retenus, sans effet sur les scores ; d'autres scrutins sont-ils touchés ? (claude, 2026-10-29)
- [creuser] Table pays → circonscription des Français de l'étranger (code électoral, art. L. 330-1) à saisir en référentiel (claude, 2026-10-29)
- [creuser] Relire `mots_cles.yaml` (brouillon), qui présélectionne les textes à suivre : motifs larges, sources de faux positifs (« eau », « soins », « violences », « justice ») (claude, 2026-10-29)
- [creuser] Quiz « qui vote comme vous ? » sur de vrais scrutins, comme leurs-votes.fr (claude, 2026-10-29)
- [creuser] Eurodéputés (HowTheyVote.eu) : hors périmètre national, à garder en tête (claude, 2026-10-29)
- [creuser] Après la session close le 28/02/2027 : en cas de dissolution, une XVIIIe à ouvrir (`LEGISLATURES`, textes pendants à l'AN, à vérifier), et un bilan de la XVIIe pour la campagne (claude, 2026-10-30)
- [creuser] Résumés « facile à lire et à comprendre » des textes qualifiés, générés hors ligne par LLM et relus avant publication : nouveau champ d'`editorial.json`, à sérialiser à l'identique dans le pipeline et l'admin (claude, 2026-10-30)
- [creuser] Recherche enrichie : des termes courants par texte (« APL », « reconnaissance faciale »), générés hors ligne et relus, pour un index statique, sans serveur ni coût à l'usage (claude, 2026-10-30)
- [creuser] `llms.txt` et documentation des données : pour interroger le site avec son propre outil, à ses frais (claude, 2026-10-30)
- [creuser] Routeur public de questions, seulement si un besoin en direct apparaît : renvoi vers des fiches ou des filtres d'une liste fermée, aucune phrase rédigée sur un élu (claude, 2026-10-30)
- [creuser] Interroger le catalogue de l'admin en langage naturel : peu d'utilisateurs et des filtres déjà là, intérêt à démontrer (user:moi, 2026-10-30)

## Refusé

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
