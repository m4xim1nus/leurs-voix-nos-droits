<script lang="ts">
  import TuilesDroits from '$lib/components/TuilesDroits.svelte';
  import { enLettres } from '$lib/format';
  import { NOM } from '$lib/site';

  let { data } = $props();
</script>

<svelte:head><title>Les droits suivis, {NOM}</title></svelte:head>

<h1>{enLettres(data.droits.length)} droits</h1>
<p class="chapo">
  La grille suit les droits des personnes face à la puissance publique et aux plus forts. Un texte
  touche un droit principal et, souvent, des droits secondaires, chacun dans un sens : il l’étend ou
  il le restreint.
</p>

<p class="legende">
  <span class="defavorable">▼ textes qui restreignent le droit</span>
  <span class="favorable">▲ textes qui l’étendent</span>
</p>
<TuilesDroits droits={data.droits} libelles />

<p class="discret">
  Deux étiquettes transversales complètent la grille : outre-mer, et régimes d’exception (états
  d’urgence, dispositifs temporaires ou expérimentaux, extension du droit antiterroriste). Voir la
  <a href="/methodologie">méthodologie</a>.
</p>

<style>
  .legende {
    display: flex;
    flex-wrap: wrap;
    gap: 0.3rem 1.25rem;
    font-weight: 700;
    margin-top: 1.5rem;
  }
</style>
