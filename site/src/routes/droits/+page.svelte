<script lang="ts">
  import { pluriel } from '$lib/format';
  import { NOM } from '$lib/site';

  let { data } = $props();
</script>

<svelte:head><title>Les droits suivis, {NOM}</title></svelte:head>

<h1>Onze droits</h1>
<p class="chapo">
  La grille suit les droits des personnes face à la puissance publique et aux plus forts. Un texte
  touche un droit principal et, souvent, des droits secondaires, chacun dans un sens : il l’étend ou
  il le restreint.
</p>

<ul class="liste">
  {#each data.droits as d (d.code)}
    <li>
      <h2><a href="/droits/{d.code}">{d.court}</a></h2>
      <p>
        {d.libelle}.
        <span class="discret">{pluriel(d.n_textes, 'texte qualifié', 'textes qualifiés')}.</span>
      </p>
    </li>
  {/each}
</ul>

<p class="discret">
  Deux étiquettes transversales complètent la grille : outre-mer, et régimes d’exception (états
  d’urgence, dispositifs temporaires ou expérimentaux, extension du droit antiterroriste). Voir la
  <a href="/methodologie">méthodologie</a>.
</p>

<style>
  .liste {
    list-style: none;
    padding: 0;
  }
  .liste h2 {
    font-size: 1.6rem;
    margin: 1.5rem 0 0.25rem;
  }
  .liste h2 a {
    text-decoration: none;
  }
  .liste h2 a:hover {
    text-decoration: underline;
  }
</style>
