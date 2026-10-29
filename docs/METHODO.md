# Méthodologie

Base de la page Méthodologie du site. Chaque règle de ce document est
**validée par Max** avant d'entrer en vigueur. Les règles 1 à 13 l'ont été
le 29/10/2026, à la fin du spike de l'étape 1. Les règles de calcul (14 à
19) l'ont été le même jour, à l'étape 2, sur simulation des six textes
témoins (`pipeline/referentiels/temoins.yaml`).
Le choix de la lecture et la notion de source qui « cite » une mesure (règle
11) l'ont été le même jour, sur le cas de Kasbarian-Bergé, puis les
exclusions de la règle 11 et les motions « inversées » (règle 10), à la
relecture des vingt et un premiers textes. L'accès aux soins (règle 2), les
résolutions et les conventions (règle 8) et le décisif unanime (règle 9)
l'ont été au lot de tri des candidats, toujours le 29/10/2026. Au lot 3, le
même jour : le choix d'une source d'énergie hors grille (règle 2), les
instances consultatives indépendantes et les syndicats de salariés parmi
les sources (règle 7), l'article unique sans vote sur l'ensemble (règle 9).
Toujours le 29/10/2026 : la grille v1 (droits civiques et politiques) et
le texte adopté par 49.3 sans vote final (règle 9). Puis, au lot 4 et au tri
complémentaire, le même jour : le sens d'un texte composite et la date de
référence du sens (règle 4), les fédérations syndicales, l'ANSES et la
source qui porte sur la mesure (règle 7), les motions de censure
spontanées (règle 8), l'article unique supprimé par amendement (règle 9).
Au lot 5, toujours le 29/10/2026 : le périmètre de `citoyennete` (règle 2),
les mesures qui ne visent que des personnes détenues (règle 3), le corps
électoral et les droits d'un peuple autochtone (règle 4), les lois de
finances de fin de gestion (règle 8), l'article devenu seul au scrutin
décisif (règle 11). Au lot 6, le même jour : la loi qui rétablit une règle
abrogée par le Conseil constitutionnel (règle 4), l'article dont les
sources ne s'accordent pas sur le sens (règle 11).

## Grille des droits

Grille v1 : `pipeline/referentiels/droits.yaml`. Douze droits et deux
étiquettes transversales (`outre-mer`, `regime-exception`). La v1 ajoute à
la v0 les **droits civiques et politiques** (`citoyennete` : droit de vote,
élections, citoyenneté), d'abord hors grille (corps électoral de
Nouvelle-Calédonie).

1. **Point de vue.** Le sens se lit toujours du point de vue des droits des
   personnes concernées, jamais des prérogatives de l'État. Un texte qui
   donne de nouveaux moyens à la police « restreint » les garanties des
   personnes face à elle.
2. **Périmètre.** La grille suit les droits des personnes face à la
   puissance publique et aux plus forts. La propriété et l'ordre public
   sont des objectifs que le législateur concilie avec ces droits : ils
   n'entrent pas dans la grille. Quand un texte les étend (Kasbarian-Bergé,
   pour la propriété), on le signale en point de vigilance. L'**accès aux
   soins** entre dans `sante` (régulation de l'installation des médecins,
   accès direct aux professionnels). Le financement de la recherche n'y
   entre pas. Les droits civiques et politiques (droit de vote, corps
   électoral de Nouvelle-Calédonie), hors de la grille v0, entrent dans la
   v1 (`citoyennete`). Ce droit couvre qui peut voter et être élu, et les
   conditions d'exercice du vote (inscription, procuration, vote par
   correspondance). Le **mode de scrutin** et le **régime des mandats**
   (cumul, incompatibilités) relèvent de l'organisation des pouvoirs
   publics : ils n'entrent pas dans la grille (Paris, Lyon et Marseille,
   2025). Le
   **choix d'une source d'énergie** (nucléaire, renouvelables) n'est pas
   un droit de la grille : le droit `environnement` se juge sur les
   garanties des personnes (information, participation du public,
   protection des milieux). Les deux lois d'accélération de 2023, qui
   allègent les mêmes garanties, sont donc qualifiées dans le même sens.
3. **Recouvrements**, tranchés par une règle fixe :
   - justice des mineurs → `enfants` principal, `police-justice`
     secondaire ;
   - technique de surveillance → `vie-privee` principal, `libertes`
     seulement si une source le relève ;
   - mesure qui ne vise que des étrangers → `etrangers` principal ;
   - mesure qui ne vise que des personnes détenues → le droit en cause
     principal, `police-justice` secondaire (vote par correspondance des
     détenus, 2025 : `citoyennete` principal).
4. **Sens droit par droit.** Chaque droit touché reçoit son sens (`etend`
   ou `restreint`). Il n'y a pas de sens « mixte » global : le sens
   affiché pour le texte est celui de son droit principal. Exemple,
   l'immigration : `etrangers` restreint, `enfants` étend.
   Le sens se lit par rapport au **droit applicable au jour du vote,
   jurisprudence comprise** : une loi qui met le code du travail en
   conformité avec la Cour de cassation, en plafonnant ce que la
   jurisprudence accordait déjà, restreint le droit (congés payés pendant
   la maladie, 2024). De même, une loi qui rétablit une règle que le
   Conseil constitutionnel avait abrogée, en l'assortissant de la garantie
   qu'il exigeait, restreint le droit par rapport au jour du vote (purge
   des nullités en matière correctionnelle, 2024).
   Dans un **texte composite** dont les mesures vont en sens opposés pour
   un même droit, le sens de ce droit est celui des mesures que les sources
   admises citent le plus souvent. La mesure de sens opposé s'affiche en
   vigilance (PLFSS 2026 : arrêts de travail limités, `restreint` ;
   suspension de la réforme des retraites, en vigilance).
   Le sens d'une mesure sur le **corps électoral** se lit, pour
   `citoyennete`, sur le droit de vote des personnes qu'elle ajoute à la
   liste ou en retire. Quand une source admise y voit une atteinte aux
   droits d'un peuple autochtone, le texte reçoit aussi `discriminations`
   en secondaire, au sens `restreint`. Les deux lectures sont alors
   comptées, chacune pour son droit (Nouvelle-Calédonie, 2024).
5. **Points de vigilance.** Les critiques sourcées portant sur la mise en
   œuvre ou sur l'insuffisance des garanties s'affichent à côté du
   jugement, sans le modifier (aide à mourir).
6. **Objet qualifié.** On qualifie le texte soumis au scrutin décisif,
   puisque c'est le vote du député qui est mesuré. La décision du Conseil
   constitutionnel s'affiche à côté (« 32 articles censurés »).
7. **Sources.** Chaque qualification cite au moins une source publique :
   - CNCDH, Défenseur des droits, Conseil constitutionnel ;
   - CNIL, CGLPL, et les autres instances consultatives indépendantes
     créées par la loi ou le règlement qui rendent des avis publics (Haut
     Conseil à l'égalité, Commission nationale du débat public, Haut Comité
     pour le logement des personnes défavorisées, Autorité
     environnementale…), et, pour la santé et l'environnement, l'ANSES ;
   - rapporteurs et comités de l'ONU ;
   - ONG ;
   - pour la santé, ordres professionnels et sociétés savantes ;
   - organisations professionnelles et syndicales du droit, de la santé et
     de l'enseignement (Conseil national des barreaux, Syndicat des avocats
     de France, Syndicat de la magistrature…) ;
   - organisations syndicales représentatives de salariés (CGT, CFDT, FO,
     CFE-CGC, CFTC, UNSA, FSU, Solidaires), y compris leurs fédérations
     professionnelles, qui parlent en leur nom dans une branche ou une
     fonction publique ; pas les syndicats ou sections d'entreprise ;
   - avis du Conseil d'État sur un projet ou une proposition de loi.

   Ne sont pas des sources les rapports parlementaires ni les positions du
   Gouvernement ou des groupes, qui sont parties au débat. La Cour des
   comptes non plus : elle évalue la dépense et l'efficacité des
   politiques publiques, pas les droits.

   Une source peut porter sur la **mesure** plutôt que sur le texte, même si
   elle lui est antérieure : il suffit qu'elle se prononce sur la mesure que
   le texte inscrit (avis de l'ANSES sur le plafond de cadmium).

   Quand un texte étend un droit contesté, au moins une source critique
   figure en vigilance. Si aucune source admise ne conteste le droit
   étendu, aucune vigilance n'est exigée, et la note de méthode le dit
   (« aucune critique trouvée parmi les sources admises »).
8. **Textes purement organisationnels** (par exemple la loi organique
   jumelle du narcotrafic) : non qualifiés. Ne sont pas qualifiées non
   plus les **résolutions**, qui expriment un avis de l'Assemblée sans
   changer aucune règle (commissions d'enquête comprises), ni les **lois
   autorisant la ratification d'une convention internationale**, dont le
   vote ne porte sur aucune mesure de droit interne. N'est pas qualifié
   enfin un texte qui, au scrutin décisif, ne contient plus aucune mesure
   normative : ses articles ont été supprimés et il ne reste que des
   demandes de rapport ou un gage. Ne sont pas qualifiées, enfin, les
   **motions de censure spontanées** (article 49, alinéa 2) : elles ne
   portent sur aucun texte, et seules les voix pour la censure y sont
   décomptées. Ne sont pas qualifiées non plus les **lois de finances de
   fin de gestion** : depuis la réforme de 2021 de la loi organique
   relative aux lois de finances, elles ne font qu'ouvrir et annuler les
   crédits de l'année, sans disposition fiscale. Les lois de finances
   initiales et rectificatives se qualifient comme les autres textes.

## Scrutins retenus

9. **Scrutin décisif** : le dernier vote de l'AN sur l'ensemble du texte.
   C'est la lecture définitive, le texte de CMP, ou la dernière lecture à
   l'AN quand l'adoption définitive a lieu au Sénat (Kasbarian-Bergé,
   justice des mineurs). Les autres lectures sont affichées, pas comptées.
   Quand un texte à **article unique** n'a pas de vote sur l'ensemble
   (article rejeté, puis texte tombé ou retiré), le vote sur l'article
   unique tient lieu de scrutin décisif. De même, quand l'amendement qui
   **supprime l'article unique** est adopté et que le texte n'est plus voté,
   ce scrutin tient lieu de décisif : voter pour, c'est voter contre le
   texte (délit de séjour irrégulier, 2025). Dans le cas habituel (article
   adopté, puis vote sur l'ensemble), le vote sur l'article double le
   décisif et n'est pas retenu.
   Un texte dont le scrutin décisif n'a **aucune voix d'un des deux côtés**
   (loi intégrale contre les violences sexuelles et sexistes, 503-0) n'est
   pas qualifié : ce vote ne départage personne, et le compter rapprocherait
   tous les scores de 100. Une voix suffit pour qu'il départage (même seuil
   que pour les amendements, règle 11).
   Un texte **adopté par le 49.3 sans vote final** à l'AN (retraites 2023,
   PLF 2026) est qualifié, mais **compté dans aucun score**, amendements
   clés compris. Ses motions de censure s'affichent groupe par groupe
   (rôle `censure`) : un scrutin de censure n'enregistre que les voix pour
   la censure, et ne dit donc rien de ceux qui ne l'ont pas votée.
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
    l'article et non d'après la nature de l'amendement. Un article dont le
    sens n'est pas univoque n'est pas retenu, y compris quand les sources
    admises ne s'accordent pas sur ce sens (primes de partage de la valeur,
    2023 : mises en cause par la CGT, soutenues par la CFDT et FO). Sur la justice des
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
    deux côtés), qui ne départage personne. Un article qui est le seul
    du texte au scrutin décisif est traité comme un article unique : sa
    suppression ou son rétablissement double le décisif (épandage par
    drones, 2025 : l'article 2, simple gage, a été supprimé). Selon les textes, on compte
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
    Limite connue : on mesure le vote, pas son motif. Un groupe qui vote
    contre un texte étendant un droit parce qu'il le juge insuffisant
    (tests de discrimination, 2023) est compté défavorable, comme celui
    qui s'y oppose sur le fond.
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
