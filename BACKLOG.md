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

- [ ] **À voir début décembre 2026.** Rejuger `mots_cles.yaml` sur un mois de dépense réelle des propositions : motifs qui n'ont presque jamais donné de texte qualifié (`egalite` 0/7, `eau` 0/6, `polynesie` 0/5, `retraites?` 1/13, `outre mer` 2/16…), chacun coûtant une proposition (claude, 2026-11-02)
- [ ] Script versionné des captures du guide `/aide` (Playwright, pastilles numérotées) : celle d'« À traiter » a été refaite à la main deux fois le 02/11/2026 (claude, 2026-11-02)
- [creuser] Résumé en mots simples des fiches de suivi et du vote du Sénat, hors périmètre du cycle Facile à lire (décision de Max du 02/11/2026) (claude, 2026-11-02)

## Cycles candidats

Un cycle à la fois, choisi et nommé au moment de l'ouvrir.

### Passation

Ce qui ne se fait qu'avec celles et ceux qui reprennent le projet : réécriture éditoriale, domaine définitif, comptes d'édition, transfert du
compte Cloudflare et du dépôt.

- [creuser] Le nom « Leurs voix, nos droits » fait écho à « Leurs votes » (Bon Pote) : filiation assumée ou risque de confusion, à trancher à la passation ; recherche INPI faite par Max le 01/11/2026, sans résultat (claude, 2026-10-29)
- [creuser] Règle 7 : admettre les syndicats nationaux membres de Solidaires, qui y tiennent lieu de fédérations (SNJ) ? Retiré de la loi organique sur l'audiovisuel public au lot 6, à trancher à la passation (claude, 2026-10-29)
- [creuser] Règle 7 : un comité national de la CGT (privés d'emploi) vaut-il fédération ? Question ouverte sur Territoires zéro chômeur (DLR5L17N51962, écarté à l'unanimité, 2e lecture inscrite le 19/11/2026), à trancher avec la précédente, à la passation (claude, 2026-10-30)
- [→Passation] Réécrire pour le public les notes de méthode et les motifs d'écart des qualifications, qui citent les règles par leur numéro (181 notes et 512 motifs au 01/11/2026). Le site les replie déjà sous « Comment ce texte a été qualifié », numéros liés à la méthodologie. Bon candidat à un traitement par LLM, relu (user:moi, 2026-10-29)
- [→Passation] Faire relire les résumés « En mots simples » par des personnes concernées, condition du label FALC (cycle Facile à lire, `CHANGELOG.md` 1.11.0) (claude, 2026-11-02)
- [→Passation] Rôles d'édition dans l'admin (rédacteur, valideur) : utile dès qu'il y a plusieurs personnes (un contributeur a accès à l'admin depuis le 29/10/2026) (claude, 2026-10-29)
- [→Passation] Revoir l'exclusion de sources posée le 29/10/2026 (`CLAUDE.md`, règles dures) : la lever ou la garder, et ce que cela change pour les qualifications (claude, 2026-11-01)
- [→Passation] Accord sur l'usage du fournisseur LLM (cycle Pré-qualification, `CHANGELOG.md` 1.10.0), et transfert de la clé API : nouvelle clé saisie sur la page « LLM » de l'admin, nouveau secret `LLM_CHIFFREMENT` (claude, 2026-11-01)
- [creuser] Quiz « qui vote comme vous ? » sur de vrais scrutins, comme leurs-votes.fr : à discuter à la passation, pour la campagne de 2027 (claude, 2026-10-29)

## À creuser

- [creuser] `/textes` : combiner un mot et les filtres (« pass sanitaire » en XVe). La case de l'en-tête suffit pour l'instant ; si le besoin apparaît, réutiliser le même moteur et les mêmes termes plutôt qu'une seconde recherche sur le titre (user:moi et claude, 2026-11-01)
- [creuser] Eurodéputés (HowTheyVote.eu) : hors périmètre national, à garder en tête (claude, 2026-10-29)
- [creuser] Après la session close le 28/02/2027 : en cas de dissolution, une XVIIIe à ouvrir (`LEGISLATURES`, textes pendants à l'AN, à vérifier), et un bilan de la XVIIe pour la campagne (claude, 2026-10-30)
- [creuser] Routeur public de questions, seulement si un besoin en direct apparaît : renvoi vers des fiches ou des filtres d'une liste fermée, aucune phrase rédigée sur un élu (claude, 2026-10-30)

## Refusé

- [refusé] Propositions automatiques sur les alertes du Sénat : elles restent sur demande, depuis la carte d'un texte dans « À traiter » (décision de Max, 2026-11-02)
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
