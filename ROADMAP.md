# Roadmap

Projet sans calendrier engageant. Ce fichier est le **plan opérationnel** :
il porte le cycle en cours, et seulement lui. Ce qui est livré est dans
`CHANGELOG.md`, les cycles à venir et les idées dans `BACKLOG.md`. Règles
de tenue : `CLAUDE.md`, section « Suivi ».

## Cycle en cours : Finitions de la pré-qualification

Ouvert le 02/11/2026, mini-cycle visé en 1.10.1. **But** : traiter dès maintenant ce que le cycle Pré-qualification a laissé
« à trier » et qui n'attend rien. Pas de nouvelle fonction.

### Items

1. **Erreur 1102 de « Publier »** (limite de calcul du Worker gratuit, 02/11/2026, en publiant 300 textes) : ne plus
   recalculer à chaque chargement ce qui n'a pas changé depuis la dernière publication (empreintes, contrôles, termes
   interdits, fichier complet). Mesurer avant et après, sur la base locale.
2. **Capture d'« À traiter »** du guide `/aide` : refaite sur l'admin locale, quatre sections et propositions d'exemple.

### Fait dans ce cycle

- Item 1 : « Publier » ne contrôle plus que les textes changés depuis la dernière publication (règles, scrutins, termes
  interdits) ; une seule sérialisation et une seule empreinte par texte ; termes compilés une fois ; fichier complet
  construit à la demande ; plus de second calcul des empreintes ni de relecture du fichier pour compter. Sur la base
  locale alignée, préparation et fichier en 80 à 100 ms au lieu de 300 à 360 ms, accès à D1 compris. Les textes
  inchangés restent contrôlés chaque jour par `lvnd check`.
