# Méthodologie

Base de la page Méthodologie du site. Chaque règle de ce document est
**validée par Max** avant d'entrer en vigueur. Les règles 1 à 13 l'ont été
le 29/10/2026, à la fin du spike de l'étape 1. Les règles de calcul (14 à
19) l'ont été le même jour, à l'étape 2, sur simulation des six textes
témoins (`pipeline/referentiels/temoins.yaml`).
Le choix de la lecture et la notion de source qui « cite » une mesure (règle
11) l'ont été le même jour, sur le cas de Kasbarian-Bergé, puis les
exclusions de la règle 11 et les motions « inversées » (règle 10), à la
relecture des vingt et un premiers textes.

## Grille des droits

Grille v0 : `pipeline/referentiels/droits.yaml`. Onze droits et deux
étiquettes transversales (`outre-mer`, `regime-exception`).

1. **Point de vue.** Le sens se lit toujours du point de vue des droits des
   personnes concernées, jamais des prérogatives de l'État. Un texte qui
   donne de nouveaux moyens à la police « restreint » les garanties des
   personnes face à elle.
2. **Périmètre.** La grille suit les droits des personnes face à la
   puissance publique et aux plus forts. La propriété et l'ordre public
   sont des objectifs que le législateur concilie avec ces droits : ils
   n'entrent pas dans la grille. Quand un texte les étend (Kasbarian-Bergé,
   pour la propriété), on le signale en point de vigilance.
3. **Recouvrements**, tranchés par une règle fixe :
   - justice des mineurs → `enfants` principal, `police-justice`
     secondaire ;
   - technique de surveillance → `vie-privee` principal, `libertes`
     seulement si une source le relève ;
   - mesure qui ne vise que des étrangers → `etrangers` principal.
4. **Sens droit par droit.** Chaque droit touché reçoit son sens (`etend`
   ou `restreint`). Il n'y a pas de sens « mixte » global : le sens
   affiché pour le texte est celui de son droit principal. Exemple,
   l'immigration : `etrangers` restreint, `enfants` étend.
5. **Points de vigilance.** Les critiques sourcées portant sur la mise en
   œuvre ou sur l'insuffisance des garanties s'affichent à côté du
   jugement, sans le modifier (aide à mourir).
6. **Objet qualifié.** On qualifie le texte soumis au scrutin décisif,
   puisque c'est le vote du député qui est mesuré. La décision du Conseil
   constitutionnel s'affiche à côté (« 32 articles censurés »).
7. **Sources.** Chaque qualification cite au moins une source publique :
   - CNCDH, Défenseur des droits, Conseil constitutionnel ;
   - CNIL, CGLPL ;
   - rapporteurs et comités de l'ONU ;
   - ONG ;
   - pour la santé, ordres professionnels et sociétés savantes.

   Quand un texte étend un droit contesté, au moins une source critique
   figure en vigilance.
8. **Textes purement organisationnels** (par exemple la loi organique
   jumelle du narcotrafic) : non qualifiés.

## Scrutins retenus

9. **Scrutin décisif** : le dernier vote de l'AN sur l'ensemble du texte.
   C'est la lecture définitive, le texte de CMP, ou la dernière lecture à
   l'AN quand l'adoption définitive a lieu au Sénat (Kasbarian-Bergé,
   justice des mineurs). Les autres lectures sont affichées, pas comptées.
10. **Motions de rejet préalable : affichées, pas comptées.** Sur
    l'immigration, la motion écologiste a été adoptée (270-265) avec les
    voix du RN (87-0) et de LR (40-2). Ces deux groupes ont ensuite voté le
    texte de CMP (88-0 et 62-0). Compter « pour la motion » comme une
    opposition au texte les créditerait d'un vote favorable aux droits.
    Une motion déposée et adoptée par les soutiens du texte, pour
    l'envoyer directement en CMP (Duplomb), s'affiche dans ce sens :
    voter pour, c'est soutenir le texte.
11. **Amendements clés** : seuls entrent en compte les amendements de
    suppression ou de rétablissement d'un article qui porte une mesure
    citée par une source. Max fixe le sens de chacun, d'après le contenu de
    l'article et non d'après la nature de l'amendement. Sur la justice des
    mineurs, le RN propose de supprimer l'article 7, qui ajoute une
    garantie (rapport éducatif avant toute détention provisoire). Voter
    cette suppression va donc dans le sens du texte. **Un seul scrutin par
    article et par lecture** : celui qui a fixé le sort de l'article
    (l'amendement adopté, sinon le dernier mis aux voix). **Une seule
    lecture** : la dernière lecture de l'AN où des suppressions ont été
    mises aux voix. C'est la rédaction la plus proche du texte soumis au
    scrutin décisif (règle 6) : la 1re lecture pour le narcotrafic et la
    justice des mineurs, la 2e pour Kasbarian-Bergé. Une source
    « cite » une mesure quand elle la met en cause. Une décision du Conseil
    constitutionnel qui la décrit pour la valider ne suffit pas. Ne sont
    pas des amendements clés : la suppression d'un article unique, qui
    double le scrutin décisif, et un scrutin unanime (aucun vote d'un des
    deux côtés), qui ne départage personne. Selon les textes, on compte
    de 0 (immigration, aide à mourir) à 17 amendements clés (RIPOST).

## Positions de groupe

12. La position d'un groupe est sa **majorité parmi les exprimés** (pour
    contre contre), toujours affichée avec sa cohésion. Quand l'abstention
    l'emporte à la fois sur le pour et sur le contre, la position porte la
    mention « majoritairement abstentionniste ». En cas d'égalité entre pour
    et contre, la position est « partagée ». La cohésion est
    la part des votants du groupe (pour, contre et abstention) qui ont voté
    comme la position. Exemple : 10 pour, 2 contre et 8 abstentions donnent
    « pour », avec une cohésion de 50 %. datan.fr et
    leurs-votes.fr comptent l'abstention comme une position : l'écart
    touche environ 3 % des positions (`docs/SOURCES.md`, contrôle croisé).
13. **Mises au point** (un député déclare après coup qu'il voulait voter
    autrement) : affichées, pas comptées, puisque le résultat officiel ne
    change pas.

## Calcul des scores

14. **Vote favorable aux droits.** Sur chaque scrutin compté et pour chaque
    droit touché, voter « pour » est favorable ou défavorable selon deux
    sens : celui du droit (le texte l'étend ou le restreint) et celui du
    scrutin (voter pour va dans le sens du texte, ou contre lui). Sur un
    texte qui restreint un droit, voter contre le texte est favorable, et
    voter pour la suppression d'un de ses articles restrictifs aussi.
15. **Score** d'un député ou d'un groupe sur un droit : part pondérée de
    ses votes favorables parmi ses votes comptés, de 0 à 100. Le score
    « global » prend le sens du droit principal de chaque texte. Le score d'un droit compte les textes où ce droit est
    principal **et** ceux où il est secondaire, chacun avec son propre sens
    (sur l'immigration : `etrangers` restreint, `enfants` étend).
16. **Abstention : exclue du calcul.** Elle n'entre pas dans le score et
    s'affiche à côté (« 2 abstentions »). Elle n'est donc jamais assimilée
    à un vote contre. Simulation : la compter comme demi-vote favorable
    ferait perdre 8 points à ECOS et GDR en XVIIe.
17. **Absences et non-votants : hors calcul.** Un député
    absent n'a pas voté : il n'a pas de score sur ce scrutin. Un
    non-votant non plus, et c'est souvent la présidence de séance. Le taux
    de participation aux scrutins comptés s'affiche à côté du score.
18. **Pondération : chaque texte pèse 1.** Le scrutin décisif en vaut la
    moitié, et les amendements clés se partagent l'autre moitié à parts
    égales. Un texte sans amendement clé ne compte que son décisif, qui
    pèse alors 1. Un texte à neuf amendements n'écrase donc pas les autres.
    Simulation : compter chaque scrutin pour 1 ferait passer EPR de 37 à 20
    en XVIIe.
19. **Changement de groupe : le groupe du jour du vote.** Chaque vote
    compte pour le groupe où siégeait le député ce jour-là, d'après la
    ventilation officielle de l'AN. La fiche d'un député réunit tous ses
    votes et liste ses groupes successifs. Un groupe qui change de nom
    (nouvel organe à l'AN) forme une seule **lignée**, sous son nom le plus
    récent : SOC → SOC-A en XVIe, À Droite → UDR → UDDPLR en XVIIe
    (`pipeline/referentiels/groupes.yaml`). Le score d'un
    groupe agrège les votes de ses membres. On ne le calcule pas sur ses
    positions, qui servent à l'affichage scrutin par scrutin.
