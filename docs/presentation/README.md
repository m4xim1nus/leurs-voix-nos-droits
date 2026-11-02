# Présentation du projet

Le projet, ses objectifs, sa méthode et son fonctionnement, en 19 slides avec notes de l'orateur. Ni le site public ni l'admin ne servent ces fichiers.

- `leurs-voix-nos-droits.bento.html` : la source. Elle s'ouvre dans un navigateur, sans rien installer, pour présenter (`F5`) ou modifier. Fait avec [Bento](https://bento.page) (MIT), dont l'application est incluse dans le fichier.
- `leurs-voix-nos-droits.pdf` : la version à partager, imprimée par Chromium : son texte se sélectionne et se cherche.

**Modifier** : à la souris dans le fichier, ou en demandant à un LLM de réécrire le bloc JSON `#bento-doc` (guide : <https://bento.page/agents.md>). Les chiffres (201 textes, 670 écartés, 20 224 scrutins) sont ceux du 01/11/2026 : à mettre à jour à la main.

**Refaire le PDF**, après chaque modification du deck, depuis la racine du dépôt :

```bash
uv run --with playwright playwright install chromium   # la première fois seulement
uv run --with playwright python -I docs/presentation/imprimer.py
```

Le script déclenche l'export PDF de l'application et fait imprimer la page par Chromium. Des captures d'écran des slides donneraient un texte non sélectionnable. Avant de refaire le PDF, relire les chiffres et les horaires des slides : ils ne se mettent pas à jour seuls.
