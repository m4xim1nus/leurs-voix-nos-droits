# Roadmap

Projet sans calendrier engageant. Ce fichier est le **plan opérationnel** :
il porte le cycle en cours, et seulement lui. Ce qui est livré est dans
`CHANGELOG.md`, les cycles à venir et les idées dans `BACKLOG.md`. Règles
de tenue : `CLAUDE.md`, section « Suivi ».

## Cycle en cours : Facile à lire

Ouvert le 02/11/2026. **But** : chaque texte qualifié porte, en plus de son résumé, quelques phrases en mots simples, pour
qu'une personne qui lit difficilement le français, ou qui ne connaît rien au travail parlementaire, comprenne ce que fait
le texte. Ces phrases sont préparées par le LLM, hors ligne, et **toujours relues** avant publication.

**Garde-fous**, valables pour tout le cycle (ceux de la pré-qualification s'appliquent aussi) :

- le résumé simple **reformule**, il n'ajoute rien : aucun fait, aucun jugement, aucune source absents de la fiche
  (titre, résumé, droits et justifications, décision du Conseil constitutionnel). Il ne nomme ni élu·e ni groupe ;
- le LLM propose, un humain valide ; un résumé simple non validé n'est jamais publié ;
- un résumé simple validé reste lié à la fiche qu'il reformule : si le résumé ou les droits changent ensuite, il redevient
  « à revoir » et le site ne l'affiche plus tant qu'il n'est pas revu ;
- l'admin et le site restent entiers sans lui : une fiche sans résumé simple s'affiche comme aujourd'hui.

### Items

1. **Cadrage, à valider par Max** (`docs/A_VALIDER.md`) :
   - *nom affiché* : « facile à lire et à comprendre » (FALC) est une méthode européenne (Inclusion Europe) dont le logo
     suppose une relecture par des personnes concernées, que le projet n'a pas. Recommandation : un intitulé sans le
     sigle (« En mots simples »), et la page Méthodologie dit qu'il suit les règles du FALC sans en porter le logo ;
   - *contenu* : ce que fait le texte et quels droits il touche ; le sens (étend, restreint) reste dans l'étiquette du
     site, qui le dit déjà, plutôt que reformulé une seconde fois. À trancher ;
   - *règles d'écriture* fixes et publiques, tirées des règles européennes : phrases courtes, une idée par phrase, mots
     courants, aucun sigle ni terme juridique sans explication, chiffres en chiffres ; longueur bornée (par exemple
     5 phrases, 80 mots) ;
   - *périmètre* : les textes qualifiés (199 au 02/11/2026) ; fiches de suivi et blocs Sénat plus tard, ou jamais.
2. **Champ d'`editorial.json`** : `resume_simple` (texte, absent quand vide), juste après `resume`, avec l'empreinte de ce
   qu'il reformule, pour repérer une fiche changée depuis. Sérialisé à l'identique dans le pipeline (`editorial.py`) et
   l'admin (`qualification.ts`) : fixture partagée, test croisé, `editorial.valider` et `lvnd check` (longueur, termes
   interdits, empreinte à jour).
3. **`lvnd resumer`** (pipeline) : un appel par texte, sans recherche web, à partir de la fiche publiée et des règles
   d'écriture. Même client que `lvnd proposer` : interrupteur, clé et plafond lus dans D1, chaque appel journalisé.
   Contrôles sans LLM avant d'écrire quoi que ce soit : termes interdits, longueur des phrases et du tout, sigles,
   aucun nom d'élu·e ni de groupe, aucun nombre absent de la fiche. Sortie dans D1, à part de la qualification
   (table `propositions`, mode `simple`, ou table dédiée : à voir à l'item). `--prompt` écrit le prompt sans appel.
4. **Relecture dans l'admin** : sur la fiche, le résumé simple proposé, éditable, avec ses contrôles et le geste
   « Valider le résumé simple ». Signalé « à revoir » quand l'empreinte ne correspond plus. Une ligne dans
   « À traiter », section « prêt à relire ». « Publier » ne change pas.
5. **Site** : sur la fiche d'un texte (`/textes/[id]`), un encadré sous le chapô, avec l'intitulé retenu ; page
   Méthodologie : comment il est écrit, par qui il est relu, ce qu'il ne dit pas. Vérifier la lecture à l'écran (taille,
   contraste, mobile) et avec un lecteur d'écran.
6. **Passe initiale** sur les textes qualifiés, après une mesure sur 5 textes (coût, qualité, contrôles) validée par Max ;
   relecture par lots, puis « Publier ». Ensuite, en continu : un texte validé sans résumé simple, ou dont le résumé
   simple est « à revoir », en reçoit une proposition à la passe suivante (Action `propositions.yml`).
7. **Documentation** : `docs/CONCEPTION.md` (champ, encadré), `docs/QUALIFICATION.md` (circuit), `docs/METHODO.md`
   (règles d'écriture), `docs/EXPLOITATION.md`, guide `/aide` de l'admin.

**À faire par Max**, au fil du cycle : trancher l'item 1 ; valider la mesure sur 5 textes ; relire la passe initiale ;
appliquer une éventuelle migration (`npm run db:migrer:distant`) et déployer l'admin (`npm run deploy`).

### Fait dans ce cycle

- Item 1, décisions de Max du 02/11/2026 (recommandations suivies) : intitulé « En mots simples », sans le sigle FALC
  (la page Méthodologie dira qu'il suit ces règles sans en porter le logo) ; le résumé simple dit ce que fait le texte et
  quels droits il touche, **pas le sens**, qui reste dans l'étiquette du site ; périmètre : les textes qualifiés seuls.
  Reste : les règles d'écriture et la longueur (5 phrases, 80 mots par défaut), à fixer à la mesure de l'item 6.
