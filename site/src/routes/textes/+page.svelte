<script lang="ts">
  import TexteLigne from '$lib/components/TexteLigne.svelte';
  import { legislature, pluriel } from '$lib/format';
  import { NOM } from '$lib/site';

  let { data } = $props();

  let droit = $state('');
  let sens = $state('');
  let leg = $state('');
  const textes = $derived(
    data.textes.filter(
      (t) =>
        (!droit || t.droits.some((d) => d.code === droit)) &&
        (!sens || t.principal.sens === sens) &&
        (!leg || String(t.legislature) === leg)
    )
  );
</script>

<svelte:head><title>Textes qualifiés, {NOM}</title></svelte:head>

<h1>Textes qualifiés</h1>
<p class="chapo">
  {pluriel(data.textes.length, 'texte', 'textes', 'Aucun texte')} de loi examinés et qualifiés, du plus
  récent au plus ancien. Le sens indiqué est celui du droit principal de chaque texte.
</p>

<form class="filtres" onsubmit={(e) => e.preventDefault()}>
  <label>
    Droit
    <select bind:value={droit}>
      <option value="">Tous</option>
      {#each data.droits as d (d.code)}<option value={d.code}>{d.court}</option>{/each}
    </select>
  </label>
  <label>
    Sens
    <select bind:value={sens}>
      <option value="">Les deux</option>
      <option value="restreint">Restreint les droits</option>
      <option value="etend">Étend les droits</option>
    </select>
  </label>
  <label>
    Législature
    <select bind:value={leg}>
      <option value="">Les deux</option>
      <option value="17">{legislature(17)}</option>
      <option value="16">{legislature(16)}</option>
    </select>
  </label>
</form>

<p class="discret petit" aria-live="polite">
  {pluriel(textes.length, 'texte affiché', 'textes affichés')}
</p>
{#each textes as t (t.id)}
  <TexteLigne texte={t} />
{/each}

{#if data.ecartes.length}
  <h2>Textes examinés et écartés</h2>
  <p>Ces textes ont été examinés, mais pas qualifiés. Le motif est donné pour chacun.</p>
  <ul>
    {#each data.ecartes as e (e.dossier_an)}
      <li>
        {#if e.url_an}<a href={e.url_an} rel="external">{e.titre}</a>{:else}{e.titre}{/if}
        <span class="discret">: {e.motif}</span>
      </li>
    {/each}
  </ul>
{/if}

<style>
  .filtres {
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem 1.5rem;
    margin: 1.5rem 0 0.5rem;
  }
  label {
    display: flex;
    flex-direction: column;
    font-weight: 650;
    font-size: 0.9rem;
  }
  select {
    font: inherit;
    font-weight: 400;
    font-size: 1rem;
    padding: 0.35rem 0.5rem;
    border: 1.5px solid var(--encre);
    border-radius: 3px;
    background: var(--papier);
    color: var(--encre);
    min-width: 11rem;
  }
</style>
