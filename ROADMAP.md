# Roadmap

Projet sans calendrier engageant. Ce fichier est le **plan opérationnel** :
il porte le cycle en cours, et seulement lui. Ce qui est livré est dans
`CHANGELOG.md`, les cycles à venir et les idées dans `BACKLOG.md`. Règles
de tenue : `CLAUDE.md`, section « Suivi ».

## Cycle en cours : Reliquat XVIe

But : finir l'étape 2 de la v1, c'est-à-dire avoir les amendements de la
XVIe et mesurer leur rattachement comme pour la XVIIe. Items `[→Reliquat
XVIe]` de `BACKLOG.md`.

Déjà fait dans ce cycle : `lvnd download` garde chaque octet reçu,
demande des plages de 256 Kio et reprend un fichier partiel d'un lancement
à l'autre.

1. ⏳ **Dump `an_amendements_16`** (363 Mo, figé le 28/06/2024). Bloqué à
   94,1 Mo : depuis le 29/10/2026 vers 18 h, le serveur de l'AN ne sert
   plus aucune plage au-delà d'environ 1 Mo. Relance :
   `cd pipeline && uv run lvnd download an_amendements_16 >> ../data/raw/download_16.log 2>&1`.
   Le dump est complet quand `an_amendements_16` figure dans
   `data/raw/manifeste.json`.
2. ⏳ Puis `lvnd build` et `lvnd check` (aujourd'hui en échec sur cette
   seule ligne), et mesure du rattachement des scrutins sur amendement de
   la XVIe dans `docs/SOURCES.md`, avec la note sur le service par
   intermittence du serveur.
3. ⏳ **Action hebdomadaire « Données AN »** (`.github/workflows/donnees.yml`) :
   son seul lancement (29/10/2026, manuel) a échoué au téléchargement, pour
   la même raison. Tant qu'elle échoue, elle ne met à jour ni les données
   ni l'admin. Prochain lancement : lundi, 4 h UTC.
4. ⏳ Relecture des scores des six textes témoins avec Max (livrable de
   l'étape 2).

## Cycle en parallèle : Au fil des votes

Ouvert le 30/10/2026 par Max, pendant que le Reliquat XVIe se termine dans
une autre copie de travail. Il réunit les anciens candidats « Textes en
cours » et « Qualification continue ». Items `[→Au fil des votes]` de
`BACKLOG.md`.

But : savoir où en est chaque texte, tenir les qualifications à jour vote
après vote, et montrer les votes à venir avec des faits, pour que chacun
puisse interpeller à temps. La promesse du site : voir qui vote quoi avant
et après, pas faire basculer un vote (au 29/10/2026, 1 décisif qualifié sur
94 se joue à 10 voix ou moins).

**Décisions de Max (30/10/2026)**

- Un seul cycle ; les lois de finances 2023 à 2025, simple stock à
  rattraper, en sortent.
- Avant le vote : droits touchés et sources publiques, **sans sens ni
  score**. Un texte déjà qualifié garde son sens, avec la mention « sur le
  texte voté le… ».
- `/en-cours` n'affiche que des textes retenus à la main (statut
  `a-suivre`) et les textes qualifiés en navette. Les mots-clés ne font que
  présélectionner.
- Un texte qualifié encore en navette reste dans les scores (règle 9), avec
  la mention « vote de 1re lecture, texte encore en navette ».

**Échéances**

- **18/11/2026** : 2e lecture des rapports locatifs, texte qualifié inscrit
  les 18 et 19/11. Les items 1 à 5, 7, 8 et 9 doivent tourner avant cette
  date.
- **Mi-décembre** : le front et le lot test, pour qu'ils servent encore
  plus de deux mois.
- **28/02/2027** : fin de la session, avant la présidentielle.

**Dépendance** : l'autre copie de travail modifie `sources.py`, `build.py`,
`cli.py`, `amendements.py` et `donnees.yml`. On attend qu'elle ait commité
pour y toucher.

### Socle de données

1. ✅ **Dosleg, décisions du Sénat seulement** : ajouter `senat_dosleg`
   (`https://data.senat.fr/data/dosleg/dosleg.zip`) à `sources.py`, et
   reprendre de `quifaitlaloi/pipeline/qfl/senat.py` les décisions de
   séance, les séances, l'activité et l'état des dossiers. Pas de vote de
   sénateur·ice : ils restent au cycle Sénat. Le dossier AN enregistre ces
   décisions avec retard (casseurs-payeurs, voté le 27/10/2026). Volume à
   relever dans `docs/SOURCES.md`.
2. ✅ **État de chaque texte** : `lvnd/encours.py`, adapté de
   `qfl/encours.py` (241 lignes) et de ce qu'il utilise de `parcours.py`
   (501 lignes). Même périmètre : voté au moins une fois en séance, ni
   promulgué ni adopté définitivement, écarté s'il est retiré, rejeté,
   caduc, fusionné ou sans acte depuis 12 mois. Exports à part
   (`en_cours*.csv`), sans effet sur les scores : `scores_*.csv` doivent
   rester identiques à l'octet. Il faut aussi un état pour **chaque** texte
   qualifié, y compris ceux de la XVIe (loi, en navette avec la chambre
   attendue, rejeté, à l'arrêt).
3. ✅ **Agenda de l'AN** : dump
   `17/vp/reunions/Agenda.json.zip` (8,5 Mo, quotidien), export des points
   de séance et de commission non supprimés et reliés à un dossier. Le mot
   est « inscrit », jamais « sera voté » : sept textes sont inscrits le seul
   19/11/2026, et une niche ne les examine pas toujours tous. Horizon
   constaté : environ 3 semaines.
4. ⏳ **Catalogue élargi** : `textes.csv` et D1 reçoivent aussi les textes
   en cours ou inscrits sans scrutin public à l'AN (66 des 126 textes en
   cours au 28/10/2026, dont casseurs-payeurs). Vérifier ce que cela change
   dans `lvnd check`, le filtre par défaut de l'admin, le site et le volume
   de `sync-admin`.
5. ⏳ **Alertes** (`lvnd check` et file « À traiter » de l'admin) : vote sur
   l'ensemble postérieur au décisif d'un texte qualifié ; texte écarté pour
   unanimité qui reçoit un vote contesté ; premier décisif d'un texte non
   traité ; texte non traité inscrit à l'ordre du jour. Ce sont des
   **avertissements** : un nouveau vote ne doit pas bloquer l'Action, qui ne
   commite que si `check` passe.
6. ⏳ **Mise à jour quotidienne** (dossiers, agenda, scrutins, Dosleg), une
   fois l'Action réparée (item 3 du Reliquat XVIe). `build` tourne sans le
   dump des amendements mais rattache alors moins bien les scrutins : la
   passe légère réutilise donc l'archive en cache et ne doit jamais dégrader
   `amendements.csv`. Elle ne commite que si un export a changé.

### Qualification au fil de l'eau

7. ⏳ **Circuit** : section « au fil de l'eau » dans `docs/QUALIFICATION.md`
   (un texte à la fois dès l'alerte, fiche courte, même validation par Max).
   Corriger ce qui gêne ce rythme : une publication faite avant la validation
   d'une requalification retire le texte du site, alors qu'elle doit y
   laisser la version publiée ; `sync-admin --brouillons` n'ajoute pas de
   révision à un texte qui en a déjà une.
8. ⏳ **Premiers textes**, à traiter selon leurs votes :
   - rapports locatifs (DLR5L17N53069, 18-19/11) : nouveau décisif, sens à
     relire (règle 6) ;
   - Territoires zéro chômeur (DLR5L17N51962, écarté à 96-0, 2e lecture le
     19/11) ;
   - PLF 2027 (vote solennel inscrit le 17/11), PLFSS 2027, abrogation des
     ZFE (DLR5L17N54557) ;
   - les textes du backlog : AGRASC, mariages simulés, concentration des
     médias, audiovisuel public.

### Front (des faits, aucun nouveau jugement)

9. ⏳ **État sur les fiches texte** et dans les listes ; mention « vote de
   1re lecture, texte encore en navette » à côté d'un vote compté ; retrait,
   par une publication de l'admin, des « (non promulgué) » saisis dans les
   titres.
10. ⏳ **Page `/en-cours`**, rangée par échéance (inscrit à une date, attendu
    à l'AN, au Sénat, en CMP, suite pas encore connue) : dernier vote de l'AN
    par groupe, mention « pas encore qualifié » s'il y a lieu. Navigation,
    encart d'accueil, section de la méthodologie, fichiers sur `/donnees`.
    Repères : `quifaitlaloi/docs/CONCEPTION.md` §19. Une page presque vide
    après le 28/02 doit le dire simplement (fin de session).
11. ⏳ **« Prochains votes » sur la fiche député** : textes retenus attendus
    à l'AN, son vote et celui de son groupe à la lecture précédente, courriel
    prérempli au ton factuel. Rien quand le texte est au Sénat.
12. ⏳ **Flux RSS et iCal statiques**, générés au build, sans donnée
    personnelle.

### Suivi avant le vote

13. ⏳ **Statut `a-suivre`** : migration D1, écran de l'admin, liste à part
    dans `editorial.json` (changement de format, test croisé
    pipeline/admin à l'octet). Contrôles : droits touchés sans sens, au moins
    une source par droit, aucun scrutin, termes interdits. Une validation par
    Max et le bouton « Publier », comme pour une qualification.
14. ⏳ **Méthodologie** : règles écrites dans `docs/METHODO.md` et sur le
    site (état d'un texte, fiche de suivi, texte qualifié en navette). **Leur
    rédaction est à valider par Max avant la mise en ligne.**
15. ⏳ **Lot test** de 3 à 5 textes inscrits, parmi : relance du logement
    (DLR5L17N54608, 17-20/11), régularisation des travailleurs sans-papiers
    (DLR5L17N54998, 19/11), ingérences étrangères (DLR5L17N54703) et
    casseurs-payeurs (DLR5L17N54925) dès leur inscription. Consigne aux agents
    dans `docs/QUALIFICATION.md`. Faute de source admise, la fiche le dit.
    Bilan avec Max : temps passé, part de textes sourcés à temps, et suite à
    donner.
