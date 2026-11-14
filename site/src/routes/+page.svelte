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
</script>

<svelte:head>
  <title>{NOM} : les votes des député·es sur les droits et libertés</title>
  <meta
    name="description"
    content="Comment les député·es votent sur les textes qui touchent aux droits et libertés : chaque texte qualifié et sourcé, chaque vote vérifiable."
  />
</svelte:head>

<section class="ouverture">
  <h1>Comment votre député·e vote sur vos droits</h1>
  <p class="chapo">
    Chaque texte de loi retenu est qualifié à la main, sources à l’appui : quels droits il touche,
    et s’il les étend ou les restreint. Ses scrutins sont ensuite croisés avec le vote de chaque
    député·e depuis 2017.
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
  <h2>Les groupes de l’Assemblée</h2>
  <p>
    Part des votes favorables aux droits sur les textes qualifiés de la législature, au sens du
    droit principal de chaque texte. Législature en cours (XVIIe, depuis juillet 2024).
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
  <p><a href="/groupes">Les groupes droit par droit</a></p>
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
</style>
