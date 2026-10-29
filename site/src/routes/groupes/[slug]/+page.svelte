<script lang="ts">
  import Regle from '$lib/components/Regle.svelte';
  import TexteLigne from '$lib/components/TexteLigne.svelte';
  import { legislature, pluriel, pourcent } from '$lib/format';
  import { NOM } from '$lib/site';

  let { data } = $props();
  const g = $derived(data.groupe);
  const actuels = $derived(data.membres.filter((m) => m.dans_le_groupe));
  const anciens = $derived(data.membres.filter((m) => !m.dans_le_groupe));
</script>

<svelte:head><title>{g.nom} ({g.sigle}), {NOM}</title></svelte:head>

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
  <Regle
    legende={false}
    lignes={data.droits.map((x) => ({
      cle: x.droit.code,
      libelle: x.droit.court,
      href: `/droits/${x.droit.code}`,
      score: x.score.score,
      couleur: g.couleur
    }))}
  />
  <h2>Texte par texte</h2>
  <ul class="textes">
    {#each data.textes as t (t.texte.id)}
      <li>
        <span class="chiffre score">{pourcent(t.score.score)}</span><TexteLigne texte={t.texte} />
      </li>
    {/each}
  </ul>
{:else}
  <p>Aucun vote compté pour ce groupe.</p>
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
    favorables aux droits :
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
  summary {
    cursor: pointer;
    font-weight: 650;
    margin-top: 1rem;
  }
  table {
    max-width: 40rem;
  }
</style>
