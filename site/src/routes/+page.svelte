<script lang="ts">
  import Recherche from '$lib/components/Recherche.svelte';
  import Regle from '$lib/components/Regle.svelte';
  import TexteCarte from '$lib/components/TexteCarte.svelte';
  import TuilesDroits from '$lib/components/TuilesDroits.svelte';
  import { enLettres, pluriel } from '$lib/format';
  import { NOM } from '$lib/site';

  let { data } = $props();

  const lignes = (leg: 15 | 16 | 17) =>
    data.groupes[leg].map((g) => ({
      cle: g.groupe.id,
      libelle: g.groupe.sigle,
      couleur: g.groupe.couleur,
      href: `/groupes/${g.groupe.slug}`,
      score: g.score.score,
      n_textes: g.score.n_textes
    }));
  // Les deux chambres, une à la fois : leurs scores ne se comparent pas (règle 28).
  let chambre = $state<'an' | 'senat'>('an');
  const lignesSenat = $derived(
    (data.senat?.groupes ?? []).map((g) => ({
      cle: g.id,
      libelle: g.sigle,
      couleur: g.couleur,
      href: '/senat',
      score: g.score,
      n_textes: g.n_textes
    }))
  );
</script>

<svelte:head>
  <title>{NOM} : les votes des député·es sur les droits et libertés</title>
  <meta
    name="description"
    content="Comment les député·es votent sur les textes qui touchent aux droits et libertés : chaque texte qualifié et sourcé, chaque vote vérifiable."
  />
</svelte:head>

<section class="ouverture">
  <h1>Comment vos élu·es votent sur vos droits</h1>
  <p class="chapo">
    Chaque texte de loi retenu est qualifié à la main, sources à l’appui : quels droits il touche,
    et s’il les étend ou les restreint. Ses scrutins sont ensuite croisés avec le vote de chaque
    député·e et de chaque sénateur·ice depuis 2017, chaque chambre à part.
  </p>
  <div class="cherche">
    <Recherche grand />
  </div>
</section>

{#if data.enCours.total}
  <p class="encart">
    <a href="/en-cours">{pluriel(data.enCours.total, 'texte en cours', 'textes en cours')}</a> :
    déjà votés, pas encore des lois{data.enCours.inscrits
      ? `, dont ${pluriel(data.enCours.inscrits, 'inscrit', 'inscrits')} à l’ordre du jour`
      : ''}.
  </p>
{/if}

<section>
  <div class="entete-groupes">
    <h2>Les groupes</h2>
    {#if data.senat}
      <div class="chambres" role="group" aria-label="Chambre">
        <button type="button" aria-pressed={chambre === 'an'} onclick={() => (chambre = 'an')}
          >Assemblée nationale</button
        >
        <button type="button" aria-pressed={chambre === 'senat'} onclick={() => (chambre = 'senat')}
          >Sénat</button
        >
      </div>
    {/if}
  </div>
  {#if chambre === 'senat' && data.senat}
    <p>
      Part des votes favorables aux droits des groupes du Sénat, {data.senat.libelle} :
      {pluriel(data.senat.n_textes, 'vote décisif compté', 'votes décisifs comptés')}. Un vote
      enregistré au nom d’un·e sénateur·ice n’est pas une présence.
    </p>
    <p class="petit discret">
      Chaque chambre a son propre calcul : les scores ne se comparent pas d’une chambre à l’autre.
    </p>
    <Regle comptes lignes={lignesSenat} />
    <p><a href="/senat">Les groupes du Sénat, droit par droit</a></p>
  {:else}
    <p>
      Part des votes favorables aux droits sur les textes qualifiés de la législature, au sens du
      droit principal de chaque texte. Législature en cours (XVIIe, depuis juillet 2024).
    </p>
    <p class="petit discret">
      Chaque chambre a son propre calcul : les scores ne se comparent pas d’une chambre à l’autre.
    </p>
    <Regle comptes lignes={lignes(17)} />
    <details>
      <summary>XVIe législature (2022-2024)</summary>
      <Regle comptes lignes={lignes(16)} legende={false} />
    </details>
    {#if lignes(15).length}
      <details>
        <summary>XVe législature (2017-2022)</summary>
        <Regle comptes lignes={lignes(15)} legende={false} />
      </details>
    {/if}
    <p><a href="/groupes">Les groupes de l’Assemblée, droit par droit</a></p>
  {/if}
</section>

<section>
  <h2>{enLettres(data.droits.length)} droits</h2>
  <TuilesDroits droits={data.droits} />
</section>

<section>
  <h2>Derniers textes qualifiés</h2>
  <ul class="cartes">
    {#each data.derniers as t (t.id)}
      <li><TexteCarte texte={t} /></li>
    {/each}
  </ul>
  <p><a href="/textes">Tous les textes</a></p>
</section>

<style>
  .ouverture {
    padding: 1rem 0 2.5rem;
    border-bottom: 1px solid var(--filet);
  }
  .ouverture h1 {
    font-size: clamp(2.8rem, 9vw, 5.5rem);
    font-stretch: 64%;
    max-width: 14ch;
    margin-bottom: 1.25rem;
  }
  .cherche {
    margin-top: 2rem;
  }
  .encart {
    max-width: none;
    margin: 1.25rem 0 0;
    padding: 0.6rem 0.8rem;
    background: var(--plan);
    border-radius: 3px;
    font-weight: 600;
  }
  details summary {
    cursor: pointer;
    font-weight: 650;
  }
  .cartes {
    list-style: none;
    padding: 0;
    margin: 0 0 1rem;
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(min(100%, 28rem), 1fr));
    gap: 0.75rem;
  }
  .cartes li {
    display: flex;
    max-width: none;
  }
  .cartes li > :global(a) {
    flex: 1;
  }
  .entete-groupes {
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    justify-content: space-between;
    gap: 0.75rem;
  }
  .chambres {
    display: inline-flex;
    gap: 3px;
    padding: 3px;
    border: 2px solid var(--encre);
    border-radius: 999px;
  }
  .chambres button {
    font: inherit;
    font-weight: 700;
    min-height: 2.75rem;
    padding: 0 clamp(0.7rem, 3vw, 1.1rem);
    white-space: nowrap;
    border: 0;
    border-radius: 999px;
    background: transparent;
    color: var(--encre);
    cursor: pointer;
  }
  .chambres button[aria-pressed='true'] {
    background: var(--encre);
    color: var(--papier);
  }
</style>
