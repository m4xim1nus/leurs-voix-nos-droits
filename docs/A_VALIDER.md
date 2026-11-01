# À valider par Max

Décisions préparées et pas encore tranchées. Chacune porte une
recommandation, que rien n'applique dans les données publiées tant que Max
ne l'a pas validée. Une fois tranchée, la décision passe dans
`docs/METHODO.md`, `pipeline/referentiels/temoins.yaml` ou
`docs/CONCEPTION.md`, et sa section disparaît d'ici.

## Cycle Recherche : à trancher avant la fusion

Prises par Claude pendant l'absence de Max (01/11/2026). Aucune ne touche un score ni `editorial.json`.

1. **Stockage des termes** : YAML dans `pipeline/referentiels/`, exporté en CSV. *Recommandation : garder.* Pas de saisie dans
   l'admin avant la passation ; un texte sans terme reste trouvable par son titre.
2. **Surnoms** : clés de recherche, jamais affichés sur les pages, mais publics dans `termes_recherche.csv` et annoncés sur la
   page Méthodologie. *Recommandation : garder.*
3. **Termes écartés d'office** : aucun nom de victime ou de personne mise en cause (une loi ne se retrouve donc pas par le nom
   d'une affaire), aucune formule militante (« tueurs d'abeilles », « préférence nationale », « bétonisation », « Kanaky »).
   Quelques noms de responsables restent (Borne, Delevoye, Dati), et quelques marques (Airbnb, Shein, TikTok, OnlyFans).
   *Recommandation : garder cette ligne, et ajuster en relisant.* Relire : `pipeline/referentiels/termes_recherche.yaml`, surtout
   les `surnoms` (47).
4. **Six rattachements absents du tableau de 2009** : Serbie, Monténégro, Kosovo (7e), Territoires palestiniens (8e), Soudan du Sud
   (10e), Taïwan (11e). Déduits du poste consulaire et de Wikipédia, pas d'un texte officiel, et signalés à côté du résultat.
   *Recommandation : garder.* La Corée du Nord, absente, ne donne aucun résultat.
5. **Texte de la Méthodologie** : le paragraphe « Recherche » dit que les termes sont préparés avec l'assistant et relus. Il ne
   devient exact qu'après la relecture du point 3.
6. **Poids de l'index** : 103 Ko compressés pour `textes.json` (44 Ko prévus au backlog, sans les 620 écartés). *Recommandation :
   accepter*, chargé une seule fois, à la première frappe.
