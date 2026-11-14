<script lang="ts">
  import Regle from '$lib/components/Regle.svelte';
  import VoteCarte, { type TexteVote } from '$lib/components/VoteCarte.svelte';
  import { courrielProchainVote } from '$lib/courriel';
  import { court, scoreSousAngle, sousAngle } from '$lib/droits';
  import {
    circonscription,
    date,
    depute as dep,
    etatTexte,
    inscription,
    legislature,
    minuscule,
    normaliser,
    pluriel,
    POSITION,
    POSITION_GROUPE,
    pourcent,
    voteDeLecture
  } from '$lib/format';
  import { NOM, URL_SITE } from '$lib/site';
  import { bilanTexte } from '$lib/votes-depute';

  let { data } = $props();
  const d = $derived(data.depute);
  const nom = $derived(`${d.prenom} ${d.nom}`);
  const elle = $derived(d.civ === 'Mme');

  const mailto = $derived(
    d.courriel
      ? `mailto:${d.courriel}?subject=${encodeURIComponent('Vos votes sur les droits et libertés')}&body=${encodeURIComponent(
          `Bonjour ${d.civ === 'Mme' ? 'Madame la Députée' : 'Monsieur le Député'},\n\nJ’ai consulté vos votes sur les textes qui touchent aux droits et libertés :\n${URL_SITE}/deputes/${d.slug}\n\n`
        )}`
      : null
  );

  // Règle 19 : à partir de deux législatures, la règle dit sur laquelle se fait la comparaison.
  const suffixe = $derived(
    data.comparaison?.plusieurs ? `, ${legislature(data.comparaison.legislature)}` : ''
  );

  const seancesDe = (p: (typeof data.prochains)[number]) =>
    p.seances.length ? p.seances : p.date_inscrite ? [p.date_inscrite] : [];
  const mailtoProchain = (p: (typeof data.prochains)[number]) => {
    if (!d.courriel) return null;
    const { sujet, corps } = courrielProchainVote({
      titre: p.titre,
      url: `${URL_SITE}${p.href}`,
      feminin: elle,
      seances: seancesDe(p),
      vote: p.vote
    });
    return `mailto:${d.courriel}?subject=${encodeURIComponent(sujet)}&body=${encodeURIComponent(corps)}`;
  };

  // Prochains votes : les trois premiers, le reste sur demande.
  const PROCHAINS = 3;
  let tousProchains = $state(false);
  const prochains = $derived(tousProchains ? data.prochains : data.prochains.slice(0, PROCHAINS));
  const prochainsCaches = $derived(data.prochains.length - prochains.length);

  // Choix éditorial à valider (question à Max) : par défaut, la liste ne montre que les textes où
  // l'élu·e a voté pour ou contre ; absences, abstentions et non-votes sont regroupés en une ligne,
  // avec un bouton qui les affiche. `false` revient à la liste complète.
  const REGROUPER_HORS_CALCUL = true;

  // Un clic sur une tuile de droit ne garde que ses textes, vus sous l'angle de ce droit.
  let filtre = $state<string | null>(null);
  type Vue = '' | 'favorable' | 'defavorable' | 'hors';
  let vue = $state<Vue>('');
  let saisie = $state('');
  const q = $derived(normaliser(saisie));

  const parDroit = $derived(
    data.textes.flatMap((t): TexteVote[] => {
      if (filtre && !t.texte.droits.some((x) => x.code === filtre)) return [];
      const vu = sousAngle(t.texte, filtre);
      return [
        {
          ...t,
          vu,
          score: scoreSousAngle(t.score?.score ?? null, vu.inverse),
          bilan: bilanTexte(t.votes, vu.inverse)
        }
      ];
    })
  );
  // Regroupés seulement s'il reste un texte où l'élu·e a voté pour ou contre, et hors recherche.
  const regrouper = $derived(
    REGROUPER_HORS_CALCUL && !q && parDroit.some((t) => t.bilan !== 'hors')
  );
  // Un texte où l'élu·e a voté dans les deux sens figure sous « pour » comme sous « contre ».
  const dans = (t: TexteVote, v: Vue) =>
    v === 'favorable'
      ? t.bilan === 'favorable' || t.bilan === 'partage'
      : v === 'defavorable'
        ? t.bilan === 'defavorable' || t.bilan === 'partage'
        : v === 'hors'
          ? t.bilan === 'hors'
          : !regrouper || t.bilan !== 'hors';
  const trouves = $derived(
    q ? parDroit.filter((t) => normaliser(t.texte.titre).includes(q)) : parDroit
  );
  const compte = (v: Vue) => trouves.filter((t) => dans(t, v)).length;
  const textes = $derived(trouves.filter((t) => dans(t, vue)));
  const hors = $derived(compte('hors'));
  const regroupes = $derived(regrouper && vue === '' && hors > 0);

  const aux = $derived(filtre ? 'à ce droit' : 'aux droits');
  const titreResultats = $derived.by(() => {
    const n = textes.length;
    const avec = (quoi: string) =>
      pluriel(n, `texte ${quoi}`, `textes ${quoi}`, `Aucun texte ${quoi}`);
    const libelle =
      vue === 'favorable'
        ? avec(`avec un vote favorable ${aux}`)
        : vue === 'defavorable'
          ? avec(`avec un vote défavorable ${aux}`)
          : vue === 'hors'
            ? avec('sans vote pour ou contre')
            : regrouper
              ? avec(`où ${elle ? 'elle' : 'il'} a voté pour ou contre`)
              : pluriel(n, 'texte', 'textes', 'Aucun texte');
    return [libelle, filtre && court(filtre), q && `« ${saisie.trim()} »`]
      .filter(Boolean)
      .join(' · ');
  });
  // L'abstention n'est pas une absence : la ligne qui les regroupe dit combien de textes en ont une.
  const abstenus = $derived(
    trouves.filter((t) => t.bilan === 'hors' && t.votes.some((v) => v.position === 'abstention'))
      .length
  );
  const ligneHors = $derived(
    `${elle ? 'Absente' : 'Absent'}, abstention ou ${elle ? 'non-votante' : 'non-votant'} sur ${pluriel(hors, 'texte')}${abstenus ? ` (dont ${abstenus} avec une abstention)` : ''}, hors calcul.`
  );
  const choisirVue = (v: Vue) => (vue = vue === v ? '' : v);
</script>

<svelte:head>
  <title>{nom}, {NOM}</title>
  <meta
    name="description"
    content="Votes de {nom} sur les textes qui touchent aux droits et libertés{data.global
      ? ` : ${pourcent(data.global.score)} de votes favorables aux droits`
      : ''}."
  />
  <meta property="og:title" content={nom} />
  <meta property="og:image" content="{URL_SITE}/cartes/deputes/{d.slug}.png" />
  <meta name="twitter:card" content="summary_large_image" />
</svelte:head>

{#if data.lignee}
  <p class="discret"><a href="/groupes/{data.lignee.slug}">{data.lignee.nom}</a></p>
{/if}
<h1>{nom}</h1>
<p class="situation">
  {#if data.mandat}
    {#if data.actuel}
      {dep(d.civ, true)} depuis le {date(data.mandat.debut)} :
      <a href="/circonscriptions/{data.mandat.circo}"
        >{data.mandat.departement}, {circonscription(data.mandat.num_circo)}</a
      >.
    {:else}
      {elle ? 'Ancienne députée' : 'Ancien député'}, {legislature(data.mandat.legislature)} législature{#if data.mandat.fin},
        jusqu’au {date(data.mandat.fin)}{/if} :
      <a href="/circonscriptions/{data.mandat.circo}"
        >{data.mandat.departement}, {circonscription(data.mandat.num_circo)}</a
      >.
    {/if}
  {/if}
  {#if data.groupe}
    {data.actuel ? 'Groupe' : 'Dernier groupe'} :
    <span class="sigle" style:--c={data.groupe.couleur}>{data.groupe.sigle}</span> ({data.groupe
      .nom}).
  {/if}
</p>

{#if data.global}
  <section class="chiffre-cle">
    <p class="grand-chiffre chiffre">{pourcent(data.global.score)}</p>
    <p>
      de votes favorables aux droits, sur {pluriel(
        data.global.n_textes,
        'texte qualifié',
        'textes qualifiés'
      )}.
      {#if data.participation}
        {elle ? 'Elle' : 'Il'} a pris part à {data.participation.votes} des {pluriel(
          data.participation.scrutins,
          'scrutin compté',
          'scrutins comptés'
        )}
        tenus pendant {data.depute.mandats.length > 1 ? 'ses mandats' : 'son mandat'} ({pourcent(
          data.participation.taux
        )}).
      {/if}
      {#if data.global.abstentions}{pluriel(data.global.abstentions, 'abstention')}, hors calcul.{/if}
    </p>
  </section>
  {#if data.parLegislature.length > 1}
    <p class="par-legislature">
      Par législature :
      {#each data.parLegislature as l, i (l.legislature)}{#if i},{' '}{/if}<span class="chiffre"
          >{pourcent(l.score.score)}</span
        >
        en {legislature(l.legislature)}
        ({pluriel(l.score.n_textes, 'texte')}){/each}.
    </p>
  {/if}
  <Regle
    lignes={[
      {
        cle: 'depute',
        libelle: `${d.nom}${suffixe}`,
        score: data.comparaison?.depute.score ?? data.global.score,
        avant: true,
        couleur: data.groupe?.couleur
      },
      ...(data.lignee && data.comparaison
        ? [
            {
              cle: 'groupe',
              libelle: `Groupe ${data.lignee.sigle}${suffixe}`,
              href: `/groupes/${data.lignee.slug}`,
              couleur: data.lignee.couleur,
              score: data.comparaison.groupe.score
            }
          ]
        : [])
    ]}
  />
{:else}
  <p class="chapo">
    Aucun vote compté : {elle ? 'elle' : 'il'} n’a voté sur aucun des scrutins comptés des textes qualifiés
    à ce jour.
  </p>
{/if}

<p class="actions">
  {#if mailto}
    <a class="bouton" href={mailto}>Lui écrire</a>
  {/if}
  <a class="bouton secondaire" href="/cartes/deputes/{d.slug}.png" download="{d.slug}.png"
    >Télécharger l’image</a
  >
  <a class="petit" href="/cartes/portrait/deputes/{d.slug}.png" download="{d.slug}-portrait.png"
    >format portrait, pour les réseaux</a
  >
  {#if data.lignee && data.global}
    <a class="petit" href="/comparer?a=d:{d.slug}&b=g:{data.lignee.slug}"
      >Comparer avec son groupe</a
    >
  {/if}
  {#if d.courriel}<span class="discret petit">{d.courriel}</span>{/if}
  {#if data.actuel && data.mandat}
    <a class="petit" href="/senat#dep-{data.mandat.circo.split('-')[0]}"
      >Les sénateur·ices de {data.mandat.departement}</a
    >
  {/if}
</p>

{#if data.prochains.length}
  <section>
    <h2>Prochains votes</h2>
    <p>
      Les textes retenus sur ce site <a href="/en-cours">attendus à l’Assemblée</a>, et son vote à
      la lecture précédente. Un texte inscrit à l’ordre du jour n’est pas forcément examiné à cette
      date, ni voté.
    </p>
    {#each prochains as p (p.id)}
      {@const m = mailtoProchain(p)}
      <article class="texte">
        <h3><a href={p.href}>{p.titre}</a></h3>
        <p class="petit">
          <strong
            >{seancesDe(p).length
              ? inscription('AN', seancesDe(p))
              : 'Attendu à l’Assemblée, pas encore inscrit'}.</strong
          >
          {#if p.vote}
            Le {date(p.vote.date)}{voteDeLecture(p.vote.etape)
              ? ` (${voteDeLecture(p.vote.etape)})`
              : ''} :
            {#if p.vote.position === null}
              {elle ? 'elle' : 'il'} n’était pas encore {elle ? 'députée' : 'député'}.
            {:else if p.vote.position === 'absent'}
              <strong>{elle ? 'absente' : 'absent'}</strong>.
            {:else}
              <strong>{POSITION[p.vote.position].toLowerCase()}</strong>.
            {/if}
            {#if p.vote.groupe}
              <span class="sigle" style:--c={p.vote.groupe.couleur}>{p.vote.groupe.sigle}</span
              >&nbsp;: {POSITION_GROUPE[p.vote.groupe.position]}.
            {/if}
            <a href={p.vote.url} rel="external">Le scrutin</a>.
          {:else}
            Aucun vote public de l’Assemblée sur ce texte pour l’instant.
          {/if}
        </p>
        {#if m}<p class="petit"><a href={m}>Lui écrire sur ce texte</a></p>{/if}
      </article>
    {/each}
    {#if prochainsCaches}
      <p>
        <button type="button" class="lien" onclick={() => (tousProchains = true)}
          >{prochainsCaches === 1
            ? 'Voir l’autre texte'
            : `Voir les ${prochainsCaches} autres`}</button
        >
      </p>
    {/if}
  </section>
{/if}

{#if data.droits.length}
  <section>
    <h2>Droit par droit</h2>
    <p class="petit discret">
      Part de ses votes favorables à chaque droit. Choisissez un droit pour n’afficher que ses
      textes.
    </p>
    <ul class="tuiles">
      {#each data.droits as x (x.droit.code)}
        {@const s = x.score.score}
        <li>
          <button
            type="button"
            class="tuile"
            aria-pressed={filtre === x.droit.code}
            onclick={() => (filtre = filtre === x.droit.code ? null : x.droit.code)}
          >
            <span class="nom">{x.droit.court}</span>
            <span class="barre" aria-hidden="true"
              >{#if s !== null}<span class="e" style:width="{s}%"></span><span
                  class="r"
                  style:width="{100 - s}%"
                ></span>{/if}</span
            >
            <span class="compte"
              ><span class="chiffre">{pourcent(s)}</span><span class="visuellement-cache">
                de votes favorables à ce droit,</span
              >
              <span class="discret">sur {pluriel(x.score.n_textes, 'texte')}</span></span
            >
          </button>
        </li>
      {/each}
    </ul>
  </section>
{/if}

{#if data.textes.length}
  <section>
    <h2>Ses votes, texte par texte</h2>
    <p>
      Pour chaque texte qualifié, ce que son vote sur les scrutins comptés signifie pour les droits.
      Absent, non-votant ou abstentionniste : son vote n’entre pas dans le score. Les motions et les
      autres lectures sont sur la fiche de chaque texte.
    </p>
    <div class="outils">
      <div class="puces" role="group" aria-label="Filtrer ses votes">
        <button
          type="button"
          class="favorable"
          aria-pressed={vue === 'favorable'}
          onclick={() => choisirVue('favorable')}
          >▲ Pour les droits <span class="n">{compte('favorable')}</span></button
        >
        <button
          type="button"
          class="defavorable"
          aria-pressed={vue === 'defavorable'}
          onclick={() => choisirVue('defavorable')}
          >▼ Contre les droits <span class="n">{compte('defavorable')}</span></button
        >
        <button type="button" aria-pressed={vue === 'hors'} onclick={() => choisirVue('hors')}
          >Absences et abstentions <span class="n">{hors}</span></button
        >
      </div>
      <form class="cherche" role="search" onsubmit={(e) => e.preventDefault()}>
        <label for="cherche-textes" class="visuellement-cache">Chercher parmi ses textes</label>
        <input
          id="cherche-textes"
          type="search"
          bind:value={saisie}
          autocomplete="off"
          spellcheck="false"
          placeholder="Chercher un texte…"
        />
      </form>
    </div>
    {#if filtre}
      <p class="filtre">
        <span
          >Textes qui touchent à <strong>{court(filtre)}</strong>, avec la lecture de chaque vote
          pour ce droit.</span
        >
        <button type="button" onclick={() => (filtre = null)}>Tous les droits</button>
        <a href="/droits/{filtre}">{court(filtre)} : tous les groupes</a>
      </p>
    {/if}
    <h3 class="resultats" aria-live="polite">{titreResultats}</h3>
    {#if regroupes}
      <p class="regroupes">
        <span>{ligneHors}</span>
        <button type="button" class="lien" onclick={() => (vue = 'hors')}>Les afficher</button>
      </p>
    {/if}
    <ul class="cartes">
      {#each textes as t (t.texte.id)}
        <li><VoteCarte {t} {elle} surDroit={Boolean(filtre)} /></li>
      {/each}
    </ul>
  </section>
{/if}

{#if data.unanimes.length}
  <section>
    <h2>Textes adoptés sans opposition</h2>
    <p>
      Ces textes, examinés pour le site, ont été adoptés sans aucune voix contre. Ce vote ne
      distingue aucun·e député·e des autres : ils ne sont ni qualifiés ni comptés dans le score. Sur
      ces {data.unanimes.length} textes,
      {elle ? 'elle' : 'il'} a voté pour
      {data.unanimes.filter((u) => u.position === 'pour').length} fois.
    </p>
    <details>
      <summary>{pluriel(data.unanimes.length, 'texte', 'textes')} et son vote</summary>
      <ul class="unanimes">
        {#each data.unanimes as u (u.url)}
          <li>
            <a href={u.url} rel="external">{u.titre}</a>
            <span class="discret petit"
              >{date(u.date)}{etatTexte(u.etat) ? `, ${minuscule(etatTexte(u.etat))}` : ''}</span
            >
            :
            <strong
              >{u.position === 'absent'
                ? elle
                  ? 'absente'
                  : 'absent'
                : POSITION[u.position].toLowerCase()}</strong
            >
          </li>
        {/each}
      </ul>
    </details>
  </section>
{/if}

{#if d.groupes.length > 1 || d.mandats.length > 1}
  <section>
    <h2>Mandats et groupes</h2>
    <ul>
      {#each d.mandats as m, i (i)}
        <li>
          {legislature(m.legislature)} législature,
          <a href="/circonscriptions/{m.circo}">{m.departement} ({m.num_circo})</a>
          : du {date(m.debut)}{#if m.fin}
            au {date(m.fin)}{/if}{#if m.cause_fin}
            ({m.cause_fin.toLowerCase()}){/if}.
        </li>
      {/each}
      {#each d.groupes as g, i (i)}
        <li>
          <span class="sigle" style:--c={g.groupe.couleur}>{g.groupe.sigle}</span>
          ({g.qualite.toLowerCase()}) : du {date(g.debut)}{#if g.fin}
            au {date(g.fin)}{/if}.
        </li>
      {/each}
    </ul>
    <p class="petit discret">Chaque vote compte pour le groupe où siégeait l’élu·e ce jour-là.</p>
  </section>
{/if}

<style>
  .situation {
    font-size: 1.1rem;
    max-width: 60ch;
    margin-top: 0.75rem;
  }
  .chiffre-cle {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 0 1.25rem;
    margin-top: 1.5rem;
  }
  .par-legislature {
    margin-top: 0.75rem;
  }
  .grand-chiffre {
    font-size: clamp(4.5rem, 16vw, 8rem);
    line-height: 0.9;
    margin: 0;
  }
  .chiffre-cle p:last-child {
    max-width: 34ch;
    font-size: 1.1rem;
  }
  .bouton {
    display: inline-block;
    padding: 0.55rem 1.1rem;
    background: var(--encre);
    color: var(--papier);
    border-radius: 3px;
    font-weight: 700;
    text-decoration: none;
    margin-right: 0.5rem;
  }
  .actions {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.5rem 0.75rem;
  }
  .bouton.secondaire {
    background: var(--papier);
    color: var(--encre);
    border: 2px solid var(--encre);
    padding: calc(0.55rem - 2px) calc(1.1rem - 2px);
  }
  .texte {
    margin-top: 1.5rem;
  }
  .texte h3 a {
    text-decoration: none;
  }
  .texte h3 a:hover {
    text-decoration: underline;
  }
  .filtre {
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    gap: 0.3rem 1rem;
    max-width: none;
    padding: 0.6rem 0.8rem;
    background: var(--plan);
    border-radius: 3px;
  }
  .filtre button {
    font: inherit;
    font-weight: 650;
    color: var(--encre);
    background: var(--papier);
    border: 1.5px solid var(--encre);
    border-radius: 3px;
    padding: 0.1rem 0.6rem;
    cursor: pointer;
  }
  details summary {
    cursor: pointer;
    font-weight: 650;
  }
  .unanimes li {
    margin-bottom: 0.35rem;
  }
  .lien {
    font: inherit;
    font-weight: 650;
    background: none;
    border: 0;
    padding: 0;
    color: var(--lien);
    text-decoration: underline;
    cursor: pointer;
    min-height: 2.75rem;
  }

  /* Droit par droit : une tuile par droit, comme sur la page des textes. */
  .tuiles {
    list-style: none;
    padding: 0;
    margin: 1rem 0 0;
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(min(100% / 2 - 0.3rem, 12rem), 1fr));
    gap: 0.6rem;
  }
  .tuiles li {
    max-width: none;
  }
  .tuile {
    width: 100%;
    height: 100%;
    font: inherit;
    text-align: left;
    color: var(--encre);
    background: var(--papier);
    border: 1px solid var(--filet);
    border-radius: 10px;
    padding: 0.8rem 0.9rem;
    cursor: pointer;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  .tuile:hover {
    border-color: var(--encre);
  }
  .tuile[aria-pressed='true'] {
    border: 2px solid var(--encre);
    background: var(--plan);
  }
  .tuile .nom {
    font-weight: 700;
    line-height: 1.2;
    overflow-wrap: anywhere;
  }
  .barre {
    display: flex;
    height: 6px;
    border-radius: 3px;
    overflow: hidden;
    background: var(--filet);
    margin-top: auto;
  }
  .barre .e {
    background: var(--favorable);
  }
  .barre .r {
    background: var(--defavorable);
  }
  .compte {
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    gap: 0 0.5rem;
    font-size: 0.9rem;
  }
  .compte .chiffre {
    font-size: 1.4rem;
  }

  /* Ses votes : filtres, recherche, cartes. */
  .outils {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.75rem 1.5rem;
    margin: 1.25rem 0 1rem;
  }
  .puces {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }
  .puces button {
    font: inherit;
    font-size: 0.95rem;
    font-weight: 650;
    min-height: 2.75rem;
    padding: 0 0.9rem;
    border: 2px solid var(--encre);
    border-radius: 999px;
    background: var(--papier);
    color: var(--encre);
    cursor: pointer;
    white-space: nowrap;
  }
  .puces .n {
    font-weight: 400;
    margin-left: 0.2rem;
  }
  .puces button[aria-pressed='true'] {
    background: var(--ardoise);
    border-color: var(--ardoise);
    color: var(--papier);
  }
  .puces button.favorable[aria-pressed='true'] {
    background: var(--favorable);
    border-color: var(--favorable);
  }
  .puces button.defavorable[aria-pressed='true'] {
    background: var(--defavorable);
    border-color: var(--defavorable);
  }
  .cherche {
    flex: 1 1 14rem;
    max-width: 24rem;
  }
  .cherche input {
    width: 100%;
    box-sizing: border-box;
    min-height: 2.75rem;
    padding: 0 1rem;
    font: inherit;
    color: var(--encre);
    background: var(--papier);
    border: 2px solid var(--encre);
    border-radius: 999px;
  }
  .resultats {
    margin: 1.5rem 0 0.75rem;
    padding-top: 1rem;
    border-top: 1px solid var(--filet);
  }
  .regroupes {
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    gap: 0 1rem;
    margin: 0 0 1rem;
    max-width: none;
    color: var(--ardoise);
  }
  .cartes {
    list-style: none;
    padding: 0;
    margin: 0;
    display: grid;
    gap: 0.75rem;
  }
  .cartes li {
    max-width: none;
  }
  @media (max-width: 30rem) {
    .puces {
      gap: 0.4rem;
    }
    .puces button {
      font-size: 0.85rem;
      padding: 0 0.65rem;
    }
  }
</style>
