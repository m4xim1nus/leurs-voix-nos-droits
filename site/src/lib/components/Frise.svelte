<script lang="ts">
  /*
    Frise du parcours d'un texte : une liste ordonnée, lisible sans le dessin (le trait et les pastilles
    sont décoratifs). Verticale, donc à l'aise à 375 px. La forme de la pastille dit le statut (plein :
    fait ; croix : bloqué ; creux : à venir), pas seulement la couleur.
  */
  import { date } from '$lib/format';
  import { resumeFrise, type PointFrise } from '$lib/frise';

  let { points }: { points: PointFrise[] } = $props();
</script>

{#if points.length}
  <section class="frise" aria-labelledby="parcours">
    <h2 id="parcours">Le parcours du texte</h2>
    <p class="visuellement-cache">{resumeFrise(points)}</p>
    <ol>
      {#each points as p (p.cle)}
        <li class={[p.statut, p.lieu && `lieu-${p.lieu}`]}>
          <span class="pastille" aria-hidden="true">{p.statut === 'bloque' ? '×' : ''}</span>
          <div class="corps">
            <p class="titre-etape">
              {p.titre}
              {#if p.groupe}<span class="sigle" style:--c={p.groupe.couleur} title={p.groupe.nom}
                  >{p.groupe.sigle}</span
                >{/if}
            </p>
            {#if p.resultat}<p class="resultat-etape">{p.resultat}</p>{/if}
            {#if p.decompte}<p class="decompte">Vote décisif : {p.decompte}</p>{/if}
            {#if p.date}<p class="petit discret">
                <time datetime={p.date}>{date(p.date)}</time>
              </p>{/if}
            {#if p.precision}<p class="petit discret">{p.precision}</p>{/if}
            {#if p.lien}<p class="petit">
                <a href={p.lien.href} rel={p.lien.href.startsWith('/') ? undefined : 'external'}
                  >{p.lien.texte}</a
                >
              </p>{/if}
          </div>
        </li>
      {/each}
    </ol>
    <p class="petit discret">
      Étapes datées par l’open data de l’Assemblée nationale. Le groupe affiché est celui de
      l’auteur·ice à la date du dépôt.
    </p>
  </section>
{/if}

<style>
  .frise ol {
    list-style: none;
    margin: 0.75rem 0;
    padding: 0;
    max-width: 42rem;
  }
  li {
    position: relative;
    display: flex;
    gap: 0.9rem;
    margin: 0;
    max-width: none;
    padding-bottom: 1.1rem;
  }
  /* Le trait qui relie les pastilles. */
  li:not(:last-child)::before {
    content: '';
    position: absolute;
    left: 0.6rem;
    top: 1.3rem;
    bottom: 0;
    width: 2px;
    background: var(--filet);
  }
  li.attente:not(:last-child)::before {
    background: repeating-linear-gradient(var(--filet) 0 4px, transparent 4px 8px);
  }
  .pastille {
    flex: none;
    box-sizing: border-box;
    width: 1.3rem;
    height: 1.3rem;
    border-radius: 50%;
    background: var(--ardoise);
    color: var(--papier);
    font-weight: 800;
    font-size: 0.9rem;
    line-height: 1.15rem;
    text-align: center;
  }
  .lieu-AN .pastille {
    background: var(--favorable);
  }
  .lieu-SN .pastille {
    background: var(--encre);
  }
  .lieu-GOUV .pastille {
    background: var(--ardoise);
  }
  .attente .pastille {
    background: var(--papier);
    border: 2px dashed var(--ardoise);
  }
  .bloque .pastille {
    background: var(--defavorable);
  }
  .corps {
    min-width: 0;
  }
  .corps p {
    margin: 0;
  }
  .titre-etape {
    font-family: var(--titre);
    font-weight: 800;
    font-stretch: 75%;
    font-size: 1.05rem;
    line-height: 1.25;
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    gap: 0.1rem 0.6rem;
  }
  .titre-etape .sigle {
    font-family: var(--texte);
    font-size: 0.85rem;
    font-stretch: 100%;
  }
  .resultat-etape {
    font-weight: 650;
  }
  .decompte {
    margin-top: 0.15rem;
    font-variant-numeric: tabular-nums;
  }
  .bloque .resultat-etape,
  .bloque .titre-etape {
    color: var(--defavorable);
  }
</style>
