# Présentation du projet

`leurs-voix-nos-droits.pdf` : une page A4 paysage, à partager telle quelle. Ni le site public ni l'admin ne la servent. Le fichier source est `presentation.html`.

Après une modification ou pour remettre les chiffres à jour :

```bash
python3 docs/presentation/generer.py /chemin/vers/chrome   # écrit le PDF
```

Sans Chrome : `python3 docs/presentation/generer.py`, puis ouvrir `presentation-a-imprimer.html` dans un navigateur, Imprimer, Enregistrer en PDF, sans marges, avec les graphiques d'arrière-plan. Supprimer ensuite ce fichier intermédiaire.
