<script lang="ts">
  import Comparateur from '$lib/components/Comparateur.svelte';
  import { legislature } from '$lib/format';
  import { NOM } from '$lib/site';
</script>

<svelte:head>
  <title>Comparer, {NOM}</title>
  <meta
    name="description"
    content="Comparer les votes de deux député·es ou de deux groupes sur les droits et libertés."
  />
</svelte:head>

<h1>Comparer</h1>
<p class="chapo">
  Deux député·es, deux groupes, ou un·e député·e et son groupe : leurs votes sur les droits, côte à
  côte. Pour le Sénat, voir <a href="/senat/comparer">sa propre page</a>.
</p>

<Comparateur
  source="/comparer/donnees.json"
  prefixeElu="d:"
  lecture={(c) => `sur les textes de la ${legislature(Number(c))} législature, celle de ce groupe`}
/>
