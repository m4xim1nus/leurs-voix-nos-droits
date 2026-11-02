# Changelog

Format inspiré de [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/).
Les tags `v*` du dépôt suivent ces versions.

## [1.9.0] — 2026-11-02

Cycle Suites de l'audit, et ce qui l'a précédé le même jour : les reliquats de l'audit de cohérence soldés, dix règles de
méthode tranchées et appliquées, deux manques de l'outil comblés. Les scores changent sur une dizaine de textes. Au
02/11/2026 : 199 textes qualifiés, 672 écartés, 3 fiches de suivi.

### Ajouté

- Alerte `lecture_posterieure` : lecture de l'AN close après le décisif d'un texte qualifié sans scrutin public sur l'ensemble
  (main levée, motion de rejet). `vote_posterieur` couvre aussi les textes qualifiés sans décisif à l'AN (texte qualifié sur
  le vote du Sénat).
- Admin : une note interne par texte (D1 seule, jamais publiée), en haut de la fiche et dans « À traiter » (migration 0005).
- Admin : « Publier » refuse de remettre l'ancienne version d'un texte modifié dans le dépôt hors de l'admin. La comparaison
  est sautée quand le fichier du dépôt est celui de la dernière publication (migration 0006).
- Qualifications : homicide routier (2025), Rist 2021 (sages-femmes), ZAN (2023), La Poste (2022, Sénat seul), directeurs
  d'école (2021). Amendements clés nouveaux : PLFSS 2026 (article 26 bis), urgence agricole (article 5), justice criminelle
  (article 3), quatre budgets au Sénat.
- Présentation : PDF vectoriel au texte sélectionnable, refait par `docs/presentation/imprimer.py`.

### Modifié

- Méthode (règles 2, 4, 5, 7, 8, 10, 25 et étiquette `regime-exception`) : vigilance réservée à la propriété, l'ordre public
  n'est plus signalé ; calendrier électoral hors grille ; ratification d'ordonnances lue sur le droit antérieur ; la décision du
  Conseil constitutionnel sur le texte quitte les vigilances pour son champ (40 fiches) ; structures régionales d'un syndicat et
  organisations professionnelles d'autres secteurs non admises ; statut d'une profession ; motion votée sans voix d'un côté non
  affichée ; texte adopté à main levée à l'AN trié pour le Sénat ; texte du seul Sénat sans source écarté (7 textes) ; extension
  du droit antiterroriste dans `regime-exception`. Aussi : conseils de l'ordre des barreaux admis, justice civile et commerciale
  hors de `police-justice`.
- Résumés des six fiches témoins, écrits sur le texte voté ; audit de forme appliqué à 218 fiches et motifs (formules
  unifiées, règles citées, étiquettes motivées), sans effet sur les scores.
- Termes de recherche : une clé d'écart devenue qualifiée n'est plus une erreur de `lvnd check`, mais un avertissement.
- `lvnd sync-admin --simuler` refusé hors du sync incrémental du catalogue.
- Passes de données à 4 h 17 (lundi) et 5 h 17 UTC, hors de l'heure pile que GitHub sautait.

### Limites connues

- Les qualifications de La Poste et des directeurs d'école reposent sur des sources syndicales seules, et celle de l'article 26 bis
  du PLFSS 2026 sur un syndicat de médecins.
- La page « Publier » reste proche de la limite de calcul d'un Worker gratuit : une erreur 1102 passagère est possible
  (`docs/EXPLOITATION.md`).

## [1.8.0] — 2026-11-01

Cycle Sénat, suite : le Sénat de 2017-2022, lu comme celui d'après. Les scores du Sénat changent, depuis 2022 aussi : ils comptent
désormais des amendements clés. Aucun score de l'Assemblée ne bouge.

### Ajouté

- **Données** : scrutins et votes du Sénat depuis le 27/06/2017, soit 2 243 scrutins et 780 054 votes. Contrôle croisé sur 247 pages de
  senat.fr, aucun écart.
- **Qualifications** : 46 textes de la XVe lus pour le Sénat, dont 37 comptés et 9 affichés ; 50 textes votés au seul Sénat écartés au tri.
- **Amendements clés du Sénat** : 19 retenus sur 87 candidats hors budgets, sur 14 textes.
- `/senat/comparer` : deux sénateur·ices, deux groupes, ou un·e sénateur·ice et un groupe sur la période de ce groupe. Jamais avec l'Assemblée.
- Cartes partageables des sénateur·ices, avec la mention « votes enregistrés à son nom ».
- `senat/scores_senateurs_periodes.csv`, et la colonne `a_vote` d'`appartenances.csv`.

### Modifié

- Règle 26 : deux périodes coupées au 28/06/2022, un texte comptant dans celle de son décisif, et amendements clés aux conditions de la règle 11.
  `senat/scores_groupes.csv` gagne la colonne `periode`. `/senat` et l'aperçu de l'admin se lisent par période.
- Fiche d'un groupe NI : seuls les député·es qui y sont, ou qui y ont voté, et non toute l'Assemblée.
- `lvnd sync-admin` envoie dans D1 les amendements du Sénat, nécessaires pour les retenir.

### Limites connues

- Les 52 amendements candidats des lois de finances et de sécurité sociale ne sont pas lus : un budget ne compte au Sénat que par son décisif.
- Les groupes du Sénat gardent leur nom actuel, faute d'historique dans l'open data, y compris sur 2017-2022.
- `justice-criminelle-2026` compte peut-être à l'Assemblée un amendement clé sur une mesure absente du texte de la CMP, à vérifier (`BACKLOG.md`).
- Plusieurs sources n'ont pas pu être lues (refus d'accès, PDF scannés lus en partie) : détail dans la fiche privée de relecture.
- La passe du 02/11/2026 n'a pas tourné au moment du tag.

## [1.7.1] — 2026-11-01

Fin du cycle Prise en main : la page d'aide, restée hors du commit de la v1.7.0.

### Ajouté

- Page d'aide dans l'admin (`/aide`) : captures numérotées de chaque écran, tableau des alertes, premier essai à cocher.
  Elle remplace `docs/TUTORIEL_ADMIN.md`, retiré dès la v1.7.0.

### Limites connues

- Elle n'a pas encore été essayée par un·e rédacteur·ice, et ses captures sont à refaire si un écran change.

## [1.7.0] — 2026-11-01

Cycle Prise en main : audit de cohérence et revue des qualifications sensibles, supports pour reprendre le projet,
finitions avant de le montrer. Les scores changent, surtout en XVe et XVIe : amendements clés retirés et cinq décisions
sur des textes écartés.

### Ajouté

- Lien « Exploitation » dans l'admin vers `docs/EXPLOITATION.md` : ce qui tourne quand, ce qui bloque un commit, quoi faire
  en cas d'échec.
- Présentation du projet, `docs/presentation/` : 19 slides avec notes, source Bento éditable et PDF, hors du site et de l'admin.
- `/llms.txt` et dictionnaire des données (`/donnees.md`), avec un test qui échoue si une colonne y manque.
- Alerte `ecart_revote` : un texte écarté pour un autre motif que l'unanimité, revoté à l'Assemblée.
- Section `corrections:` de `rattachements.yaml`, qui prime sur le dump, et `pipeline/explo/rattachement_objet.py`.

### Modifié

- Règle 4 : décompte des sources, choix du droit principal, mesure d'un autre droit en secondaire, constat de discrimination.
- Règle 11 : mesure absente du texte décisif, critique visant seulement un droit secondaire de sens opposé, réserve du
  Conseil constitutionnel.
- Qualifications : audit de 199 textes et 620 écarts, puis 61 fiches relues sur décision de Max. Amendements clés alignés sur
  la règle 11, droits secondaires ajoutés ou retirés, motifs d'écart corrigés. RIPOST compte 18 amendements clés.
  Nouveaux qualifiés : EGalim, révision constitutionnelle de Nouvelle-Calédonie (Sénat seul), inscription d'office en
  Nouvelle-Calédonie. Écarté : droit de visite des parlementaires dans les établissements sociaux et médico-sociaux.
- En-tête du site à cinq rubriques (Droits, Textes, Groupes, Sénat, Méthode), avec sous-onglets. Les adresses ne changent pas.
- Recherche : repli sur la saisie corrigée quand rien ne correspond, signalé à l'écran. Le code postal donne aussi les
  sénateur·ices du département, et la case de `/senat` disparaît.
- Admin : la version `autre` du Sénat se saisit aux formulaires habituels, sans JSON.

### Corrigé

- V6758 (loi d'urgence agricole) était rattaché à la loi organique sur les natifs de Nouvelle-Calédonie. Sans effet sur les scores.

### Limites connues

- La passe du 02/11/2026 n'a pas tourné au moment du tag (`BACKLOG.md`, « À trier »).
- L'audit a comparé les fiches, sans relire toutes les sources. Ses écarts de forme ne sont pas tous traités (`BACKLOG.md`).
- Le PDF de la présentation est fait de captures : son texte ne se sélectionne pas. Ses chiffres se mettent à jour à la main.
- Sites refusant la lecture automatique (France Nature Environnement, Générations Futures, Légifrance) : ZAN 2023 et plastiques dangereux restent écartés faute d'avoir pu lire ces pages.

## [1.6.0] — 2026-11-01

Cycle Recherche : on peut désormais chercher un texte, et plus seulement un·e élu·e. Aucune qualification,
aucun score ni décisif modifié ; `editorial.json` est inchangé.

### Ajouté

- Case de recherche dans l'en-tête, sur toutes les pages : élu·es, code postal, pays, textes qualifiés et à
  suivre, textes écartés avec leur motif. Menu au clavier, et page `/recherche?q=…` pour tous les résultats.
- Index statiques `textes.json` et `pays.json`, chargés avec ceux des élu·es à la première frappe. Le moteur
  tourne dans le navigateur : aucune requête ne dit ce que l'on cherche.
- `pipeline/referentiels/termes_recherche.yaml` : environ 1 780 termes courants et surnoms d'usage public
  (« APL », « loi Duplomb »), cherchés et jamais affichés, publics dans `termes_recherche.csv`. `lvnd check`
  refuse une clé inconnue et les termes de la liste privée, et signale un texte qualifié sans terme.
- `pipeline/referentiels/pays_circonscriptions.yaml` : 194 pays et territoires → circonscription des Français
  établis hors de France (code électoral, tableau n° 1 ter), publics dans `pays_circonscriptions.csv`.
- Méthodologie : paragraphes « Français établis hors de France » et « Recherche ».

### Modifié

- Case de l'accueil : elle trouve aussi un pays et donne le ou la député·e de la circonscription.

### Limites connues

- Aucune tolérance aux fautes de frappe ; la case de `/senat` ne cherche que les sénateur·ices.
- Six pays et territoires absents du tableau de 2009 (Serbie, Monténégro, Kosovo, Territoires palestiniens,
  Soudan du Sud, Taïwan) sont rattachés d'après le poste consulaire et Wikipédia, et le site le signale.
- Un texte nouvellement qualifié n'a pas de termes tant qu'on ne les ajoute pas au YAML, hors de l'admin. Il
  reste trouvable par son titre et son résumé.
- Essayé dans Chromium seulement, sur bureau et mobile : ni Firefox, ni Safari, ni lecteur d'écran.

## [1.5.0] — 2026-11-01

Cycle Relecture XVe : relecture de ce que la v1.4.0 a publié, reliquats d'outillage et de
catalogue. Aucune nouvelle qualification, aucun score ni décisif modifié.

### Ajouté

- Alerte `vote_sans_decisif` : lecture de l'AN close sans décisif proposé (rejet d'une partie, vote
  sans scrutin public), sur un texte ni qualifié, ni écarté, ni à l'arrêt. 3 à la sortie, dont le PLFSS 2027.
- Fiche député·e : les textes du seul Sénat attendus à l'AN dans « Prochains votes ».
- Nombre de textes écrit sur `/groupes`, `/droits/<code>` et l'accueil.

### Modifié

- Règle 19 : la fiche et la carte d'un·e député·e ne le comparent à son groupe que sur la législature de
  ce groupe (décision de Max). Le score global reste le chiffre principal.
- Filtre Législature de `/textes` tiré des données, XVe comprise, « Toutes » par défaut.
- Le compteur de l'accueil compte les textes en cours du seul Sénat : 27 au lieu de 16, comme `/en-cours`.
- `lvnd check` : plus de délai sur le taux d'amendements d'une législature close (XVIe : 3 159/3 173).
- `lvnd download --leger` : réutilise un plan B achevé et, si rien n'est là, part de la release sans
  attendre le dump de l'AN. Un fichier partiel périmé se purge seul.
- Marche à suivre du build local dans `docs/SOURCES.md` : il redonne les exports à l'octet près, sauf
  `meta.json`, à dumps identiques.

### Corrigé

- Déclarations du Gouvernement rattachées au texte du jour : elles ne vont plus qu'à leur propre dossier,
  aussi en XVIIe (V4698). Rattachements figés prioritaires sur la séance : V1093, V1094, V1518.
- Catalogue : titre de la programmation de la recherche (2030), sens de la décision 2021-817 DC.
- Fiches : espaces manquantes, libellé « Travail et protection sociale » tronqué, « ses mandats ».

### Limites connues

- Passe quotidienne pas encore observée avec la XVe ni avec ce code, à vérifier le 02/11/2026 (`BACKLOG.md`).
- Relecture faite sans Max, sur un échantillon de pages : pas de relecture commune à l'écran.
- `/comparer` confronte encore le score global d'un·e député·e au score d'un groupe sur sa législature.
- V45, V738 et V1612 : le titre et l'amendement citent deux articles différents, sans lecture pour trancher.

## [1.4.0] — 2026-11-01

Cycle XVe : la législature 2017-2022 entre sur le site d'un seul déploiement, données et
qualifications : sécurité globale, séparatisme, anti-casseurs, crise sanitaire. 199 textes
qualifiés au total, dont 70 de la XVe, et 620 écartés. Le Sénat de 2017-2022 reste à part.

### Ajouté

- **Données** : 4 417 scrutins et 472 631 votes nominatifs de la XVe, 413 textes au catalogue,
  dossiers de la XIVe votés en XVe, rattachements figés, lignées de groupes. Amendements : le
  dump plafonne à 11 Ko/s, 3 071 amendements viennent du plan B et d'une copie dans la release
  `donnees-figees`.
- **Qualifications** : 70 textes en six lots thématiques, 33 amendements clés, 199 textes de la
  XVe écartés au tri, dont les lois de finances sans source. Positions de groupe contrôlées
  contre datan.fr : aucun écart réel.
- **Méthode** : échéance d'un régime restrictif et droit lu à la seule date du vote (règle 4), lois
  de finances (règle 8), lois successives d'une même crise (règle 18), détail par législature
  (règle 19).
- **Site** : vues par législature, score par législature sur la fiche député·e à partir de deux
  législatures, `scores_deputes_legislatures.csv`, périmètre et limites sur la page Méthodologie.

### Modifié

- `lvnd download` : sous 20 Ko/s pendant la patience, une source avec plan B y bascule.
- Rendu des cartes PNG dans un fil recyclé : resvg retenait environ 5 Mo de mémoire native par
  carte, jusqu'à faire tuer le build de Cloudflare. Pic de 13,9 Go à 2,6 Go, mêmes images.
- 4 dossiers d'engagement de responsabilité écartés, dont 3 de la XVIIe.

### Corrigé

- Rattachement des motions de censure, qui dépendait de l'ordre du système de fichiers : une
  motion citée par un texte et par son engagement de responsabilité va à l'engagement, le texte
  qualifié continuant de l'afficher. Vaut aussi pour les XVIe et XVIIe.
- Un amendement contredit par le référentiel ou par un titre nettement plus proche est refusé, car
  il vient d'un autre texte portant le même numéro : 6 scrutins de la XVe et 2 de la XVIIe (V4239,
  V5726) changent de dossier.

### Limites connues

- 55 scrutins sur amendement de la XVe sur 3 124 n'ont pas d'amendement (98,2 % de rattachés,
  seuil de `lvnd check` à 98 %). V446 et V2886 restent retenus d'après le titre et le PDF ou le
  compte rendu, sans dispositif contrôlable.
- Passe quotidienne pas encore observée avec la XVe, à vérifier le 02/11/2026.
- Vues par législature et fiche député·e pas encore relues avec les qualifications de la XVe.
- Quelques scrutins de la XVe restent mal rattachés, sans effet sur décisif ni scores (`BACKLOG.md`).

## [1.3.0] — 2026-10-31

Cycle Sénat : le second vote de chaque texte. Le site montre comment les groupes du
Sénat ont voté sur les textes qualifiés, ajoute ce que le Sénat vote seul, et chacun·e
retrouve ses sénateur·ices. Aucun score ne mélange les deux chambres : `scores_*.csv` et
`participation.csv` de l'AN sont identiques à l'octet. 132 textes qualifiés, 417 écartés.

### Ajouté

- **Données** : 1 336 scrutins publics du Sénat et 464 719 votes nominatifs depuis juin
  2022, sénateur·ices et groupes datés, à part dans `data/export/senat/`, avec un code postal
  → département dans `data/annuaire/`. Contrôles de `lvnd check`, passe quotidienne et son
  garde-fou.
- **Méthode** : règles 23 à 28 (décisif du Sénat, lecture sur le texte voté, texte du seul
  Sénat, scores, vote de groupe, deux chambres séparées), publiées sur la page Méthodologie.
- **Qualifications** : 95 votes du Sénat lus sur les textes qualifiés, dont 76 décisifs comptés
  et 19 affichés. 28 textes votés au seul Sénat, casseurs-payeurs compris, dont 21 comptés
  et 7 affichés sans jugement. 49 textes écartés au tri. 37 textes publiés n'ont aucun bloc Sénat, ni
  scrutin public sur l'ensemble ni motion.
- **Scores du Sénat** : décisif seul, une seule période depuis le 28/06/2022, fichiers à part.
- **Site** : section « Au Sénat » sur chaque fiche texte, `/senat` (les groupes d'abord,
  droit par droit, le vote de groupe expliqué, recherche par code postal), `/senat/<slug>`
  (score « d'après les votes enregistrés à son nom », écarts au groupe, « Lui écrire », aucun
  taux de participation), filtre de chambre sur `/textes`, dernier vote du Sénat sur `/en-cours`,
  lien depuis la fiche député·e, sénateur·ices dans la recherche par nom.
- **Admin** : scrutins et décisif du Sénat sur la fiche, contrôles identiques à `lvnd check`
  (test croisé à l'octet), aperçu des scores, textes sans vote à l'AN, alertes
  `senat_premier_vote` et `senat_vote_posterieur` dans « À traiter ». Migration `0004_senat.sql`.

### Modifié

- Le catalogue s'étend aux dossiers votés au Sénat sur l'ensemble, même sans scrutin à l'AN.
- Le contenu de l'accueil ne change pas. Le menu gagne une entrée « Sénat », le pied de page cite
  l'open data du Sénat, et la recherche par nom y trouve aussi les sénateur·ices.

### Limites connues

- Le score individuel d'un·e sénateur·ice dit peu de choses : presque tous les votes suivent le groupe,
  et ils ne disent pas qui était présent (règle 27).
- Passe quotidienne pas encore observée avec ces données, à vérifier le 01/11/2026.
- Comparer ne couvre pas le Sénat. Pas d'amendements clés du Sénat, ni de cartes partageables
  des sénateur·ices.
- Dans l'admin, les droits d'une version « autre » du Sénat se saisissent en JSON.
- La fiche de suivi des ingérences étrangères (340-0) attend l'inscription à l'AN : son alerte
  reste ouverte.

## [1.2.0] — 2026-10-30

Cycle Stock des lois de finances : les six lois de finances adoptées par 49.3
sans vote final figurent sur le site, avec leurs motions de censure. Elles ne
comptent dans aucun score (règle 9) : `scores_*.csv` et `participation.csv` sont
identiques à l'octet avec ou sans elles. 104 textes qualifiés, 368 écartés.

### Ajouté

- **Six qualifications** : PLF 2023, 2024 et 2025, PLFSS 2023, 2024 et 2025, avec
  leurs 29 motions de censure, attribuées une à une d'après la page du dossier de
  l'AN et le compte rendu de la séance du vote. V2610 et V2989 portent sur la
  programmation des finances publiques : non retenues.
- **Deux textes au fil de l'eau** : corps de fonctionnaires pour les AESH et parcours
  de soins des victimes de violences sexuelles, votés le 29/10/2026, comptés dans
  les scores.
- **Méthode** : la formation professionnelle dans `travail-protection-sociale`
  (règle 2) ; la CIIVISE et les unions confédérales de retraités parmi les sources
  (règle 7).

### Modifié

- Cinq dossiers d'engagement de responsabilité écartés : leurs motions s'affichent
  avec le texte qualifié (PLFSS 2025 et PLF 2026).

### Limites connues

- Sources rares pour 2022-2023. Le PLF 2024 repose sur une seule source admise, un
  avis de la CNIL postérieur au vote et portant sur le décret d'application. Le
  PLFSS 2023 repose surtout sur des sources qui portent sur le projet. Le PLF 2025
  repose sur une seule mesure et sur des sources syndicales.
- Des mesures restent hors jugement faute de source admise trouvée (AAH à Mayotte,
  crédits de l'AME).
- Lois promulguées non lues sur Légifrance (accès refusé) : les articles viennent des
  textes adoptés par l'AN, comparés aux décisions du Conseil constitutionnel.

## [1.1.0] — 2026-10-30

Cycles Reliquat XVIe et Au fil des votes : les amendements de la XVIe sont
là, les données se mettent à jour chaque jour, et le site montre où en est
chaque texte, avant et après le vote. Scores inchangés (96 textes qualifiés).

### Ajouté

- **Amendements de la XVIe** : `lvnd download` essaie le dump de l'AN (20
  minutes sans octet, il abandonne), puis une archive antérieure, puis une copie
  figée dans la release `donnees-figees`, puis un plan B qui lit chaque
  amendement voté sur le site de l'AN. 3 159 scrutins sur amendement rattachés
  sur 3 173 (99,6 %). Le dump revenu remplace le tout (`docs/SOURCES.md`).
- **État de chaque texte** : source `senat_dosleg` (décisions du Sénat, pas de
  votes de sénateur·ices), parcours, agenda de l'AN (« inscrit », jamais « sera
  voté »), catalogue élargi aux textes en cours ou inscrits sans scrutin public
  à l'AN (559 textes). Exports `en_cours*.csv`, sans effet sur les scores.
- **Alertes** dans `lvnd check` et la file « À traiter » de l'admin : vote
  postérieur au décisif, unanimité contestée, premier décisif, texte inscrit.
- **Mise à jour quotidienne** : Action `donnees-quotidien.yml` (dossiers et scrutins
  de la XVIIe, agenda, Dosleg ; les gros dumps viennent du cache ou de la release).
  Elle ne commite rien si un score change sans qualification nouvelle ou si
  `amendements.csv` perd des lignes. L'Action hebdomadaire est réparée.
- **Site** : page `/en-cours` rangée par échéance, état sur les fiches et dans
  les listes, mention « vote de 1re lecture, texte encore en navette »,
  « Prochains votes » sur la fiche député·e, flux RSS et iCal statiques.
- **Fiches de suivi** : statut `a-suivre` dans l'admin et liste `suivis` de
  `editorial.json` : droits touchés et sources, sans sens, score ni scrutin.
  Deux fiches publiées (relance du logement, régularisation des travailleurs
  sans-papiers).
- **Méthode** : règles 20 à 22 (état d'un texte, texte qualifié en navette, fiche
  de suivi) et compléments à la règle 9, validés par Max. Circuit « au fil de
  l'eau » dans `docs/QUALIFICATION.md`.

### Modifié

- 363 textes écartés (6 de plus, tri de la file) ; titres débarrassés des
  mentions « (non promulgué) » et « (rejetée) », que l'état remplace.

### Corrigé

- Une publication faite avant la validation d'une requalification laisse la
  version publiée sur le site. `sync-admin --brouillons` ajoute une révision à
  un texte qui en a déjà une.

### Limites connues

- Tant que le dump de la XVIe reste injoignable, `amendements.csv` n'a pour cette
  législature que les amendements mis aux voix, sans leurs identiques ni les
  amendements non votés. 14 scrutins restent sans amendement. Sur la XVIe, l'article
  lu diffère dans 9 cas sur 2 712 (0,33 %) de celui de l'intitulé.
- L'Action hebdomadaire retente ce dump avant de prendre la release : 32 minutes de
  plus le 30/10/2026.
- `lvnd check` retire du taux de la XVIe ses derniers scrutins (3 041 sur 3 053
  affichés), par un délai de 14 jours pensé pour une législature en cours.
- Le suivi au fil des votes continue en fonctionnement courant (`BACKLOG.md`).
- Le Sénat (votes) et la XVe législature ne sont pas couverts ; les lois de finances
  2023 à 2025 ne sont pas encore qualifiées.

## [1.0.0] — 2026-10-29

Première version publique, en ligne sur
[lvnd.technoperchoir.fr](https://lvnd.technoperchoir.fr). Assemblée
nationale, XVIe et XVIIe législatures (depuis juin 2022).

### Ajouté

- **Pipeline `lvnd`** (Python 3.12, uv, polars) : `download` → `build` →
  `check`, à partir de l'open data de l'AN seul. 1,97 M votes nominatifs
  versionnés en CSV mensuels (`data/export/votes/`), correction des
  ventilations `PO0`, lignées de groupes, rattachement des scrutins aux
  dossiers (99,9 % en XVIIe) et aux amendements, catalogue des candidats
  par mots-clés (aide au tri, jamais de qualification automatique).
- **Méthode** (`docs/METHODO.md`, page Méthodologie) : grille v1 de douze
  droits et deux étiquettes, dix-neuf règles fixes validées une à une
  (qualification, scrutins retenus, position de groupe, calcul des
  scores). Abstentions et absences hors calcul, chaque texte pèse 1,
  texte adopté par 49.3 qualifié sans être compté.
- **Qualifications** : 96 textes qualifiés et sourcés (six textes témoins
  et six lots), 357 textes examinés puis écartés avec leur motif.
  Préparées avec un assistant IA, validées par une personne (dit sur le
  site).
- **Scores** (`lvnd scores`) : par député·e, par groupe, par droit et par
  texte, avec participation et cohésion ; recalculés en ≈ 1 s depuis
  `data/export/` et `data/editorial.json`.
- **Annuaire** (`lvnd annuaire`) : code postal → circonscription
  (6 326 codes, La Poste × résultats des législatives 2024) et courriels
  des député·es.
- **Admin** (`admin/`, SvelteKit + D1 derrière Cloudflare Access) :
  saisie des qualifications, contrôles identiques à `lvnd check`, garde-fou
  sur les sources, diff publié/brouillon, bouton « Publier » qui commite
  `data/editorial.json` via l'API GitHub. `lvnd sync-admin` pousse le
  catalogue dans D1.
- **Site public** (`site/`, SvelteKit adapter-static + d3) : accueil et
  recherche par code postal ou par nom, pages par droit, textes et fiches
  texte, fiches député·e (« Lui écrire » par courriel), circonscriptions,
  groupes, Comparer, méthodologie, données téléchargeables, cartes PNG
  partageables. Contestation d'une qualification par courriel. Aucun
  traceur, aucun CDN tiers.
- **Déploiement** : `build.sh` (aucun téléchargement), Cloudflare Pages
  sur `main` (chaque publication de l'admin redéploie le site), CI des
  tests, Action hebdomadaire de mise à jour des données.

### Déroulé

Quatre étapes et six lots de qualification, du 29/10/2026. Chaque règle
de méthode a été validée par Max (`docs/METHODO.md` date chacune).

- **Étape 0, cadrage** : dépôt public, admin tout Cloudflare (D1 et
  Access, publication par commit), périmètre AN XVIe-XVIIe.
- **Étape 1, spike** : verdict GO, l'open data de l'AN suffit
  (`docs/SOURCES.md`). Ventilations identiques à celles de leurs-votes.fr
  (22 531 paires scrutin × groupe), concordantes avec datan.fr sur un
  échantillon. Pas de table officielle code postal → circonscription :
  71 % des électeurs ont un député unique par code postal. PISTE écarté
  (Conseil constitutionnel et JO viennent des dossiers AN). Grille v0,
  règles 1 à 13, six textes témoins.
- **Étape 2, pipeline et méthode** : `lvnd build` (≈ 25 s) et
  `lvnd check`, rattachement scrutin → dossier à 99,9 % en XVIIe (votes de
  CMP de la XVIe compris), catalogue de 479 textes. Règles de calcul 14 à
  19, amendements clés du narcotrafic, de la justice des mineurs et de
  Kasbarian-Bergé. Reste le dump des amendements de la XVIe (limites
  ci-dessous).
- **Étape 3, admin** : `lvnd-admin.technoperchoir.fr`, choix A à F
  (`docs/CONCEPTION.md`), tests croisés pipeline/admin (sérialisation à
  l'octet près, scores, arrondi).
- **Étape 4, site** : choix G à K (transparence sur l'IA, seuil
  d'ouverture, score toujours affiché avec son nombre de textes,
  participation, domaine), recette sur téléphone, grille v1
  (`citoyennete`), règle du 49.3, écriture inclusive.
- **Qualification** (`docs/QUALIFICATION.md` : Claude prépare, Max
  arbitre et publie) : lot 1 (19 qualifiés), deux tris des candidats
  (144 puis 176 écartés, dont les motions de censure spontanées), lots 2 à
  6 (17, 15, 14, 16 et 10 validés). Le vivier de la v1 est épuisé.

### Limites connues

- **Étape 2 encore ouverte** : le dump des amendements de la XVIe
  (`an_amendements_16`) n'a pas pu être téléchargé, le serveur de l'AN
  coupant les transferts. Le rattachement des scrutins sur amendement de
  la XVIe n'est donc pas mesuré (`docs/SOURCES.md`). Les scrutins et votes
  de la XVIe sont complets ; ses scrutins sur amendement sont rattachés à
  leur dossier par la séance, sans l'amendement ni son auteur.
- Le Sénat et la XVe législature ne sont pas couverts.
- Les lois de finances adoptées par 49.3 sans vote final (PLF et PLFSS
  2023 à 2025) ne sont pas encore qualifiées.
- Les textes de la liste C attendent un vote final pour être qualifiés
  (`BACKLOG.md`).
