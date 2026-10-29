<script lang="ts">
  import Regle from '$lib/components/Regle.svelte';
  import TexteLigne from '$lib/components/TexteLigne.svelte';
  import { court, scoreSousAngle, sousAngle } from '$lib/droits';
  import { date, legislature, pluriel, POSITION_GROUPE, pourcent } from '$lib/format';
  import { NOM, URL_SITE } from '$lib/site';

  let { data } = $props();
  const g = $derived(data.groupe);
  const actuels = $derived(data.membres.filter((m) => m.dans_le_groupe));
  const anciens = $derived(data.membres.filter((m) => !m.dans_le_groupe));

  // Un clic sur un droit de la règle ne garde que ses textes, vus sous l'angle de ce droit.
  let filtre = $state<string | null>(null);
  const textes = $derived(
    data.textes.flatMap((t) => {
      if (filtre && !t.texte.droits.some((x) => x.code === filtre)) return [];
      return [{ ...t, score: scoreSousAngle(t.score.score, sousAngle(t.texte, filtre).inverse) }];
    })
  );
</script>

<svelte:head>
  <title>{g.nom} ({g.sigle}), {NOM}</title>
  <meta property="og:title" content="{g.nom} ({g.sigle})" />
  <meta property="og:image" content="{URL_SITE}/cartes/groupes/{g.slug}.png" />
  <meta name="twitter:card" content="summary_large_image" />
</svelte:head>

<p class="discret"><a href="/groupes">Groupes</a>, {legislature(g.legislature)} législature</p>
<h1><span class="sigle" style:--c={g.couleur}>{g.sigle}</span></h1>
<p class="chapo">
  {g.nom}{#if !g.actif}
    (groupe dissous ou renommé){/if}.
</p>

{#if data.global}
  <p class="grand chiffre">{pourcent(data.global.score)}</p>
  <p>
    de votes favorables aux droits, sur {pluriel(
      data.global.n_textes,
      'texte qualifié',
      'textes qualifiés'
    )}
    ({data.global.favorables} votes favorables, {data.global.defavorables} défavorables, {pluriel(
      data.global.abstentions,
      'abstention'
    )}
    hors calcul).
  </p>
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
      couleur: g.couleur
    }))}
  />
  <h2>Texte par texte</h2>
  {#if filtre}
    <p class="filtre" role="status">
      <span
        >{pluriel(textes.length, 'texte touche', 'textes touchent')} à
        <strong>{court(filtre)}</strong>.</span
      >
      <button type="button" onclick={() => (filtre = null)}>Tous les textes</button>
      <a href="/droits/{filtre}">{court(filtre)} : tous les groupes</a>
    </p>
  {/if}
  <ul class="textes">
    {#each textes as t (t.texte.id)}
      <li>
        <span class="chiffre score">{pourcent(t.score)}</span><TexteLigne
          texte={t.texte}
          droit={filtre}
        />
      </li>
    {/each}
  </ul>
{:else}
  <p>Aucun vote compté pour ce groupe.</p>
{/if}

{#if data.unanimes.length}
  <h2>Textes adoptés sans opposition</h2>
  <p>
    Adoptés sans aucune voix contre, ces textes ne distinguent aucun groupe : ils ne sont ni
    qualifiés ni comptés. Le groupe a voté pour {data.unanimes.filter((u) => u.position === 'pour')
      .length} des
    {data.unanimes.length} textes de sa législature.
  </p>
  <details>
    <summary>{pluriel(data.unanimes.length, 'texte', 'textes')} et sa position</summary>
    <ul>
      {#each data.unanimes as u (u.url)}
        <li>
          <a href={u.url} rel="external">{u.titre}</a>
          <span class="discret petit">{date(u.date)}</span> :
          <strong>{POSITION_GROUPE[u.position]}</strong>
        </li>
      {/each}
    </ul>
  </details>
{/if}

<h2>Membres</h2>
{#snippet liste(ms: typeof data.membres)}
  <div class="defile">
    <table>
      <tbody>
        {#each ms as m (m.slug)}
          <tr>
            <td><a href="/deputes/{m.slug}">{m.nom}</a></td>
            <td class="discret">{m.departement}</td>
            <td class="nombre">{m.score ? pourcent(m.score.score) : ''}</td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
{/snippet}
{#if actuels.length}
  <p>
    {pluriel(actuels.length, 'membre actuel', 'membres actuels')}, avec leur part de votes
    favorables aux droits :
  </p>
  {@render liste(actuels)}
{/if}
{#if anciens.length}
  <details>
    <summary>{pluriel(anciens.length, 'ancien membre', 'anciens membres')}</summary>
    {@render liste(anciens)}
  </details>
{/if}

<style>
  h1 {
    font-size: clamp(3rem, 10vw, 5rem);
  }
  .grand {
    font-size: clamp(4rem, 14vw, 7rem);
    line-height: 0.9;
    margin: 1.5rem 0 0.25rem;
  }
  .textes {
    list-style: none;
    padding: 0;
  }
  .textes li {
    display: grid;
    grid-template-columns: 4rem 1fr;
    align-items: center;
    max-width: none;
  }
  .score {
    font-size: 1.5rem;
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
  summary {
    cursor: pointer;
    font-weight: 650;
    margin-top: 1rem;
  }
  table {
    max-width: 40rem;
  }
</style>
