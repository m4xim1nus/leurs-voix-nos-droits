<script lang="ts">
  import Recherche from '$lib/components/Recherche.svelte';
  import Regle from '$lib/components/Regle.svelte';
  import TexteLigne from '$lib/components/TexteLigne.svelte';
  import { enLettres, pluriel } from '$lib/format';
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
  <title>{NOM} : les votes des députés sur les droits et libertés</title>
  <meta
    name="description"
    content="Comment les députés votent sur les textes qui touchent aux droits et libertés : chaque texte qualifié et sourcé, chaque vote vérifiable."
  />
</svelte:head>

<section class="ouverture">
  <h1>Comment votre député vote sur vos droits</h1>
  <p class="chapo">
    Chaque texte de loi retenu est qualifié à la main, sources à l’appui : quels droits il touche,
    et s’il les étend ou les restreint. Ses scrutins sont ensuite croisés avec le vote de chaque
    député depuis 2022.
  </p>
  <div class="cherche">
    <Recherche grand />
  </div>
</section>

<section>
  <h2>Les groupes de l’Assemblée</h2>
  <p>
    Part des votes favorables aux droits sur les {pluriel(
      data.n_textes,
      'texte qualifié',
      'textes qualifiés'
    )}, au sens du droit principal de chaque texte. Législature en cours (XVIIe, depuis juillet
    2024).
  </p>
  <Regle lignes={lignes(17)} />
  <details>
    <summary>XVIe législature (2022-2024)</summary>
    <Regle lignes={lignes(16)} legende={false} />
  </details>
  <p><a href="/groupes">Les groupes droit par droit</a></p>
</section>

<section>
  <h2>{enLettres(data.droits.length)} droits</h2>
  <ul class="droits">
    {#each data.droits as d (d.code)}
      <li>
        <a href="/droits/{d.code}">
          <span class="court">{d.court}</span>
          <span class="discret petit">{pluriel(d.n_textes, 'texte')}</span>
        </a>
      </li>
    {/each}
  </ul>
</section>

<section>
  <h2>Derniers textes qualifiés</h2>
  {#each data.derniers as t (t.id)}
    <TexteLigne texte={t} />
  {/each}
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
  details summary {
    cursor: pointer;
    font-weight: 650;
  }
  .droits {
    list-style: none;
    padding: 0;
    margin: 0;
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(18rem, 1fr));
    gap: 0 2rem;
    border-top: 1px solid var(--filet);
  }
  .droits li {
    max-width: none;
    border-bottom: 1px solid var(--filet);
  }
  .droits a {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: 1rem;
    padding: 0.7rem 0.25rem;
    text-decoration: none;
  }
  .droits .court {
    font-family: var(--titre);
    font-stretch: 78%;
    font-weight: 750;
    font-size: 1.3rem;
  }
  .droits a:hover .court {
    text-decoration: underline;
  }
</style>
