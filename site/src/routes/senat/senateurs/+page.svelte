<script lang="ts">
  import { pourcent } from '$lib/format';
  import { NOM } from '$lib/site';

  let { data } = $props();
</script>

<svelte:head>
  <title>Sénateur·ices en poste, {NOM}</title>
  <meta
    name="description"
    content="Les sénateur·ices en poste, par département, et le score de chacun·e d’après les votes enregistrés à son nom."
  />
</svelte:head>

<p class="surtitre">Sénat</p>
<h1>Sénateur·ices en poste, par département</h1>
<p class="chapo">
  Score d’après les votes enregistrés au nom de chacun·e. Un vote enregistré n’est pas une présence
  : aucune fiche n’affiche de taux de participation (<a href="/methodologie#regle-27">règle 27</a>).
  Pour trouver les vôtres, tapez votre code postal ou leur nom dans la case de recherche, en haut de
  la page.
</p>
<nav class="sommaire" aria-label="Départements">
  {#each data.departements as dep (dep.code)}<a href="#dep-{dep.code}">{dep.code}</a>{/each}
</nav>
{#each data.departements as dep (dep.code)}
  <section class="departement" id="dep-{dep.code}">
    <h2>{dep.nom}</h2>
    <ul>
      {#each dep.senateurs as s (s.slug)}
        <li>
          <a href="/senat/{s.slug}">{s.nom}</a>
          <span class="discret petit"
            >{s.sigle}{s.score?.score != null ? `, ${pourcent(s.score.score)}` : ''}</span
          >
        </li>
      {/each}
    </ul>
  </section>
{/each}

<style>
  .sommaire {
    display: flex;
    flex-wrap: wrap;
    gap: 0.25rem 0.6rem;
    margin: 1rem 0 1.5rem;
    font-size: 0.95rem;
  }
  .departement h2 {
    margin: 1.25rem 0 0.25rem;
    font-size: 1.15rem;
  }
  .departement ul {
    list-style: none;
    padding: 0;
    margin: 0 0 1rem;
    columns: 2 16rem;
  }
  .departement {
    scroll-margin-top: 1rem;
  }
</style>
