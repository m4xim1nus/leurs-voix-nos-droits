# À valider par Max

Décisions préparées et pas encore tranchées. Chacune porte une
recommandation, que rien n'applique dans les données publiées tant que Max
ne l'a pas validée. Une fois tranchée, la décision passe dans
`docs/METHODO.md`, `pipeline/referentiels/temoins.yaml` ou
`docs/CONCEPTION.md`, et sa section disparaît d'ici.

## 4. Vote du Sénat sur un texte suivi, sans voix contre (ingérences étrangères)

**Le cas.** Le projet de loi sur les ingérences étrangères (DLR5L17N54703) est publié comme **fiche de suivi**. Le Sénat
l'a adopté en 1re lecture par 340 voix contre 0 (SN2026-21) ; il est attendu à l'Assemblée. L'alerte « vote du Sénat à
lire » s'affiche, et l'essai du mode Sénat du LLM (02/11/2026) relève deux trous :

- la règle 23 dit qu'un vote sans voix d'un côté est « affiché et non compté », mais un texte qui n'est pas qualifié à
  l'Assemblée n'a pas de fiche où l'afficher ; la règle 25 ne prévoit l'écart au Sénat que faute de source ;
- la règle 22 interdit tout scrutin dans une fiche de suivi, alors que le vote du Sénat demanderait un bloc `senat`.

**Recommandation.** Deux phrases fixes :

- **Règle 22** : une fiche de suivi ne porte jamais de vote, de l'Assemblée ni du Sénat. Le vote du Sénat s'ajoute
  quand le texte est qualifié, après le vote de l'Assemblée (ou selon la règle 25 s'il n'y en a pas).
- **Règle 23** : sur un texte qui n'est pas qualifié à l'Assemblée (suivi ou non traité), un vote du Sénat sans voix
  d'un côté ne demande rien : comme à l'Assemblée (règle 9), il ne départage personne. L'alerte `senat_premier_vote` ne
  se déclenche pas sur un tel vote. Le texte reste suivi et attend l'Assemblée.

Conséquence ici : rien à publier ; l'alerte disparaît une fois la règle appliquée (`alertes.py` et
`admin/src/lib/alertes.ts`).

Les trois cas non prévus précédents ont été tranchés le 02/11/2026 (recommandations suivies) et sont passés dans
`docs/METHODO.md` : médico-social admis comme santé (règle 7), fiche de suivi sur le dernier état connu du texte
(règle 22), loi de finances rejetée par une partie (règle 25) et écart faute de vote sur l'ensemble à l'Assemblée,
qualifiable au Sénat (règle 28).
