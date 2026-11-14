<script lang="ts">
  import Regle from '$lib/components/Regle.svelte';
  import Sources from '$lib/components/Sources.svelte';
  import { phrase } from '$lib/droits';
  import { date, etatEnListe, legislature, pluriel } from '$lib/format';
  import { NOM } from '$lib/site';
  import type { Sens } from '$lib/types';

  let { data } = $props();

  // Combien de textes restreignent ce droit, combien l'étendent ; le sélecteur ne garde qu'un sens.
  const restreint = $derived(data.textes.filter((t) => t.droit.sens === 'restreint').length);
  const etend = $derived(data.textes.length - restreint);
  let sens = $state<'' | Sens>('');
  const textes = $derived(data.textes.filter((t) => !sens || t.droit.sens === sens));
  const titreListe = $derived(
    sens === 'restreint'
      ? pluriel(textes.length, 'texte le restreint', 'textes le restreignent')
      : sens === 'etend'
        ? pluriel(textes.length, 'texte l’étend', 'textes l’étendent')
        : pluriel(textes.length, 'texte', 'textes')
  );

  const lignes = (leg: 15 | 16 | 17) =>
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
    content="Votes des groupes et des député·es sur les textes qui touchent à : {data.droit
      .libelle}."
  />
</svelte:head>

<p class="discret"><a href="/droits">Droits</a></p>
<h1>{data.droit.court}</h1>
<p class="chapo">{data.droit.libelle}.</p>

{#if !data.textes.length}
  <p>Aucun texte qualifié ne touche encore ce droit.</p>
{:else}
  <div class="bilan">
    <a class="defavorable" href="#textes" onclick={() => (sens = 'restreint')}
      ><span class="nombre">▼ {restreint}</span>
      {pluriel(
        restreint,
        'texte le restreint',
        'textes le restreignent',
        'aucun texte ne le restreint'
      )}</a
    >
    <a class="favorable" href="#textes" onclick={() => (sens = 'etend')}
      ><span class="nombre">▲ {etend}</span>
      {pluriel(etend, 'texte l’étend', 'textes l’étendent', 'aucun texte ne l’étend')}</a
    >
  </div>
  <h2>Comment votent les groupes</h2>
  <p>
    Sur les {pluriel(data.textes.length, 'texte qui touche', 'textes qui touchent')} ce droit, en principal
    ou en secondaire, chacun avec son propre sens.
  </p>
  {#each [17, 16, 15] as const as leg (leg)}
    {#if data.groupes[leg].length}
      <h3>{legislature(leg)} législature</h3>
      <Regle
        comptes
        lignes={lignes(leg)}
        legende={leg === [17, 16, 15].find((l) => data.groupes[l as 17 | 16 | 15].length)}
      />
    {/if}
  {/each}

  <h2 id="textes">Les textes</h2>
  <div class="sens" role="group" aria-label="Sens">
    <button type="button" aria-pressed={sens === ''} onclick={() => (sens = '')}>Tous</button>
    <button
      type="button"
      class="restreint"
      aria-pressed={sens === 'restreint'}
      onclick={() => (sens = 'restreint')}>▼ Restreignent</button
    >
    <button
      type="button"
      class="etend"
      aria-pressed={sens === 'etend'}
      onclick={() => (sens = 'etend')}>▲ Étendent</button
    >
  </div>
  <p class="discret" role="status">{titreListe}</p>
  {#each textes as t (t.texte.id)}
    <article class="texte {t.droit.sens}">
      <p class="marque">
        {t.droit.sens === 'etend' ? '▲ Étend' : '▼ Restreint'} ce droit, {t.droit.role ===
        'principal'
          ? 'droit principal'
          : 'droit secondaire'}
      </p>
      <h3><a href="/textes/{t.texte.id}">{t.texte.titre}</a></h3>
      <p class="petit discret">
        Voté le {date(t.texte.date)}.
        {#if etatEnListe(t.texte.etat, t.texte.etape)}
          {etatEnListe(t.texte.etat, t.texte.etape)}.
        {/if}
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
  .bilan {
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem;
    margin: 1.5rem 0 0.5rem;
  }
  .bilan a {
    flex: 1 1 14rem;
    display: flex;
    flex-direction: column;
    gap: 0.15rem;
    padding: 0.8rem 1rem;
    border: 1px solid currentColor;
    border-radius: 10px;
    font-weight: 650;
    text-decoration: none;
  }
  .bilan a:hover {
    text-decoration: underline;
  }
  .bilan .nombre {
    font-family: var(--titre);
    font-stretch: 75%;
    font-weight: 800;
    font-size: 2.2rem;
    line-height: 1;
  }
  .sens {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
    margin: 0.75rem 0 0.5rem;
  }
  .sens button {
    font: inherit;
    font-weight: 650;
    white-space: nowrap;
    min-height: 2.75rem;
    padding: 0 clamp(0.6rem, 2.5vw, 1rem);
    border: 1.5px solid var(--filet);
    border-radius: 999px;
    background: var(--papier);
    color: var(--encre);
    cursor: pointer;
  }
  .sens button.restreint {
    color: var(--defavorable);
  }
  .sens button.etend {
    color: var(--favorable);
  }
  .sens button[aria-pressed='true'] {
    border-color: currentColor;
    background: var(--plan);
  }
  .texte {
    border-top: 1px solid var(--filet);
    border-left: 6px solid var(--ardoise);
    margin-top: 1.25rem;
    padding: 0.25rem 0 0 0.9rem;
  }
  .texte.etend {
    border-left-color: var(--favorable);
  }
  .texte.restreint {
    border-left-color: var(--defavorable);
  }
  .marque {
    margin: 0.5rem 0 0;
    font-size: 0.8rem;
    font-weight: 700;
    letter-spacing: 0.05em;
    text-transform: uppercase;
  }
  .etend .marque {
    color: var(--favorable);
  }
  .restreint .marque {
    color: var(--defavorable);
  }
  .texte h3 {
    margin-top: 0.2rem;
  }
  .texte h3 a {
    text-decoration: none;
  }
  .texte h3 a:hover {
    text-decoration: underline;
  }
</style>
