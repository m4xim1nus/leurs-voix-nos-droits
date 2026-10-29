<script lang="ts">
  import { circonscription, date, legislature, pourcent } from '$lib/format';
  import { NOM } from '$lib/site';

  let { data } = $props();
  const titre = $derived(`${data.departement}, ${circonscription(data.num)}`);
</script>

<svelte:head><title>{titre}, {NOM}</title></svelte:head>

<h1>{titre}</h1>
{#if !data.actuel}
  <p class="chapo">Siège vacant : aucun député n’y siège aujourd’hui.</p>
{/if}

<h2>Députés depuis 2022</h2>
<ul class="mandats">
  {#each data.mandats as m, i (i)}
    <li class:actuel={m === data.actuel}>
      <a href="/deputes/{m.depute.slug}">{m.depute.nom}</a>
      <span class="sigle" style:--c={m.depute.couleur}>{m.depute.sigle}</span>
      <span class="discret">
        {legislature(m.legislature)} législature, du {date(m.debut)}{#if m.fin}
          au {date(m.fin)}{:else}, en cours{/if}.
        {#if m.score}{pourcent(m.score.score)} de votes favorables aux droits.{/if}
      </span>
    </li>
  {/each}
</ul>

<style>
  .mandats {
    list-style: none;
    padding: 0;
  }
  .mandats li {
    padding: 0.6rem 0;
    border-bottom: 1px solid var(--filet);
  }
  .mandats a {
    font-weight: 700;
    font-size: 1.1rem;
    margin-right: 0.4rem;
  }
  .actuel a {
    font-size: 1.35rem;
  }
</style>
