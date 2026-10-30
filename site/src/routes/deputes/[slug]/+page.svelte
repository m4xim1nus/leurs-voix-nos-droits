<script lang="ts">
  import Regle from '$lib/components/Regle.svelte';
  import { courrielProchainVote } from '$lib/courriel';
  import { court, phrase, scoreSousAngle, sousAngle } from '$lib/droits';
  import {
    circonscription,
    date,
    depute as dep,
    etatTexte,
    inscription,
    legislature,
    mentionNavette,
    minuscule,
    pluriel,
    POSITION,
    POSITION_GROUPE,
    pourcent,
    voteDeLecture
  } from '$lib/format';
  import type { VoteDepute } from '$lib/server/vues';
  import { NOM, URL_SITE } from '$lib/site';
  import type { EtatTexte } from '$lib/types';

  let { data } = $props();
  const d = $derived(data.depute);
  const nom = $derived(`${d.prenom} ${d.nom}`);
  const elle = $derived(d.civ === 'Mme');

  /** `inverse` : texte vu sous l'angle d'un droit de sens contraire à son droit principal. */
  function lecture(v: VoteDepute, inverse: boolean): { texte: string; classe: string } {
    const s = v.scrutin;
    if (!s.compte) return { texte: 'non compté', classe: 'discret' };
    if (v.position === 'pour' || v.position === 'contre')
      return (v.position === s.favorable) !== inverse
        ? { texte: 'favorable aux droits', classe: 'favorable' }
        : { texte: 'défavorable aux droits', classe: 'defavorable' };
    return { texte: 'hors calcul', classe: 'discret' };
  }

  const mailto = $derived(
    d.courriel
      ? `mailto:${d.courriel}?subject=${encodeURIComponent('Vos votes sur les droits et libertés')}&body=${encodeURIComponent(
          `Bonjour ${d.civ === 'Mme' ? 'Madame la Députée' : 'Monsieur le Député'},\n\nJ’ai consulté vos votes sur les textes qui touchent aux droits et libertés :\n${URL_SITE}/deputes/${d.slug}\n\n`
        )}`
      : null
  );

  const seancesDe = (p: (typeof data.prochains)[number]) =>
    p.seances.length ? p.seances : p.date_inscrite ? [p.date_inscrite] : [];
  const mailtoProchain = (p: (typeof data.prochains)[number]) => {
    if (!d.courriel) return null;
    const { sujet, corps } = courrielProchainVote({
      titre: p.titre,
      url: `${URL_SITE}/textes/${p.id}`,
      feminin: elle,
      seances: seancesDe(p),
      vote: p.vote
    });
    return `mailto:${d.courriel}?subject=${encodeURIComponent(sujet)}&body=${encodeURIComponent(corps)}`;
  };

  // Un clic sur un droit de la règle ne garde que ses textes, vus sous l'angle de ce droit.
  let filtre = $state<string | null>(null);
  const textes = $derived(
    data.textes.flatMap((t) => {
      if (filtre && !t.texte.droits.some((x) => x.code === filtre)) return [];
      const vu = sousAngle(t.texte, filtre);
      return [{ ...t, vu, score: scoreSousAngle(t.score?.score ?? null, vu.inverse) }];
    })
  );
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

{#snippet vote(v: VoteDepute, inverse: boolean, etat: EtatTexte | null)}
  {@const l = lecture(v, inverse)}
  {@const mention = mentionNavette(etat, v.scrutin.etape)}
  <li>
    <span class="objet"
      ><a href={v.scrutin.url} rel="external">{v.scrutin.objet}</a>
      <span class="petit discret">{date(v.scrutin.date)}{mention ? `, ${mention}` : ''}</span></span
    >
    <span class="position"
      >{v.position === 'absent' ? (elle ? 'Absente' : 'Absent') : POSITION[v.position]}</span
    >
    <span class="lecture {l.classe}">{l.texte}</span>
    <span class="groupe petit">
      {#if v.groupe}<span class="sigle" style:--c={v.groupe.couleur}>{v.groupe.sigle}</span
        >{#if v.ventilation}&nbsp;: {POSITION_GROUPE[v.ventilation.position]}{/if}{/if}
    </span>
  </li>
{/snippet}

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
        tenus pendant son mandat ({pourcent(data.participation.taux)}).
      {/if}
      {#if data.global.abstentions}{pluriel(data.global.abstentions, 'abstention')}, hors calcul.{/if}
    </p>
  </section>
  <Regle
    lignes={[
      {
        cle: 'depute',
        libelle: d.nom,
        score: data.global.score,
        avant: true,
        couleur: data.groupe?.couleur
      },
      ...(data.lignee && data.scoreGroupe
        ? [
            {
              cle: 'groupe',
              libelle: `Groupe ${data.lignee.sigle}`,
              href: `/groupes/${data.lignee.slug}`,
              couleur: data.lignee.couleur,
              score: data.scoreGroupe.score
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
</p>

{#if data.prochains.length}
  <section>
    <h2>Prochains votes</h2>
    <p>
      Les textes retenus sur ce site <a href="/en-cours">attendus à l’Assemblée</a>, et son vote à
      la lecture précédente. Un texte inscrit à l’ordre du jour n’est pas forcément examiné à cette
      date, ni voté.
    </p>
    {#each data.prochains as p (p.id)}
      {@const m = mailtoProchain(p)}
      <article class="texte">
        <h3><a href="/textes/{p.id}">{p.titre}</a></h3>
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
  </section>
{/if}

{#if data.droits.length}
  <section>
    <h2>Droit par droit</h2>
    <p class="petit discret">Choisissez un droit pour n’afficher que ses textes.</p>
    <Regle
      legende={false}
      choisie={filtre}
      onchoisir={(c) => (filtre = filtre === c ? null : c)}
      lignes={data.droits.map((x) => ({
        cle: x.droit.code,
        libelle: x.droit.court,
        href: `/droits/${x.droit.code}`,
        score: x.score.score,
        n_textes: x.score.n_textes
      }))}
    />
  </section>
{/if}

{#if data.textes.length}
  <section>
    <h2>Ses votes, texte par texte</h2>
    <p>
      Pour chaque texte qualifié, son vote sur les scrutins comptés et ce qu’il signifie pour les
      droits. Absent, non-votant ou abstentionniste : son vote n’entre pas dans le score. Les
      motions et les autres lectures sont sur la fiche de chaque texte.
    </p>
    {#if filtre}
      <p class="filtre" role="status">
        <span
          >{pluriel(textes.length, 'texte touche', 'textes touchent')} à
          <strong>{court(filtre)}</strong>, avec la lecture de chaque vote pour ce droit.</span
        >
        <button type="button" onclick={() => (filtre = null)}>Tous les textes</button>
        <a href="/droits/{filtre}">{court(filtre)} : tous les groupes</a>
      </p>
    {/if}
    {#each textes as t (t.texte.id)}
      <article class="texte">
        <h3><a href="/textes/{t.texte.id}">{t.texte.titre}</a></h3>
        <p class="petit">
          {#if etatTexte(t.texte.etat)}{etatTexte(t.texte.etat)}.{/if}
          Le texte {phrase(t.vu.code, t.vu.sens)}.
          {#if t.score !== null}Sur ce texte : <strong>{pourcent(t.score)}</strong> de votes
            favorables {filtre ? 'à ce droit' : 'aux droits'}.{/if}
        </p>
        <ul class="votes">
          {#each t.votes as v (v.scrutin.id)}{@render vote(v, t.vu.inverse, t.texte.etat)}{/each}
        </ul>
        {#if t.autres}
          <p class="petit discret">
            <a href="/textes/{t.texte.id}#autres-scrutins"
              >{pluriel(t.autres, 'autre scrutin', 'autres scrutins')} sur ce texte</a
            >, affichés sans être comptés.
          </p>
        {/if}
      </article>
    {/each}
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
  .votes {
    list-style: none;
    padding: 0;
    margin: 0.5rem 0;
  }
  .votes li {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 7rem 11rem 11rem;
    gap: 0.2rem 1rem;
    align-items: baseline;
    max-width: none;
    padding: 0.55rem 0;
    border-bottom: 1px solid var(--filet);
  }
  .position {
    font-weight: 700;
  }
  .lecture.favorable,
  .lecture.defavorable {
    font-weight: 650;
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
  @media (max-width: 46rem) {
    .votes li {
      grid-template-columns: auto 1fr;
    }
    .objet,
    .groupe {
      grid-column: 1 / -1;
    }
  }
</style>
