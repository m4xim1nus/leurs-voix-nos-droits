<script lang="ts">
  import { NOM } from '$lib/site';

  let { data } = $props();
</script>

<svelte:head><title>Circonscriptions, {NOM}</title></svelte:head>

<h1>Les 577 circonscriptions</h1>
<p class="chapo">Par département, puis outre-mer et Français établis hors de France.</p>

<dl>
  {#each data.departements as d (d.nom)}
    <dt id={d.circos[0].id.startsWith('099') ? 'etranger' : undefined}>{d.nom}</dt>
    <dd>
      <!-- L'espace après la virgule est dans une chaîne : en fin de bloc {#if}, Svelte l'ôterait. -->
      {#each d.circos as c, i (c.id)}{i ? ', ' : ''}<a href="/circonscriptions/{c.id}">{c.num}</a
        >{/each}
    </dd>
  {/each}
</dl>

<style>
  dl {
    display: grid;
    grid-template-columns: minmax(8rem, 16rem) minmax(0, 1fr);
    gap: 0.3rem 1rem;
  }
  dt {
    font-weight: 650;
  }
  dd {
    margin: 0;
  }
  /* Sur téléphone, le département au-dessus de ses circonscriptions, qui gardent toute la largeur. */
  @media (max-width: 30rem) {
    dl {
      grid-template-columns: minmax(0, 1fr);
      gap: 0;
    }
    dd {
      margin-bottom: 0.6rem;
    }
  }
</style>
