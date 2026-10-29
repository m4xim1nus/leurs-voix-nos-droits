<script lang="ts">
  import Regle from '$lib/components/Regle.svelte';
  import Sources from '$lib/components/Sources.svelte';
  import { phrase } from '$lib/droits';
  import { date, legislature, pluriel } from '$lib/format';
  import { NOM } from '$lib/site';

  let { data } = $props();

  const lignes = (leg: 16 | 17) =>
    data.groupes[leg].map((g) => ({
      cle: g.groupe.id,
      libelle: g.groupe.sigle,
      couleur: g.groupe.couleur,
      href: `/groupes/${g.groupe.slug}`,
      score: g.score.score,
      n_textes: g.score.n_textes
    }));
</script>

<svelte:head>
  <title>{data.droit.court}, {NOM}</title>
  <meta
    name="description"
    content="Votes des groupes et des députés sur les textes qui touchent à : {data.droit.libelle}."
  />
</svelte:head>

<p class="discret"><a href="/droits">Droits</a></p>
<h1>{data.droit.court}</h1>
<p class="chapo">{data.droit.libelle}.</p>

{#if !data.textes.length}
  <p>Aucun texte qualifié ne touche encore ce droit.</p>
{:else}
  <h2>Comment votent les groupes</h2>
  <p>
    Sur les {pluriel(data.textes.length, 'texte qui touche', 'textes qui touchent')} ce droit, en principal
    ou en secondaire, chacun avec son propre sens.
  </p>
  {#each [17, 16] as const as leg (leg)}
    {#if data.groupes[leg].length}
      <h3>{legislature(leg)} législature</h3>
      <Regle lignes={lignes(leg)} legende={leg === 17 || !data.groupes[17].length} />
    {/if}
  {/each}

  <h2>Les textes</h2>
  {#each data.textes as t (t.texte.id)}
    <article class="texte">
      <h3><a href="/textes/{t.texte.id}">{t.texte.titre}</a></h3>
      <p class="petit discret">
        Voté le {date(t.texte.date)}. Droit {t.droit.role === 'principal'
          ? 'principal'
          : 'secondaire'}
        du texte.
      </p>
      <p>
        <strong class={t.droit.sens === 'etend' ? 'favorable' : 'defavorable'}
          >Le texte {phrase(t.droit.code, t.droit.sens)}.</strong
        >
        {t.droit.justification}
      </p>
      <Sources sources={t.sources} />
    </article>
  {/each}
{/if}

<style>
  .texte {
    border-top: 1px solid var(--filet);
    margin-top: 1.25rem;
    padding-top: 0.25rem;
  }
  .texte h3 a {
    text-decoration: none;
  }
  .texte h3 a:hover {
    text-decoration: underline;
  }
</style>
