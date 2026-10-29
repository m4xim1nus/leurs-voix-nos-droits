# Backlog

File d'attente brute, non ordonnée. Une ligne par item :

```
- [TAG] description courte (origine, date)
```

**Tags** : `[ ]` à trier, `[→Étape N]` ou `[→Codename]` rangé, `[creuser]`
à réfléchir avant d'arbitrer, `[refusé]` tranché négatif (trace gardée).
**Origines** : `user:moi`, `claude`, `gh#N`.

---

## À trier

- [creuser] Le nom « Leurs voix, nos droits » fait écho à « Leurs votes » (Bon Pote) : filiation assumée ou risque de confusion, à trancher avant la passation ; recherche INPI non faite (claude, 2026-10-29)
- [creuser] Quiz « qui vote comme vous ? » sur de vrais scrutins, comme leurs-votes.fr (claude, 2026-10-29)
- [refusé] Cas « instrumentalise le sujet » (vote favorable mais texte de façade) : jugement au cas par cas, contraire à la règle fixe de la méthode (claude, 2026-10-29)
- [ ] Afficher les décisions du Conseil constitutionnel (censures totales ou partielles) sur la fiche texte : source PISTE ou open data CONSTIT (claude, 2026-10-29)
- [ ] Eurodéputés (HowTheyVote.eu) : hors périmètre national, à garder en tête (claude, 2026-10-29)
- [→Étape 2] Table pays → circonscription des Français de l'étranger (code électoral, art. L. 330-1) à saisir en référentiel (claude, 2026-10-29)
- [refusé] Recherche par code postal, communes coupées : l'option A (tous les députés possibles, avec leurs communes) reste. Choisir son adresse (C) demanderait un service tiers à l'exécution ou une table de 490 Mo (claude, 2026-10-29)
- [ ] Relire `mots_cles.yaml` (brouillon) : motifs larges, sources de faux positifs (« eau », « soins », « violences », « justice ») (claude, 2026-10-29)
- [ ] Candidat `etrangers` en attente d'un vote final : mariages simulés ou arrangés (DLR5L16N49075, examen inachevé le 25/06/2026, 35 amendements votés) (claude, 2026-10-29)
- [refusé] `data/lvnd.sqlite` en identifiants entiers : 193 Mo, local et non versionné, la taille ne gêne pas (claude, 2026-10-29)
- [ ] Rôles d'édition dans l'admin (rédacteur, valideur) : à la passation, quand il y aura plusieurs personnes (claude, 2026-10-29)
- [ ] Mettre à jour `docs/SOURCES.md` : le serveur de l'AN sert les plages par intermittence ; `download` reprend désormais d'un lancement à l'autre (claude, 2026-10-29)
- [ ] Catalogue : saisines du Conseil constitutionnel déclarées irrecevables absentes (ingérences étrangères : 2024-870 DC et 2024-871 DC, après la dissolution) ; vérifier aussi « Non conforme » affiché pour une non-conformité partielle (2026-911 DC) (claude, 2026-10-29)
- [refusé] `lvnd annuaire` : repli sur la table MI 2017 pour les 8 couples code postal × commune sans circonscription. Sans objet : six villages détruits de Verdun (sans habitant, leur code postal est résolu par les autres communes), Monaco et Clipperton (claude, 2026-10-29)
- [ ] Rattachement scrutin → dossier : V4239 (amendement du Gouvernement au PLF 2026, 21/11/2025) est rattaché à la simplification de l'urbanisme (DLR5L17N51852) (claude, 2026-10-29)
- [ ] `lvnd check` : alerte quand un texte qualifié reçoit un vote sur l'ensemble postérieur à son décisif (texte en navette, règle 9) (claude, 2026-10-29)
- [ ] Passation : revoir deux qualifications tranchées par défaut, où le choix du droit principal inverse les groupes favorables et défavorables : antisemitisme-enseignement-superieur (discriminations étend contre libertes restreint) et abrogation-obligation-vaccinale-2023 (travail-protection-sociale étend, retenu, contre sante restreint) (claude, 2026-10-29)
- [ ] Avant la passation, une fois tout qualifié : réécrire pour le public les notes de méthode et les motifs d'écart des qualifications, qui citent les règles par leur numéro (≈ 60 notes, ≈ 50 motifs). Le site les replie déjà sous « Comment ce texte a été qualifié », numéros liés à la méthodologie (user:moi, 2026-10-29)
- [ ] Passation : ajouter aux qualifications politiquement sensibles à revoir (avec antisemitisme-enseignement-superieur et abrogation-obligation-vaccinale-2023) energies-renouvelables-2023 et nucleaire-acceleration-2023, toutes deux `environnement` restreint par la règle 2 (choix d'énergie hors grille) : sur les renouvelables, RN, LR, LFI et GDR, qui ont voté contre, sont comptés favorables (user:moi, 2026-10-29)
- [ ] Catalogue : `cc_url` en 404 quand la décision est rendue l'année suivant la saisine (2022-846 DC, LOPMI : l'URL valide est `/decision/2023/2022846DC.htm`) (claude, 2026-10-29)
