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

Prochain cycle : à choisir parmi les cycles candidats de `BACKLOG.md`.
