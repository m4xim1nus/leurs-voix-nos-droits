<script lang="ts">
  // Guide de l'admin : captures numérotées de la vraie interface, et un essai à cocher.
  // Les captures (static/aide/) viennent de l'admin locale, numéros ajoutés : à refaire si un écran change.
  type Etape = { image: string; alt: string; legende: string[] };

  const CLE = 'lvnd-aide-essai';
  const ESSAI = [
    'Ouvrir un texte déjà publié, et comparer sa fiche à sa page sur le site public',
    'Dans « Textes », ouvrir un texte encore sans statut',
    'Lire son dossier à l’Assemblée',
    'Ajouter deux sources, puis un droit principal qui les cite',
    'Retenir le scrutin décisif proposé',
    'Lire les contrôles et l’aperçu du score',
    'Enregistrer au statut « à relire », sans publier'
  ];
  function lire(): boolean[] {
    try {
      const v = JSON.parse(localStorage.getItem(CLE) ?? '[]');
      return ESSAI.map((_, i) => Boolean(v[i]));
    } catch {
      return ESSAI.map(() => false);
    }
  }
  let coches = $state(ESSAI.map(() => false));
  $effect.pre(() => {
    coches = lire();
  });
  function cocher(i: number, oui: boolean) {
    coches[i] = oui;
    try {
      localStorage.setItem(CLE, JSON.stringify(coches));
    } catch {
      // navigation privée : la liste ne se garde pas, et reste utilisable
    }
  }
  const faites = $derived(coches.filter(Boolean).length);
</script>

{#snippet capture(e: Etape)}
  <div class="capture">
    <a href="/aide/{e.image}.webp" target="_blank" rel="noopener">
      <img src="/aide/{e.image}.webp" alt={e.alt} loading="lazy" />
    </a>
    <ol class="legende">
      {#each e.legende as l, i (i)}
        <li><span class="p" aria-hidden="true">{i + 1}</span><span>{@html l}</span></li>
      {/each}
    </ol>
  </div>
{/snippet}

<svelte:head><title>Aide · admin</title></svelte:head>

<h1>Qualifier un texte, pas à pas</h1>
<p class="chapo">
  Ce guide dit où cliquer, pas comment juger : les règles de fond sont dans la
  <a href="https://lvnd.technoperchoir.fr/methodologie" rel="external noopener" target="_blank"
    >méthodologie</a
  >. Les captures sont celles de cette admin, avec des exemples réels ; un clic les agrandit.
</p>
<p class="essentiel">
  <strong>Vous ne pouvez rien casser.</strong> Ce que vous enregistrez reste privé. Rien n’apparaît sur
  le site public avant un clic sur « Publier », et chaque publication reste dans un historique public.
</p>

<nav class="sommaire" aria-label="Étapes">
  <a href="#reperer">1. Se repérer</a>
  <a href="#statuts">2. Les statuts</a>
  <a href="#fiche">3. Remplir la fiche</a>
  <a href="#scrutins">4. Choisir les scrutins</a>
  <a href="#senat">5. Le Sénat</a>
  <a href="#controles">6. Enregistrer</a>
  <a href="#publier">7. Publier</a>
  <a href="#alertes">8. Les alertes</a>
  <a href="#essai">Premier essai</a>
</nav>

<section id="reperer">
  <h2>1. Se repérer</h2>
  <p>
    Vous êtes connecté·e avec votre courriel, par un code reçu à chaque session : il n’y a pas de
    mot de passe. Il signe chacun de vos enregistrements.
  </p>
  {@render capture({
    image: 'textes',
    alt: 'Onglet Textes : les onglets en haut, les filtres, puis la liste des textes.',
    legende: [
      '<b>Les onglets.</b> Textes, À traiter, Aperçu des scores (validés, et brouillons sur demande), Publier, Journal (qui a modifié quoi).',
      '<b>Les filtres.</b> Par défaut : lois ordinaires présélectionnées par mots-clés, avec un scrutin.',
      '<b>Un texte.</b> Un clic ouvre sa fiche.'
    ]
  })}
  <p>
    Le plus souvent, on part de « À traiter » : ce qu’un nouveau vote demande de regarder, rangé en
    quatre sections. <b>Prêt à relire</b> : un vote a eu lieu (ou une source a publié sur un texte
    déjà traité), et le LLM a préparé une proposition qui passe les contrôles ; « mise à jour
    mineure » signale celles qui ne changent ni le statut, ni le droit principal, ni le sens, ni le
    décisif.
    <b>Question de méthode</b> : la proposition signale un cas que les règles ne prévoient pas.
    <b>À faire à la main</b> : pas de proposition utilisable. <b>À venir</b> : textes seulement inscrits,
    rien à qualifier avant le vote.
  </p>
  <p>
    Une proposition du LLM se lit sur sa carte : la phrase en tête dit ce qu’il propose de faire,
    puis le jugement, l’écart avec la fiche actuelle, les sources avec leurs extraits, les points
    d’attention. <b>Charger « à relire »</b> l’écrit sur la fiche, où on la corrige et la valide
    comme toute qualification, avant « Publier » ; <b>Écarter la proposition</b> la retire (un motif
    court aide à mesurer sa qualité). Sur un texte sans proposition, on peut en <b>demander une</b> :
    elle arrive après la prochaine mise à jour des données. Le LLM se règle (interrupteur, clé, plafond
    de dépense) dans l’onglet LLM ; coupé, tout le reste fonctionne.
  </p>
  <p>
    En dessous, les <b>notes internes</b> : un pense-bête saisi en haut de la fiche d’un texte (« fiche
    prête, attendre l’inscription », « motif à actualiser au prochain passage »). Elles ne sont jamais
    publiées ; on en retire une en la vidant.
  </p>
  {@render capture({
    image: 'a-traiter',
    alt: 'Onglet À traiter : les compteurs des quatre sections, puis une carte par texte, avec la proposition du LLM.',
    legende: [
      '<b>Les quatre sections.</b> Un clic sur un compteur y mène : prêt à relire, question de méthode, à faire à la main, à venir.',
      '<b>Prêt à relire.</b> Un vote a eu lieu et la proposition du LLM passe les contrôles. Les mises à jour mineures viennent en tête.',
      '<b>La phrase d’action.</b> Ce que le LLM propose de faire, et ce qu’il faut vérifier d’abord. En dessous : le jugement, puis les sources et leurs extraits, les points d’attention, les incertitudes (un clic les déplie).',
      '<b>Les gestes.</b> « Charger « à relire » » ouvre la fiche avec la proposition ; « Écarter la proposition » la retire (un motif court aide à mesurer sa qualité). « Question tranchée » apparaît sur une question de méthode réglée.',
      '<b>À venir.</b> Textes seulement inscrits : rien à faire avant le vote. « Demander une fiche de suivi au LLM » pour un texte qu’on veut suivre.'
    ]
  })}
</section>

<section id="statuts">
  <h2>2. Les statuts</h2>
  <div class="defile">
    <table>
      <thead><tr><th>Statut</th><th>Sens</th><th>Sur le site ?</th></tr></thead>
      <tbody>
        <tr
          ><td><span class="pastille brouillon">brouillon</span></td><td>en cours d’écriture</td><td
            >non</td
          ></tr
        >
        <tr
          ><td><span class="pastille a-relire">à relire</span></td><td>prêt pour une relecture</td
          ><td>non</td></tr
        >
        <tr
          ><td><span class="pastille valide">validé</span></td><td
            >relu, tous les contrôles passent</td
          ><td>à la prochaine publication</td></tr
        >
        <tr
          ><td><span class="pastille ecarte">écarté</span></td><td
            >non qualifié, avec un motif public</td
          ><td>à la prochaine publication, avec son motif</td></tr
        >
        <tr
          ><td><span class="pastille a-suivre">à suivre</span></td><td
            >fiche avant le vote : droits et sources, sans sens ni scrutin</td
          ><td>à la prochaine publication</td></tr
        >
      </tbody>
    </table>
  </div>
  <p class="note">
    Un texte déjà publié qu’on repasse en brouillon <strong>garde sa version publiée</strong> en ligne
    jusqu’à sa validation. Pour le retirer du site, il faut l’écarter.
  </p>
</section>

<section id="fiche">
  <h2>3. Remplir la fiche</h2>
  <p>
    Les modifications restent locales jusqu’au bouton « Enregistrer », en bas de page. Commencez par
    lire le dossier du texte.
  </p>
  {@render capture({
    image: 'fiche-haut',
    alt: 'Haut de la fiche : liens vers le dossier, identifiant, titre et résumé.',
    legende: [
      '<b>À lire d’abord.</b> Dossier de l’Assemblée, loi sur Légifrance, décision du Conseil constitutionnel.',
      '<b>Identifiant public.</b> Minuscules, chiffres et tirets : il forme l’adresse de la fiche. Ne le changez plus après publication.',
      '<b>Résumé.</b> Une ou deux phrases factuelles sur ce que fait le texte.'
    ]
  })}
  <p>
    Saisissez les <strong>sources d’abord</strong> : les droits les citent. Seules celles de la
    <a
      href="https://lvnd.technoperchoir.fr/methodologie#regle-7"
      rel="external noopener"
      target="_blank">règle 7</a
    > sont admises.
  </p>
  {@render capture({
    image: 'sources',
    alt: 'Tableau des sources : clé, auteur, titre, date, adresse, et boutons pour en ajouter.',
    legende: [
      '<b>La clé.</b> Un nom court (<span class="mono">cnil-2023-05</span>) pour la citer. La renommer met à jour ses citations.',
      '<b>L’adresse.</b> Celle du document, avec sa date au format AAAA-MM-JJ.',
      '<b>+ source</b> ajoute une ligne.',
      '<b>Reprendre</b> une source déjà citée par un autre texte, sans ressaisie.'
    ]
  })}
  {@render capture({
    image: 'droits',
    alt: 'Une ligne de droit : le droit, son rôle, son sens, ses sources et sa justification.',
    legende: [
      '<b>Le droit</b> touché, dans la grille.',
      '<b>Son rôle.</b> Un seul principal, celui de la mesure que les sources citent le plus.',
      '<b>Son sens.</b> Étend ou restreint, du point de vue des personnes (règle 1).',
      '<b>Ses sources</b>, à cocher : au moins une.',
      '<b>La justification.</b> Courte, avec la source.'
    ]
  })}
  <p>
    Plus bas : les <strong>étiquettes</strong> (outre-mer, régimes d’exception), les
    <strong>points de vigilance</strong> (critiques sourcées, affichées à côté du jugement sans le
    modifier), la décision du Conseil constitutionnel et la <strong>note</strong> publique qui explique
    les choix.
  </p>
</section>

<section id="scrutins">
  <h2>4. Choisir les scrutins</h2>
  {@render capture({
    image: 'scrutins',
    alt: 'Section Scrutins : les scrutins retenus, puis tous les scrutins du dossier et les positions des groupes.',
    legende: [
      '<b>Le rôle.</b> Décisif, autre lecture, motion, amendement clé… Seuls le décisif et les amendements clés comptent.',
      '<b>Le sens.</b> Pour un amendement clé, à fixer à la main : il n’est pas compté tant qu’il reste « à trancher » (règle 11).',
      '<b>Le filtre.</b> « Amendements et articles » affiche le reste.',
      '<b>Les positions des groupes</b> sur ce scrutin.',
      '<b>Retenir</b> ce scrutin, dans le rôle choisi.'
    ]
  })}
  <p>En bas de fiche, un tableau montre aussitôt ce que ce texte donne pour chaque groupe.</p>
  <div class="capture seule">
    <img
      src="/aide/apercu.webp"
      alt="Aperçu du score de ce texte : un tableau des groupes, score global et par droit."
      loading="lazy"
    />
  </div>
  <p class="note">
    Un résultat surprend ? Relisez le sens du droit principal et celui des scrutins, c’est le
    meilleur contrôle.
  </p>
</section>

<section id="senat">
  <h2>5. Le vote du Sénat</h2>
  {@render capture({
    image: 'senat',
    alt: 'Section Vote du Sénat : la version votée, le scrutin retenu, et les formulaires de qualification propres à cette version.',
    legende: [
      '<b>Sur quoi porte le vote.</b> Même texte que l’Assemblée : le sens est repris. Autre version : qualifiée à part. Pas de décisif à l’Assemblée : les droits du haut de la fiche valent pour le Sénat.',
      '<b>Le scrutin retenu.</b> Seul le décisif compte.',
      '<b>Autre version</b> : les mêmes formulaires s’ouvrent. Sans source admise sur cette version, retenez le scrutin comme « ensemble », sans droits : il est affiché et non compté.'
    ]
  })}
</section>

<section id="controles">
  <h2>6. Enregistrer et lire les contrôles</h2>
  {@render capture({
    image: 'enregistrer',
    alt: 'Barre d’enregistrement : messages d’erreur, statut, commentaire et bouton Enregistrer.',
    legende: [
      '<b>Les contrôles</b>, en direct. En rouge : à corriger pour valider ; un brouillon s’enregistre quand même. Les avertissements n’empêchent rien.',
      '<b>Le statut.</b>',
      '<b>Le commentaire</b>, privé, pour l’historique.',
      '<b>Enregistrer.</b> Si quelqu’un a modifié le texte entre-temps, l’admin refuse : copiez vos ajouts, rechargez, reprenez.'
    ]
  })}
  <p class="note">
    L’historique, en bas de fiche, permet de recharger une ancienne version. Pour écarter un texte :
    statut « écarté », et un motif public qui cite la règle en cause.
  </p>
</section>

<section id="publier">
  <h2>7. Publier</h2>
  {@render capture({
    image: 'publier',
    alt: 'Page Publier : la liste des changements et le bouton Publier.',
    legende: [
      '<b>Ce qui va changer sur le site</b>, depuis la dernière publication.',
      '<b>Chaque ligne</b> est un texte nouveau ou modifié : relisez-la. Des sources définies et non citées sont signalées.',
      '<b>Publier</b> crée un commit à votre nom dans le dépôt public. Le site se reconstruit en quelques minutes. Grisé : un texte validé a une erreur, et la page dit lequel.'
    ]
  })}
  <p class="note">
    Une liste privée de termes fait refuser certaines sources au moment de publier. Si cela vous
    arrive, cherchez une autre source.
  </p>
</section>

<section id="alertes">
  <h2>8. Ce que demande chaque alerte</h2>
  <div class="defile">
    <table>
      <thead><tr><th>Alerte</th><th>Ce qu’elle demande</th></tr></thead>
      <tbody>
        <tr
          ><td>Vote sur l’ensemble après le décisif</td><td
            >Le nouveau vote devient le décisif : relire le sens sur le texte voté</td
          ></tr
        >
        <tr
          ><td>Lecture close après le décisif, sans vote public sur l’ensemble</td><td
            >Relire la fiche : retenir la motion, ou dire dans la note ce qui s’est passé, avec sa
            date (19/11/2026)</td
          ></tr
        >
        <tr
          ><td>Écarté pour unanimité, vote contesté</td><td
            >Qualifier, ou garder l’écart avec un motif à jour</td
          ></tr
        >
        <tr
          ><td>Texte écarté, revoté à l’Assemblée</td><td
            >Qualifier, ou garder l’écart avec un motif qui cite ce vote (décompte, ou date sans
            scrutin public)</td
          ></tr
        >
        <tr><td>Décisif d’un texte non traité</td><td>Qualifier, ou écarter avec son motif</td></tr>
        <tr
          ><td>Lecture close sans décisif proposé</td><td
            >Lire le dossier, puis qualifier ou écarter</td
          ></tr
        >
        <tr
          ><td>Texte non traité, inscrit en séance</td><td
            >Rien à qualifier : le vote n’a pas eu lieu. Repérer les sources, ou rédiger une fiche «
            à suivre » (le LLM peut en préparer une, sur demande)</td
          ></tr
        >
        <tr
          ><td>Vote du Sénat à lire, nouveau vote du Sénat</td><td
            >Remplir ou mettre à jour le bloc « Vote du Sénat »</td
          ></tr
        >
      </tbody>
    </table>
  </div>
</section>

<section id="essai" class="essai">
  <h2>Premier essai : dix minutes, sans risque</h2>
  <p>
    {faites} étape{faites > 1 ? 's' : ''} sur {ESSAI.length}. Laissez le texte « à relire » : il ne
    sera pas publié, et on le relira avec vous.
  </p>
  <ul>
    {#each ESSAI as e, i (i)}
      <li>
        <label>
          <input
            type="checkbox"
            checked={coches[i]}
            onchange={(ev) => cocher(i, ev.currentTarget.checked)}
          />
          <span>{e}</span>
        </label>
      </li>
    {/each}
  </ul>
</section>

<style>
  h1 {
    margin-bottom: 0.3rem;
  }
  .chapo {
    max-width: 70ch;
  }
  .essentiel {
    background: var(--ok-fond);
    padding: 0.7rem 1rem;
    border-radius: 6px;
    max-width: 70ch;
  }
  .sommaire {
    display: flex;
    flex-wrap: wrap;
    gap: 0.3rem 1rem;
    padding: 0.6rem 0;
    position: sticky;
    top: 0;
    background: var(--fond);
    border-bottom: 1px solid var(--bord);
    z-index: 2;
  }
  section {
    margin-top: 2.2rem;
    scroll-margin-top: 3.2rem;
  }
  section > p {
    max-width: 75ch;
  }
  .capture {
    display: grid;
    grid-template-columns: minmax(0, 3fr) minmax(0, 2fr);
    gap: 1.2rem;
    align-items: start;
    margin: 1rem 0;
  }
  .capture.seule {
    grid-template-columns: minmax(0, 3fr);
    max-width: 60%;
  }
  .capture img {
    width: 100%;
    height: auto;
    display: block;
    border: 1px solid var(--bord);
    border-radius: 6px;
  }
  .legende {
    list-style: none;
    margin: 0;
    padding: 0;
    display: grid;
    gap: 0.6rem;
  }
  .legende li {
    display: grid;
    grid-template-columns: 1.6rem minmax(0, 1fr);
    gap: 0.5rem;
    align-items: start;
  }
  .p {
    width: 1.6rem;
    height: 1.6rem;
    border-radius: 50%;
    background: #c2185b;
    color: #fff;
    font-weight: 700;
    font-size: 0.85rem;
    line-height: 1.6rem;
    text-align: center;
  }
  .note {
    color: var(--texte-2);
  }
  .defile {
    overflow-x: auto;
  }
  .essai {
    background: var(--surface);
    border: 1px solid var(--bord);
    border-radius: 8px;
    padding: 1rem 1.2rem;
  }
  .essai ul {
    list-style: none;
    padding: 0;
    margin: 0.6rem 0 0;
    display: grid;
    gap: 0.45rem;
  }
  .essai label {
    display: flex;
    gap: 0.5rem;
    align-items: baseline;
  }
  @media (max-width: 800px) {
    .capture,
    .capture.seule {
      grid-template-columns: minmax(0, 1fr);
      max-width: none;
    }
  }
</style>
