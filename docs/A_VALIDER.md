# À valider par Max

Décisions préparées et pas encore tranchées. Chacune porte une
recommandation, que rien n'applique dans les données publiées tant que Max
ne l'a pas validée. Une fois tranchée, la décision passe dans
`docs/METHODO.md`, `pipeline/referentiels/temoins.yaml` ou
`docs/CONCEPTION.md`, et sa section disparaît d'ici.

## Cycle Sénat, suite (préparé le 01/11/2026)

Branche `senat-suite`, non fusionnée. Le code, `docs/METHODO.md` et la page Méthodologie **appliquent déjà ces recommandations sur la
branche**, pour qu'elles puissent être essayées : ne pas fusionner avant la décision de Max. Rien n'est validé, chargé dans D1 ni publié.

### 1. Règle 26 : deux périodes

*Recommandation :* deux périodes, de juin 2017 à juin 2022 et depuis le 28/06/2022, un texte comptant dans la période de son décisif. Les
scores d'un groupe se lisent par période. Celui d'un·e sénateur·ice réunit tous ses votes et se lit aussi par période, comme un·e député·e
(règle 19). Les scores de groupe depuis 2022 ne bougent pas.

*Écartée :* couper aux renouvellements (2017, 2020, 2023, 2026). C'est plus fidèle à la composition du Sénat, mais la dernière période
n'aurait presque aucun vote, et les périodes ne suivraient plus les textes de la XVe.

*Limite :* les groupes gardent leur nom actuel, faute d'historique des noms dans l'open data (RDPI en 2018, par exemple). La page le dit.

### 2. Règles 23 et 26 : amendements clés du Sénat

*Recommandation :* mêmes conditions que la règle 11, sur la dernière lecture du Sénat où des suppressions ont été mises aux voix, et même
poids qu'à l'Assemblée (la moitié du texte pour le décisif, l'autre partagée entre les amendements). Sur 87 candidats hors budgets, 20 sont
retenus sur 15 textes. Cela change des scores du Sénat depuis 2022 : ceux de la simulation sont dans la fiche de relecture.

*Point à trancher :* quand le décisif est antérieur à cette dernière lecture (bioéthique : décisif de 1re lecture, suppressions de 2e
lecture), la règle prise à la lettre ne retient rien. *Recommandation :* la garder telle quelle, une règle fixe valant mieux qu'une exception ici.

### 3. Amendements clés des budgets

52 candidats sur les lois de finances et de sécurité sociale, **non lus**. *Recommandation :* ne pas les traiter dans ce cycle : la lecture
demande une recherche par mesure. Tant qu'ils ne sont pas lus, un budget ne compte au Sénat que par son décisif, alors que les autres textes ont
leurs amendements clés. Le manque est dit dans la fiche de relecture et mis au backlog.

### 4. Correspondance entre les groupes des deux chambres

*Recommandation :* ne pas la faire, et passer l'item en `[refusé]`. Elle demanderait un jugement au cas par cas (RDPI et Ensemble, UC et
MoDem ou Horizons, un groupe SER qui réunit des écologistes), contraire à la règle fixe et à la règle 28. Comparer existe pour le Sénat, à
l'intérieur de la chambre (`/senat/comparer`).

### 5. Mise en service, après décision

Dans cet ordre : fusionner `senat-suite` ; déployer l'admin, dont les contrôles acceptent désormais le rôle `amendement` ; faire tourner la
synchronisation du catalogue (`lvnd sync-admin --remote`) ; charger les brouillons validés ; publier. Entre la fusion et la publication,
« À traiter » montre environ 90 alertes `senat_premier_vote` : c'est attendu, et aucun score ne change avant la publication.
