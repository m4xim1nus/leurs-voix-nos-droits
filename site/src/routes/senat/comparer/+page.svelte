<script lang="ts">
  import Comparateur from '$lib/components/Comparateur.svelte';
  import { NOM } from '$lib/site';

  const periodes: Record<string, string> = {
    'depuis-2022': 'depuis juin 2022',
    '2017-2022': 'de juin 2017 à juin 2022'
  };
</script>

<svelte:head>
  <title>Comparer au Sénat, {NOM}</title>
  <meta
    name="description"
    content="Comparer les votes enregistrés au nom de deux sénateur·ices, ou de deux groupes du Sénat, sur les droits et libertés."
  />
</svelte:head>

<p class="discret"><a href="/senat">Sénat</a></p>
<h1>Comparer au Sénat</h1>
<p class="chapo">
  Deux sénateur·ices, deux groupes, ou un·e sénateur·ice et son groupe : les votes enregistrés à
  leur nom sur les droits, côte à côte. Un score du Sénat ne se compare pas à un score de
  l’Assemblée : les textes comptés diffèrent (<a href="/methodologie#regle-28">règle 28</a>).
</p>

<Comparateur
  source="/senat/comparer/donnees.json"
  prefixeElu="s:"
  lecture={(c) =>
    `sur les textes dont le vote décisif date ${periodes[String(c)] ?? ''}, la période de ce groupe`}
>
  {#snippet mention()}
    Un vote enregistré ne dit pas qui était présent : voir le
    <a href="/methodologie#regle-27">vote de groupe</a>.
  {/snippet}
</Comparateur>
