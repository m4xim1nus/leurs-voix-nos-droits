# Qualifier un texte dans l'admin

Pour les rédacteur·ices. Aucune installation : un navigateur et une adresse courriel suffisent. Les règles de fond sont dans la
[méthodologie](METHODO.md) : ce guide dit où cliquer, pas comment juger.

**L'essentiel** : ce que vous enregistrez reste un brouillon privé. Rien n'apparaît sur le site public avant un clic sur « Publier », et chaque
publication reste dans l'historique du dépôt. Vous pouvez essayer sans risque, tant que vous ne publiez pas.

## 1. Se connecter

1. Ouvrez <https://lvnd-admin.technoperchoir.fr>.
2. Saisissez votre adresse courriel. Elle doit figurer sur la liste d'accès : sinon, demandez qu'on vous ajoute (Cloudflare Zero Trust, Access, politique de l'application).
3. Recopiez le code reçu par courriel. Il n'y a pas de mot de passe.

Votre adresse s'affiche en haut de la page, à côté de la date des données. Elle signe chacun de vos enregistrements.

## 2. Se repérer

| Onglet | À quoi il sert |
|---|---|
| **Textes** | tout le catalogue, avec des filtres : législature, nature, droit candidat, statut. Par défaut : lois ordinaires présélectionnées par mots-clés, avec un scrutin |
| **À traiter** | ce qu'un nouveau vote ou une inscription demande de regarder. Le plus souvent, c'est par là qu'on commence |
| **Aperçu des scores** | les scores des groupes avec les textes validés, publiés ou non ; un lien y ajoute brouillons et textes à relire |
| **Publier** | ce qui va changer sur le site, et le bouton |
| **Journal** | qui a modifié quoi, et quand |

## 3. Les statuts

| Statut | Sens | Sur le site ? |
|---|---|---|
| brouillon | en cours d'écriture | non |
| à relire | prêt pour une relecture | non |
| validé | relu, tous les contrôles passent | à la prochaine publication |
| écarté | non qualifié, avec un motif public | à la prochaine publication, dans la liste des écartés |
| à suivre | fiche avant le vote : droits et sources, sans sens ni scrutin (règle 22) | à la prochaine publication |

Un texte déjà publié qu'on repasse en brouillon **garde sa version publiée** en ligne jusqu'à sa validation. Pour le retirer du site, il faut l'écarter.

## 4. Qualifier un texte

Ouvrez le texte depuis « Textes » ou « À traiter ». En haut : le dossier de l'Assemblée, la loi sur Légifrance, la décision du Conseil constitutionnel. Lisez-les d'abord. Les
modifications restent locales jusqu'au bouton « Enregistrer », en bas de page.

1. **Identifiant public** : minuscules, chiffres et tirets (`sren-2024`). Il forme l'adresse de la fiche : ne le changez plus après publication.
2. **Titre et résumé** : une ou deux phrases factuelles sur ce que fait le texte.
3. **Sources**, d'abord, car les droits les citent. « + source » : une clé courte (`cnil-2023-05`), l'auteur, le titre, la date (`AAAA-MM-JJ`), l'adresse. Une source déjà utilisée ailleurs se reprend avec « reprendre une source d'un autre texte ». Seules les sources de la règle 7 sont admises.
4. **Droits touchés**, « + droit » : le droit, son rôle (un seul principal), son sens (étend ou restreint, du point de vue des personnes, règle 1), ses sources cochées, une justification courte. Renommer une clé de source met à jour ses citations.
5. **Étiquettes** : `outre-mer`, `regime-exception`, selon leur définition dans la méthodologie.
6. **Points de vigilance** : les critiques sourcées, qui s'affichent à côté du jugement sans le modifier (règle 5). Un texte qui étend un droit contesté en demande au moins une (règle 7).
7. **Conseil constitutionnel et note** : la décision résumée, et la note publique qui explique les choix de scrutins.
8. **Scrutins** : « Retenir le décisif proposé » s'il convient (règle 9). Le menu de chaque ligne retient un scrutin dans son rôle : décisif, autre lecture, motion, amendement clé. Le filtre « amendements et articles » affiche le reste. Pour un amendement clé, **fixez le sens à la main** : il arrive « à trancher » et n'est pas compté tant qu'il le reste (règle 11).
9. **Vote du Sénat**, s'il y a lieu (règles 23 à 28). Indiquez sur quoi porte le vote :
   - *même texte que le décisif de l'Assemblée* : le sens est repris, il suffit de retenir le scrutin ;
   - *autre version* : les mêmes formulaires apparaissent (droits, étiquettes, sources, vigilance), propres à la version votée au Sénat. Sans source admise sur cette version, retenez le scrutin comme « ensemble », sans droits : il est affiché et non compté ;
   - *pas de décisif à l'Assemblée* : les droits du haut de la fiche valent pour le Sénat.
10. **Aperçu du score** : les tableaux montrent ce que ce texte donne pour chaque groupe. Si un résultat surprend, relisez le sens du droit principal et celui des scrutins.
11. **Enregistrer** : choisissez le statut, écrivez au besoin un commentaire de révision (privé), puis enregistrez.

Pour **écarter** un texte, choisissez le statut « écarté » et écrivez son motif, public, qui cite la règle en cause.

## 5. Les contrôles

Ils s'affichent en bas de page, pendant la saisie.

- **Erreurs** (rouge) : elles empêchent de valider, pas d'enregistrer un brouillon. Par exemple : pas de droit principal, clé de source inconnue, décompte du scrutin faux.
- **Avertissements** : à lire, ils n'empêchent rien. Par exemple : sens d'amendement à trancher, vigilance manquante.
- **Sources exclues** : une liste privée de termes fait refuser une qualification au moment de publier. Si cela vous arrive, cherchez une autre source. Le message vous dira où est le terme.

Si quelqu'un a enregistré le même texte pendant que vous le modifiiez, l'admin refuse votre enregistrement : copiez vos ajouts, rechargez, reprenez. L'historique en bas de fiche permet de **recharger une ancienne version**.

## 6. Publier

1. Ouvrez « Publier » : relisez la liste des changements. Chaque ligne est un texte nouveau ou modifié.
2. Si le bouton est grisé, un texte validé a une erreur : la page le dit.
3. Cliquez sur « Publier ». L'admin crée un commit dans le dépôt, à votre nom, et affiche son lien. Le site se reconstruit en quelques minutes.

## 7. Traiter une alerte

| Alerte | Ce qu'elle demande |
|---|---|
| Vote sur l'ensemble après le décisif | le nouveau vote devient le décisif (règle 9) : relire le sens sur le texte voté |
| Écarté pour unanimité, vote contesté | qualifier, ou garder l'écart avec un motif à jour |
| Texte écarté, revoté à l'Assemblée | qualifier, ou garder l'écart avec un motif qui cite ce vote (décompte, ou date sans scrutin public) |
| Décisif d'un texte non traité | qualifier, ou écarter avec son motif |
| Lecture close sans décisif proposé | lire le dossier, puis qualifier ou écarter |
| Texte non traité, inscrit en séance | rien à qualifier : le vote n'a pas eu lieu. Repérer les sources utiles, ou rédiger une fiche « à suivre » |
| Vote du Sénat sur l'ensemble, à lire ; nouveau vote du Sénat | remplir ou mettre à jour le bloc « Vote du Sénat » |

## Premier essai conseillé

Prenez un texte déjà publié, simple, et comparez sa fiche à sa page sur le site public : chaque champ de l'admin y a sa place. Puis, sur un texte non traité : brouillon, deux sources, un droit, le décisif. Regardez les contrôles et l'aperçu. Repassez-le sans publier, ou laissez-le en « à relire » pour qu'on le relise avec vous.
