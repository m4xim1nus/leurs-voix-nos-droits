# Réflexion : supprimer le droit principal ?

*Note rédigée par Claude pour Max, le 19/11/2026. Elle ne change aucune
règle, aucun code, aucune donnée, et ne contient ni calcul ni simulation
(choix de Max). C'est un choix sensible (grille et règles de calcul) : Max
seul tranche.*

La question de Max : que devient le projet si l'on supprime le principe du
**droit principal** ? Il faudrait renoncer à une note globale unique, mais
on gagnerait en objectivité, on noterait mieux chaque droit, et l'on
pourrait montrer, pour chaque groupe, la **priorisation entre les droits**.

## 1. Ce que fait aujourd'hui le droit principal

### Dans les règles (`docs/METHODO.md`)

- **Règle 3** : les recouvrements fixent le droit principal d'office (justice
  des mineurs : `enfants` ; technique de surveillance : `vie-privee` ; mesure
  qui ne vise que des étrangers : `etrangers`).
- **Règle 4** : « il n'y a pas de sens mixte global : le sens affiché pour
  le texte est celui de son droit principal ». Le droit principal est celui
  de la mesure que les sources admises citent le plus souvent (chaque
  organisation compte une fois) ; à égalité, celui de l'objet du texte. Le
  sens d'un droit dans un texte composite suit le même décompte.
- **Règle 4 encore** : une mesure qui touche un autre droit le reçoit en
  secondaire ; la vigilance est réservée aux mesures de sens opposé pour
  *un même* droit et à la mise en œuvre.
- **Règle 7** : un texte qui étend son droit principal doit citer une source
  critique en vigilance (contrôle de `lvnd check`, en avertissement).
- **Règle 11** : n'est pas retenu un article retenu pour une critique qui
  ne vise qu'un droit secondaire de sens opposé au droit principal, car le
  vote compterait au score global à rebours de cette critique.
- **Règle 15** : le score **global** prend le sens du droit principal de
  chaque texte. Le score **d'un droit** compte les textes où il est
  principal *et* ceux où il est secondaire, chacun avec son propre sens.
- **Règles 23 à 28** (Sénat) : mêmes règles ; la version votée au Sénat peut
  avoir un autre droit principal que celle de l'Assemblée (règle 24).

### Dans le pipeline

- `pipeline/lvnd/scores.py` : pour chaque scrutin compté, une ligne par
  droit du texte (avec son sens) **plus** une ligne `global` au sens du
  principal. Un réglage `droits` (`principal` ou `tous`) existe déjà : la
  règle 15 a donc déjà tranché, pour le score d'un droit, en faveur de
  `tous`. Seule la ligne `global` dépend du principal.
- `pipeline/lvnd/check.py` et `editorial.py` : erreur bloquante si un texte
  n'a pas « exactement un droit principal » (aussi côté Sénat) ; avertissement
  « étend son droit principal → source critique en vigilance ».
- `resumer.py` : le prompt du résumé en mots simples met le principal d'abord.
- `data/editorial.json` et `temoins.yaml` : champ `role` de chaque droit.

### Dans l'admin

- `EditeurDroits.svelte` : menu « droit principal / secondaire », un seul
  principal. `qualification.ts` (mêmes contrôles que le pipeline, vérifiés
  par un test croisé), `etapes.ts` (étape « Choisir le droit principal »,
  bloquante pour valider), `scores.ts` (aperçu des scores), `propositions.ts`
  (propositions du LLM), `a-traiter` (une « mise à jour mineure » ne change
  ni statut, ni droit principal, ni sens, ni décisif), page d'aide.

### Sur le site public

- **Accueil** : « part des votes favorables aux droits, au sens du droit
  principal de chaque texte » ; moteur de recherche (`recherche.ts`).
- **Cartes de texte** (`TexteCarte.svelte`, liste `/textes`) : la bande
  « ▲ Étend / ▼ Restreint + droit » est le principal. Sous un filtre de droit,
  `sousAngle` montre le sens de ce droit et inverse le score du texte s'il
  est contraire à celui du principal (`100 − score`).
- **Fiche texte** : le verdict en tête met le principal d'abord et en plus
  grand ; seul le principal écrit son sens en toutes lettres ; la mention
  « droit principal » ; la phrase « Le texte restreint X » (aussi dans
  `og:description`) ; l'intitulé des tableaux de votes de groupe.
- **Fiches groupe, député·e, droit, comparateur, tuiles de partage,
  Sénat** : « score global » partout, plus le score par droit.
- **Page Méthodologie** : recouvrements, sens d'un texte, règles 11 et 15.

## 2. Ce qu'on perd

1. **Le score global unique.** C'est le chiffre qui s'affiche en premier sur
   la fiche d'un·e député·e, d'un groupe, dans le comparateur et sur les
   tuiles de partage. Il se lit d'un coup d'œil et se classe.
2. **Le sens unique d'un texte.** La bande de la carte (« ▼ Restreint la vie
   privée ») disparaît telle quelle. Un texte comme la loi immigration de 2024
   (`etrangers` restreint, `enfants` étend) n'a plus de verdict en un mot.
3. **La phrase « ce texte restreint X »**, utile pour les titres, les
   résumés, l'aperçu des liens et la recherche.
4. **Un tri simple** des textes par sens, et une porte d'entrée pour le
   non-spécialiste.

### Options pour garder une forme de synthèse

| Option | Principe | Problèmes |
|---|---|---|
| **A. Aucun score de synthèse** | Seuls les scores par droit existent. | Perd le chiffre d'accroche et le classement. Le public veut souvent une note. Mais c'est le plus cohérent avec « une règle fixe plutôt qu'un jugement ». |
| **B. Moyenne simple des scores par droit** | Chaque droit pèse 1. | Introduit une **pondération entre droits** (tous égaux ? c'est un choix de valeur). Un droit touché par deux textes pèse autant qu'un droit touché par vingt. Il faut une règle pour un droit sans texte ou presque. |
| **C. Un point par couple (texte, droit)** | Chaque couple compte 1. | **Double comptage** : un texte à cinq droits pèse cinq fois plus. Le droit le plus souvent touché domine. |
| **D. Idem, mais le texte pèse 1 réparti entre ses droits** | Poids 1 divisé par le nombre de droits. | Le partage à parts égales est une pondération inventée : un droit ajouté en secondaire allège les autres. |
| **E. Profil par droit, sans note unique** | Une valeur par droit, avec le nombre de textes comptés. | Moins accrocheur ; demande un bon design (§ 3). Pas de classement unique des groupes. |
| **F. Synthèse en mots** | « Favorable sur 8 droits, défavorable sur 3 ». | Compte des droits sans dire leur poids ; lecture trompeuse possible. |

Deux problèmes communs aux options chiffrées : la **pondération entre
droits** (un droit en vaut-il un autre ?) et le **double comptage** des
textes à plusieurs droits (un vote sur une loi immigration compterait pour
`etrangers` et pour `enfants`). Ils existent déjà dans le score *par droit*
(règle 15 : principal et secondaire), mais n'y gênent pas, car chaque score
reste interne à un droit. Ils deviennent gênants dès qu'on additionne des
droits.

## 3. Ce qu'on gagne

### Objectivité

- **Le choix du principal est un jugement**, même encadré par le décompte des
  sources. Cas limites : égalité de décompte (on retombe sur « l'objet du
  texte », qui est un jugement) ; texte composite dont aucune mesure ne
  domine ; sources qui ne couvrent qu'un droit (le principal reflète alors
  ce que les ONG ont commenté, pas ce que le texte fait surtout) ; principal
  qui change quand une nouvelle source arrive ; version du Sénat dont le
  principal diffère de celui de l'Assemblée (règle 24).
- Les recouvrements de la règle 3 sont des **règles fixes**, mais ce sont des
  conventions : « justice des mineurs → `enfants` principal » est un
  arbitrage de valeur.
- Le score global **hérite** de ce jugement : un même vote compte à l'endroit
  ou à l'envers selon le principal retenu (voir `sousAngle` et `100 − score`).
- Supprimer le principal retire un jugement par texte, l'avertissement de la
  règle 7 et l'exception de la règle 11 pour les droits secondaires de sens
  opposé.

### Notation par droit plus franche

Un droit secondaire compte déjà dans son score (règle 15), mais l'interface
lui donne un statut de seconde zone. Sans principal, un texte qui touche
`enfants` et `etrangers` compte à égalité pour chacun, avec son sens propre.
Le score d'un droit ne dit plus « texte surtout sur autre chose, droit
annexe ».

### Priorisation entre les droits, par groupe

Le **profil** de chaque groupe devient l'objet central : sur quels droits il
est favorable, sur lesquels il est défavorable. Cela répond mieux à la
question du public (« ce groupe défend-il les libertés mais pas les droits
des étrangers ? ») qu'une moyenne, qui masque ces écarts.

Affichages possibles, sans copier leurs-votes.fr :

- **Barres horizontales**, une par droit, triées du plus défendu au moins
  défendu, avec le nombre de textes comptés en légende et un repère à 50 %.
  Lisible sur téléphone.
- **Grille groupes × droits** (carte de chaleur) sur la page des groupes : la
  priorisation se lit en ligne, la comparaison entre groupes en colonne.
- **Haltères** pour comparer deux groupes, ou un·e député·e à son groupe,
  droit par droit : prolonge le comparateur actuel.
- **Radar** : à éviter (douze axes, surfaces trompeuses).
- Un droit sous un seuil de textes comptés est grisé.

Précautions : le nombre de textes comptés reste à côté de chaque valeur (un
droit à 2 textes n'est pas un droit à 20). Et « priorisation » est une
lecture : la donnée montre ce qu'un groupe **vote**, pas ce qu'il estime
prioritaire. Le libellé doit le dire.

## 4. Effets de bord

- **Règle 4, vigilance.** La règle (vigilance réservée aux sens opposés d'un
  même droit) ne parle pas du principal et tient telle quelle. Mais
  « secondaire » perd son sens : tous les droits sont équivalents, et il faut
  dire comment on décide qu'un droit est **touché**. Aujourd'hui le principal
  absorbe une partie des cas limites ; sans lui, le seuil de « droit touché »
  devient la zone de jugement.
- **Sens d'un scrutin.** Inchangé : le sens du scrutin (`pour: texte` ou
  `contre-texte`) ne dépend pas du droit. En revanche la règle 11 (article
  retenu pour un droit secondaire de sens opposé) doit se reformuler droit
  par droit : un amendement clé peut valoir pour un droit sans valoir pour un
  autre, ce qui peut demander de saisir, par droit, quels amendements comptent.
- **Pondération (règle 18).** « Chaque texte pèse 1 » reste vrai pour chaque
  droit pris à part. Il ne l'est plus pour une synthèse (§ 2).
- **Textes témoins** (`temoins.yaml`, `pipeline/tests/`). Les six textes
  portent un principal. `test_scores.py`, `test_editorial.py`, `test_llm.py`
  et `test_resumer.py` l'utilisent, ainsi que les fixtures `editorial_*.json`.
  Il faudrait rebaser les attendus ; « exactement un principal » deviendrait
  « au moins un droit ».
- **Admin.** Retirer le menu de rôle, l'étape « Choisir le droit principal »,
  les contrôles, la consigne du LLM (« un seul principal, celui de la mesure
  la plus citée ») et la page d'aide. Pas de migration D1 indispensable : le
  champ peut rester en base, ignoré, le temps de la transition.
- **Qualifications existantes.** À reprendre telles quelles : chaque droit
  garde son sens et ses sources ; seul `role` devient sans effet. Rien à
  requalifier si l'on garde le format. Le champ pourra être retiré plus tard,
  dans un diff mécanique d'`editorial.json`.
- **Site.** Cartes de texte : la bande devient une rangée de pastilles (une
  par droit, ▲ ou ▼), ou montre le sens du droit filtré. Fiche texte : tous
  les droits au même niveau ; la phrase d'aperçu à réécrire. Accueil, fiches
  groupe et député·e, comparateur, tuiles de partage : à concevoir sans
  chiffre unique, c'est le plus gros chantier. Recherche : l'extrait
  « droit : sens » devient une liste.
- **Page Méthodologie.** À réécrire (recouvrements, sens d'un texte, règles
  11 et 15). Elle perd une notion difficile à expliquer (« droit principal »)
  et gagne une notion nouvelle (profil).
- **Sénat.** Même traitement ; la règle 24 sur le principal de la version du
  Sénat disparaît, ce qui simplifie.
- **leurs-votes.fr.** Le modèle donne une note par parlementaire. Un profil
  par droit accentue nos différences (texte plutôt qu'amendement, règles
  publiques, sources, code postal), mais on perd la note d'accroche. Le
  contrôle croisé (`docs/SOURCES.md`) porte sur les ventilations de votes, pas
  sur les scores : il n'est pas touché.

## 5. Questions à trancher

1. **Garde-t-on un score de synthèse ?**
   *Recommandation : non dans un premier temps (options A et E), avec le
   profil par droit en vedette.* Toute synthèse chiffrée réintroduit une
   pondération entre droits, c'est-à-dire un choix de valeur, ce que la
   préférence pour les règles fixes cherche à éviter. On pourra en ajouter une
   plus tard si les retours le demandent.
2. **Si oui, laquelle ?**
   *Recommandation : la moyenne simple des scores par droit (option B), avec
   un seuil minimal de textes par droit.* Elle est fixe, publique, sans
   double comptage. Écarter C et D (double comptage ou partage inventé).
3. **Que montre la carte d'un texte ?**
   *Recommandation : une rangée de pastilles par droit, sans hiérarchie,
   avec le titre officiel et le résumé en mots simples comme ancre.* Sous un
   filtre de droit, la bande reste le sens de ce droit (c'est déjà le cas).
4. **Comment décide-t-on qu'un droit est « touché » sans principal ?**
   *Recommandation : qu'au moins une source admise se prononce sur la mesure,
   comme aujourd'hui pour le secondaire (règle 4), et rien de plus.* Le
   jugement passe de « quel droit domine » à « ce droit est-il touché »,
   plus facile à sourcer et à vérifier.
5. **Que devient la règle 11 pour un droit de sens opposé ?**
   *Recommandation : la garder, reformulée « droit de sens opposé à celui du
   droit dont on calcule le score », et la traiter dans la PR de mise en
   œuvre.* Elle protège les scores par droit contre un vote compté à rebours.
6. **Comment affiche-t-on la priorisation d'un groupe ?**
   *Recommandation : barres triées par droit avec le nombre de textes
   comptés, grille groupes × droits sur la page des groupes, et un libellé
   « ce que le groupe vote », pas « ce qu'il juge prioritaire ».*
7. **Garde-t-on le champ `role` dans les qualifications ?**
   *Recommandation : oui, inerte, pendant une version, puis retrait.* Le
   coût de bascule est minimal et le retour en arrière reste possible.
8. **Faut-il un essai à blanc avant de trancher ?**
   *Recommandation : seulement après la question 1, dans une PR séparée.* Le
   calcul par droit existe déjà ; il reste à produire les affichages sans
   chiffre unique. Max a choisi de ne pas simuler dans cette note.
9. **Calendrier.**
   *Recommandation : ne pas toucher aux règles en plein cycle ; ouvrir un
   cycle « Profil par droit » avec cette note comme point de départ.* Max
   ouvre et ferme les cycles.
