# Méthodologie

Base de la page Méthodologie du site. Chaque règle de ce document est
**validée par Max** avant d'entrer en vigueur. Les règles ci-dessous l'ont
été le 29/10/2026, à la fin du spike de l'étape 1. Elles ont été testées
sur six textes témoins (`pipeline/referentiels/temoins.yaml`). Les règles
de calcul (abstention, absences, pondération, changement de groupe)
viendront à l'étape 2.

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
11. **Amendements clés** : seuls entrent en compte les amendements de
    suppression ou de rétablissement d'un article qui porte une mesure
    citée par une source. Max fixe le sens de chacun. Leur pondération sera
    décidée à l'étape 2 : selon les textes, on compte de 0 (immigration,
    rejetée d'emblée à l'AN) à 866 scrutins sur amendement (aide à
    mourir).

## Positions de groupe

12. La position d'un groupe est sa **majorité parmi les exprimés** (pour
    contre contre), toujours affichée avec sa cohésion. Quand l'abstention
    l'emporte à la fois sur le pour et sur le contre, la position porte la
    mention « majoritairement abstentionniste ». datan.fr et
    leurs-votes.fr comptent l'abstention comme une position : l'écart
    touche environ 3 % des positions (`docs/SOURCES.md`, contrôle croisé).
13. **Mises au point** (un député déclare après coup qu'il voulait voter
    autrement) : affichées, pas comptées, puisque le résultat officiel ne
    change pas.
