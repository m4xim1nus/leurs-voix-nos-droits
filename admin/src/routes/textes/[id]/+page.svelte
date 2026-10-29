<script lang="ts">
  import Fiche from '$lib/components/Fiche.svelte';

  let { data, form } = $props();
</script>

<svelte:head><title>{data.qualif.doc.id || data.texte.id} · admin</title></svelte:head>

<!-- Une fiche neuve à chaque texte : l'état local ne passe pas d'un texte à l'autre. -->
{#key data.texte.id}
  <Fiche {data} {form} />
{/key}
