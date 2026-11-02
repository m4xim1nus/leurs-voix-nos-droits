# À valider par Max

Décisions préparées et pas encore tranchées. Chacune porte une
recommandation, que rien n'applique dans les données publiées tant que Max
ne l'a pas validée. Une fois tranchée, la décision passe dans
`docs/METHODO.md`, `pipeline/referentiels/temoins.yaml` ou
`docs/CONCEPTION.md`, et sa section disparaît d'ici.

Questions du cycle Suites de l'audit (02/11/2026), relevées par l'audit de cohérence du 01/11/2026. Aucune ne change un
score, sauf mention contraire. Réponse attendue : « ok » sur la recommandation, ou l'autre option.

## 1. Vigilance « ordre public » (règle 2)

La règle 2 dit que la propriété et l'ordre public n'entrent pas dans la grille, et que « quand un texte les étend », on le
signale en vigilance. Trois fiches le font pour l'ordre public (`casseurs-payeurs-2026`, `installations-illicites-gens-du-voyage-2026`,
`ripost-2026`), alors que presque tous les textes de police l'étendent sans le dire (`anti-casseurs-2019`, `silt-2017`,
`lopmi-2023`, `polices-municipales-2026`…).

- **A (recommandé)** : la vigilance de la règle 2 vise la **propriété** seulement. L'ordre public est l'objet même de tout texte
  de police : le signaler partout n'apprend rien au lecteur. Les trois vigilances perdent la mention de l'ordre public.
- B : l'ordre public partout où un texte l'étend, une vingtaine de fiches de police à compléter.

## 2. Validation du Conseil constitutionnel : vigilance ou champ du Conseil ?

Huit fiches citent en vigilance une validation du Conseil (`asap-2020`, `plui-bas-chablais-2023`,
`energies-renouvelables-2023`, `nucleaire-acceleration-2023`, `simplification-vie-economique-2026`, `montagne-vivante-2026`,
`urgence-agricole-2026`, `neonicotinoides-betteraves-2020`) ; d'autres ne le font pas (`simplification-urbanisme-2025`,
`loi-orientation-agricole-2025`). Le champ du Conseil affiche déjà la décision (règle 6).

- **A (recommandé)** : une décision du Conseil, validation, réserve ou censure, va dans le **champ du Conseil**, jamais en
  vigilance. La règle 5 réserve la vigilance aux critiques sourcées. Ce que dit une vigilance actuelle et qui manque au champ du
  Conseil y passe.
- B : une validation qui porte sur la mesure contestée va aussi en vigilance, dans toutes les fiches où c'est le cas.

Même question pour la vigilance « on qualifie le texte voté, mesure censurée » (`duplomb-2025`, `loi-orientation-agricole-2025`,
`simplification-vie-economique-2026`) : avec A, elle devient une phrase de la note.

## 3. Textes du seul Sénat sans source : un seul statut (règles 7, 24, 25)

Sept textes du seul Sénat sont publiés comme qualifiés, sans droit ni sens, avec « vote affiché, non compté »
(`acces-soins-territoires-ppl-2025`, `allocation-autonomie-etudes-2023`, `ecole-liberte-egalite-laicite-ppl-2023`,
`exploitation-sexuelle-en-ligne-senat-2026`, `formation-internes-mg-ppl-2022`, `lapi-2025`, `organisation-algorithmique-travail-2023`).
Quatre autres, dans le même cas, sont écartés (44555, 46652, 51477, 53956).

- **A (recommandé)** : **écartés**, avec le motif « aucune source admise ne se prononce sur … (règle 7) » et le décompte du Sénat.
  Une qualification cite au moins une source (règle 7), et un texte de l'Assemblée sans source est écarté. Le « vote affiché, non
  compté » de la règle 24 reste réservé au vote du Sénat sur un texte qualifié à l'Assemblée. Les sept textes perdent leur page de
  texte qualifié, et gardent leur motif dans la liste des écartés.
- B : tous dans les textes qualifiés, sans sens : les quatre écartés reviennent avec leur vote du Sénat affiché.

## 4. Texte adopté à main levée à l'Assemblée (règle 25)

La règle 25 assimile au texte du seul Sénat celui que l'Assemblée a « rejeté par une motion ou à main levée ». Elle ne dit rien
d'un texte **adopté** à main levée, sans aucun scrutin public de l'Assemblée sur l'ensemble. Cas : La Poste (DLR5L16N46271),
écarté pour l'Assemblée, voté en scrutin public au Sénat (SN2022-9, 253-91), sans que son motif en parle.

- **A (recommandé)** : la règle 25 couvre aussi l'adoption à main levée : aucun vote nominatif ne départage les député·es, le texte
  est trié pour le Sénat. La Poste est relue pour le Sénat (source admise ou non) et son motif le dit.
- B : la règle 25 ne vise que le rejet ; le motif de La Poste dit seulement que le Sénat n'est pas traité.

## 5. Motion de rejet adoptée sans aucune voix contre (règle 10)

La règle 10 affiche les motions, et celle des soutiens d'un texte « dans ce sens » (Duplomb). Cas nouveau, signalé par l'alerte
`lecture_posterieure` : sur l'A69 (`a69-riipm-2025`), la motion de la gauche a été adoptée 176-0 avec les voix des soutiens du
texte. L'afficher « pour = contre le texte » montrerait ces soutiens contre lui.

- **A (recommandé)** : une motion adoptée **sans aucune voix d'un côté** n'est pas affichée : comme un décisif unanime
  (règle 9), elle ne départage personne. La note dit le rejet et sa date. Brouillon prêt dans ce sens.
- B : l'afficher selon son dépôt (« contre le texte »), comme le veut la lettre de la règle 10.

## 6. Ratification d'ordonnances : date de référence (règle 4)

Le sens se lit sur le droit du jour du vote (règle 4). Une loi de ratification vote sur des ordonnances **déjà en vigueur** :
lue à la lettre, elle ne changerait rien au droit du jour, et `ratification-ordonnances-travail-2018` (restreint) n'aurait plus
de sens.

- **A (recommandé)** : une loi de ratification se lit par rapport au **droit antérieur aux ordonnances**. C'est le seul vote du
  Parlement sur leurs mesures, puisque la loi d'habilitation n'en fixait que le cadre. La fiche de 2018 garde son sens, et sa note
  dit sa date de référence.
- B : la lettre de la règle 4 ; les ratifications perdent leur sens, sauf pour les modifications qu'elles apportent aux ordonnances
  (effet sur les scores de 2018).

## 7. `regime-exception` : la méthode alignée sur le libellé de l'étiquette

`droits.yaml` définit l'étiquette par « états d'urgence, dispositifs temporaires ou expérimentaux, extension du droit
antiterroriste ». La méthode (grille, en tête de `METHODO.md`) ne cite que le temporaire et l'expérimental, alors que
`retention-2025` et `narcotrafic` portent l'étiquette pour une extension du droit antiterroriste (motifs publiés le 02/11/2026).

- **A (recommandé)** : ajouter à la méthode « et toute extension à d'autres infractions d'un pouvoir ou d'une durée réservés au
  terrorisme ». Aucune fiche ne change.
- B : retirer l'étiquette des deux fiches, et ce membre de phrase du libellé.

## 8. Motifs d'écart de même nature (formulation)

- **Calendrier électoral** (report ou fixation d'une élection) : motivé tantôt par la règle 8 (49374, 50450, 52655), tantôt par la
  règle 2 (39814, 41207). **Recommandé** : règle 2, organisation des pouvoirs publics, comme le mode de scrutin.
- **Statut d'une profession** : règle 8 (36973, 47755, 51346, 39648) ou règle 2 (47601, 47797). **Recommandé** : « aucune source
  admise (règle 7) » quand le droit au travail est en jeu, comme l'ont montré `aesh-corps-fonctionnaires-2026` et
  `psc-agents-territoriaux-2025` ; règle 8 sinon.
- **Textes sans vote sur l'ensemble** : 14 écartés en XVIe, 63 dossiers voisins jamais triés. **Recommandé** : rien à changer. Un
  texte sans vote sur l'ensemble n'est trié que si une alerte le demande (`vote_sans_decisif`), et un écart déjà écrit reste exact.

## 9. Union nationale de l'apiculture française (règle 7)

Un amendement clé de `neonicotinoides-betteraves-2020` reposait sur elle seule, présentée comme « partie prenante ». Elle se dit
« syndicat apicole représentatif », et la Cour de cassation la traite en union de syndicats (soc., 13/01/2009, n° 07-17.692) :
c'est une organisation professionnelle agricole. La règle 7 n'admet que celles du droit, de la santé et de l'enseignement. Une note
commune de septembre 2020 contre ce projet de loi, signée par seize organisations dont Générations Futures, Greenpeace France, la
LPO, Pollinis et Foodwatch, met en cause la même mesure.

- **A (recommandé)** : l'Union nationale de l'apiculture française n'est pas une source admise seule ; la fiche cite la note
  commune à sa place. L'amendement clé reste, et aucun score ne change. Ne pas la confondre avec l'UNAF des familles, admise.
- B : l'admettre comme association porteuse d'un dispositif (partie prenante), ce que la règle 7 réserve aux associations.

## 10. Structures régionales d'un syndicat admis (règle 7)

`langues-regionales-2021` cite en vigilance la FSU Bretagne. La règle 7 admet les confédérations, leurs fédérations et leurs
syndicats nationaux, et exclut les syndicats d'entreprise ; elle ne dit rien des structures régionales ou départementales. Aucune
publication de la FSU nationale sur l'article 6 n'a été trouvée.

- **A (recommandé)** : les structures régionales et départementales ne sont pas admises, comme les syndicats d'entreprise : elles
  ne parlent pas au nom de la branche. La vigilance FSU Bretagne est retirée. Le texte étendant un droit contesté, la note dit
  alors « aucune critique trouvée parmi les sources admises » (règle 7), sauf si le communiqué de la FNEC FP-FO du 31/05/2021,
  que nous n'avons pas pu ouvrir, se révèle lisible.
- B : les admettre quand elles s'expriment sur une mesure propre à leur territoire (ici, les langues régionales).
