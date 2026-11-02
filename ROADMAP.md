# Roadmap

Projet sans calendrier engageant. Ce fichier est le **plan opérationnel** :
il porte le cycle en cours, et seulement lui. Ce qui est livré est dans
`CHANGELOG.md`, les cycles à venir et les idées dans `BACKLOG.md`. Règles
de tenue : `CLAUDE.md`, section « Suivi ».

## Cycle en cours : Suites de l'audit

Ouvert le 02/11/2026. **But** : solder ce que l'audit de cohérence du 01/11/2026 et le chargement du 02/11/2026 ont laissé
de côté, et combler deux manques de l'outil apparus en route. Pas de nouvelle fonction publique.

### Items

1. **Alerte « vote final sans scrutin public »** (`pipeline/lvnd/alertes.py`). Un texte qualifié ou écarté dont l'Assemblée
   ou le Sénat adopte définitivement le texte à main levée, après le décisif, ne déclenche rien : `vote_posterieur` ne voit
   que les scrutins publics, `vote_sans_decisif` que les textes ni qualifiés ni écartés. Cas en vue : audiovisuel public
   (DLR5L16N47697).
2. **Note interne par texte dans l'admin.** D1 seule, jamais publiée ni exportée ; saisie sur la fiche, affichée dans
   « À traiter ». Migration D1 (`admin/migrations/0005_…`) : `npm run db:migrer:distant` puis `npm run deploy`, à lancer par
   Max, avant le sync suivant.
3. **Résumés des six fiches témoins** (immigration, JO, Kasbarian-Bergé, narcotrafic, justice des mineurs, aide à mourir),
   réécrits sur le texte voté, sources lues. Circuit éditorial : brouillon, « à relire », ok de Max, « Publier ».
4. **Reliquat de fond de l'audit** (`source/relecture-audit-forme.md`, « Laissés de côté ») : retraite universelle
   (article 8), PLFSS 2026 (articles 26 et 26 bis), urgence agricole (article 5), motif d'`asap-2020`, cinq motifs d'écart
   (48392, 37436, 48739, 40764, 47215), `regime-exception` sur le titre de séjour expérimental d'`immigration-2024`. Même
   circuit.
5. **Questions de règle** : chacune avec une recommandation, dans `docs/A_VALIDER.md` ; ce que Max tranche passe dans
   `docs/METHODO.md` et, s'il y a lieu, dans les fiches.
6. **Sources non relues faute d'accès** (Générations Futures sur les plastiques dangereux, CFDT sur le PLFSS 2026,
   loi n° 2026-651 au JO) : lecture dans un navigateur, par Max.

### Fait dans ce cycle

- Item 1 : alerte `lecture_posterieure` (lecture de l'AN close après le décisif sans vote public sur l'ensemble) ;
  `vote_posterieur` couvre aussi les textes qualifiés sans décisif à l'AN (audiovisuel public). Deux alertes à la mise en
  service, `a69-riipm-2025` et `travail-1er-mai-ppl-2025` (motions de rejet « tactiques »), brouillons prêts.
- Item 2 : note interne (migration `0005_notes_internes.sql`), sur la fiche et dans « À traiter ». **À faire par Max** :
  `npm run db:migrer:distant`, puis `npm run deploy`.
- Items 3 et 4 : 18 brouillons chargés « à relire » dans l'admin le 02/11/2026 (six résumés de témoins, cinq fiches de fond,
  cinq écarts dont deux deviennent qualifiés, les deux fiches de l'alerte). En attente de l'ok de Max.
- Item 5 : dix questions dans `docs/A_VALIDER.md`, chacune avec une recommandation. En attente de Max.
- Item 6 : les trois sources, lues par Max dans un navigateur, confirment les fiches publiées. Rien à changer.
