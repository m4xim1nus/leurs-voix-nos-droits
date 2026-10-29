<script lang="ts">
  import Regle from '$lib/components/Regle.svelte';
  import { court, phrase } from '$lib/droits';
  import {
    circonscription,
    date,
    depute as dep,
    legislature,
    pluriel,
    POSITION,
    POSITION_GROUPE,
    pourcent
  } from '$lib/format';
  import type { VoteDepute } from '$lib/server/vues';
  import { NOM, URL_SITE } from '$lib/site';

  let { data } = $props();
  const d = $derived(data.depute);
  const nom = $derived(`${d.prenom} ${d.nom}`);
  const elle = $derived(d.civ === 'Mme');

  function lecture(v: VoteDepute): { texte: string; classe: string } {
    const s = v.scrutin;
    if (!s.compte) return { texte: 'non compté', classe: 'discret' };
    if (v.position === 'pour' || v.position === 'contre')
      return v.position === s.favorable
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

{#snippet vote(v: VoteDepute)}
  {@const l = lecture(v)}
  <li>
    <span class="objet"
      ><a href={v.scrutin.url} rel="external">{v.scrutin.objet}</a>
      <span class="petit discret">{date(v.scrutin.date)}</span></span
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
    Aucun vote compté : {elle ? 'elle' : 'il'} n’a voté sur aucun des scrutins comptés des textes qualifiés
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
  {#if d.courriel}<span class="discret petit">{d.courriel}</span>{/if}
</p>

{#if data.droits.length}
  <section>
    <h2>Droit par droit</h2>
    <Regle
      legende={false}
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
      Chaque scrutin retenu, son vote et ce qu’il signifie pour les droits. Absent ou non-votant :
      hors calcul (règle 17). Abstention : hors calcul aussi, et comptée à part (règle 16).
    </p>
    {#each data.textes as t (t.texte.id)}
      <article class="texte">
        <h3><a href="/textes/{t.texte.id}">{t.texte.titre}</a></h3>
        <p class="petit">
          Le texte {phrase(t.texte.principal.code, t.texte.principal.sens)}.
          {#if t.score?.score !== null && t.score?.score !== undefined}Sur ce texte : <strong
              >{pourcent(t.score.score)}</strong
            > de votes favorables aux droits.{/if}
        </p>
        <ul class="votes">
          {#each t.votes.filter((v) => v.scrutin.compte) as v (v.scrutin.id)}{@render vote(
              v
            )}{/each}
        </ul>
        {#if t.votes.some((v) => !v.scrutin.compte)}
          <details>
            <summary>Autres scrutins du texte, affichés sans être comptés</summary>
            <ul class="votes">
              {#each t.votes.filter((v) => !v.scrutin.compte) as v (v.scrutin.id)}{@render vote(
                  v
                )}{/each}
            </ul>
          </details>
        {/if}
      </article>
    {/each}
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
          ({g.qualite.toLowerCase()}) : du {date(g.debut)}{#if g.fin}
            au {date(g.fin)}{/if}.
        </li>
      {/each}
    </ul>
    <p class="petit discret">Chaque vote compte pour le groupe du jour du vote (règle 19).</p>
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
    align-items: baseline;
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
  details summary {
    cursor: pointer;
    font-size: 0.95rem;
    color: var(--ardoise);
    margin-top: 0.5rem;
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
