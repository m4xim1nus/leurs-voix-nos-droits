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
- [creuser] Cas « instrumentalise le sujet » (vote favorable mais texte de façade) : prévu dans le code de leurs-votes.fr, jamais utilisé ; utile pour nous ? (claude, 2026-10-29)
- [creuser] Aide à la qualification par LLM (suggestion de droits et de sens, toujours validée à la main) en plus des mots-clés (claude, 2026-10-29)
- [ ] Afficher les décisions du Conseil constitutionnel (censures totales ou partielles) sur la fiche texte : source PISTE ou open data CONSTIT (claude, 2026-10-29)
- [ ] Mise à jour automatique des données (pipeline en GitHub Action planifiée, puis `sync-admin`) (claude, 2026-10-29)
- [ ] Formulaire de contestation d'une qualification, sans service tiers (leurs-votes.fr passe par Tally) (claude, 2026-10-29)
- [ ] Comparateur de deux groupes sur un droit (« là où ils s'opposent ») (claude, 2026-10-29)
- [ ] Eurodéputés (HowTheyVote.eu) : hors périmètre national, à garder en tête (claude, 2026-10-29)
- [→Étape 2] Table pays → circonscription des Français de l'étranger (code électoral, art. L. 330-1) à saisir en référentiel (claude, 2026-10-29)
- [→Étape 4] État « siège vacant » sur la fiche circonscription (3 sièges sans mandat en cours au 28/10/2026) (claude, 2026-10-29)
- [creuser] Recherche par code postal, communes coupées (14 % des électeurs) : A afficher les N députés possibles, B choisir la commune déléguée ou l'arrondissement, C saisir son adresse (table d'adresses Insee en statique, 490 Mo brut) ; cf. `docs/SOURCES.md` (claude, 2026-10-29)
- [creuser] Texte adopté au 49.3 sans vote final à l'AN : quel scrutin décisif (motion de censure miroir, comme quifaitlaloi, ou dernier vote sur l'ensemble d'une lecture antérieure) ? La règle 9 ne couvre pas ce cas (claude, 2026-10-29)
- [ ] Relire `mots_cles.yaml` (brouillon) : motifs larges, sources de faux positifs (« eau », « soins », « violences », « justice ») (claude, 2026-10-29)
- [→Étape 4] Taux de participation aux scrutins comptés sur la fiche député (règle 17), depuis les votes et les mandats (claude, 2026-10-29)
- [ ] `data/lvnd.sqlite` pèse 193 Mo (votes en identifiants texte) : identifiants entiers si la taille gêne (claude, 2026-10-29)
- [→Étape 4] `lvnd scores` : scores recalculés depuis `data/export/` et `editorial.json`, sans dump (choix F de `docs/CONCEPTION.md`) (claude, 2026-10-29)
- [ ] Admin : afficher le diff entre la version publiée et le brouillon d'un texte (les révisions sont déjà gardées) (claude, 2026-10-29)
- [ ] Admin : alerte quand `sync-admin` fait disparaître un scrutin retenu dans une qualification (scrutin renuméroté ou rattaché ailleurs) (claude, 2026-10-29)
- [ ] Rôles d'édition dans l'admin (rédacteur, valideur) : à la passation, quand il y aura plusieurs personnes (claude, 2026-10-29)
- [ ] Mettre à jour `docs/SOURCES.md` : le serveur de l'AN sert les plages par intermittence ; `download` reprend désormais d'un lancement à l'autre (claude, 2026-10-29)
