<!--
  Liste des résultats, partagée par le menu de la case d'en-tête (`limites`) et la page /recherche (tout).
  `surLien` ferme le menu au clic. Le motif d'un texte écarté s'affiche dans le résultat : il n'a pas de fiche.
-->
<script lang="ts">
  import type { ResultatCP } from '$lib/charge-recherche';
  import type { Resultats } from '$lib/recherche';
  import { typo } from '$lib/format';
  import type { EntreeIndex } from '$lib/types';

  let {
    r,
    cp = null,
    limites = null,
    compact = false
  }: {
    r: Resultats;
    cp?: ResultatCP | null;
    limites?: { elus: number; pays: number; textes: number; ecartes: number } | null;
    compact?: boolean;
  } = $props();

  const borne = <T,>(l: T[], n: number | undefined) => (n === undefined ? l : l.slice(0, n));
  const qualite = (e: EntreeIndex) =>
    e.senat
      ? e.feminin
        ? e.actuel
          ? 'sénatrice'
          : 'ancienne sénatrice'
        : e.actuel
          ? 'sénateur'
          : 'ancien sénateur'
      : e.feminin
        ? e.actuel
          ? 'députée'
          : 'ancienne députée'
        : e.actuel
          ? 'député'
          : 'ancien député';
</script>

{#snippet elu(e: EntreeIndex)}
  <a class="ligne" data-option href="{e.senat ? '/senat' : '/deputes'}/{e.slug}">
    <span class="titre">{e.nom}</span>
    <span class="detail">
      {#if e.sigle}<span class="sigle" style:--c={e.couleur}>{e.sigle}</span>{/if}
      {qualite(e)}{#if e.departement}, {e.departement}{/if}
    </span>
  </a>
{/snippet}

{#if cp && 'erreur' in cp}
  <p class="vide">{cp.erreur}</p>
{:else if cp}
  <h3>Code postal {cp.cp}</h3>
  {#if cp.circos.length > 1}
    <p class="note">
      Ce code postal couvre {cp.circos.length} circonscriptions. Votre député·e dépend {new Set(
        cp.circos.flatMap((c) => c.communes)
      ).size === 1
        ? 'de votre adresse'
        : 'de votre commune, voire de votre adresse'}.
    </p>
  {/if}
  <ul>
    {#each cp.circos as c (c.id)}
      <li>
        {#if c.depute}
          {@render elu(c.depute)}
        {:else}
          <a class="ligne" data-option href="/circonscriptions/{c.id}">
            <span class="titre">Siège vacant</span>
            <span class="detail">{c.libelle}</span>
          </a>
        {/if}
        {#if cp.circos.length > 1}<p class="note">{c.libelle} : {c.communes.join(', ')}</p>{/if}
      </li>
    {/each}
  </ul>
{/if}

{#if r.elus.length}
  <h3>Élu·es</h3>
  <ul>
    {#each borne(r.elus, limites?.elus) as e (`${e.senat ? 's' : 'd'}-${e.slug}`)}
      <li>{@render elu(e)}</li>
    {/each}
  </ul>
{/if}

{#if r.pays.length}
  <h3>Français établis hors de France</h3>
  <ul>
    {#each borne(r.pays, limites?.pays) as p (p.pays)}
      <li>
        <a
          class="ligne"
          data-option
          href={p.depute ? `/deputes/${p.depute.slug}` : `/circonscriptions/${p.circo}`}
        >
          <span class="titre">{p.pays}</span>
          <span class="detail">
            {#if p.depute}{p.depute.nom},{:else}Siège vacant,{/if}
            {p.libelle}{#if p.hors_tableau && !compact}. Absent du tableau du code électoral,
              rattaché d’après le poste consulaire qui le couvre{/if}
          </span>
        </a>
      </li>
    {/each}
  </ul>
{/if}

{#if r.textes.length}
  <h3>Textes qualifiés</h3>
  <ul>
    {#each borne(r.textes, limites?.textes) as t (t.id)}
      <li>
        <a class="ligne" data-option href={t.url}>
          <span class="titre">{t.titre}</span>
          <span class="detail">{t.detail}</span>
        </a>
      </li>
    {/each}
  </ul>
{/if}

{#if r.ecartes.length}
  <h3>Textes écartés</h3>
  <ul>
    {#each borne(r.ecartes, limites?.ecartes) as e (e.dossier)}
      <li>
        {#if e.url}
          <a class="ligne" data-option href={e.url} rel="external">
            <span class="titre">{e.titre}</span>
            <span class="detail">{typo(e.motif)}</span>
          </a>
        {:else}
          <div class="ligne">
            <span class="titre">{e.titre}</span>
            <span class="detail">{typo(e.motif)}</span>
          </div>
        {/if}
      </li>
    {/each}
  </ul>
{/if}

<style>
  h3 {
    font-family: inherit;
    font-size: 0.8rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: var(--ardoise);
    margin: 0.9rem 0 0.25rem;
  }
  h3:first-child {
    margin-top: 0;
  }
  ul {
    list-style: none;
    padding: 0;
    margin: 0;
  }
  .ligne {
    display: block;
    padding: 0.4rem 0.5rem;
    border-radius: 3px;
    text-decoration: none;
    color: inherit;
  }
  a.ligne:hover,
  a.ligne:focus-visible,
  :global(a.ligne[data-actif='oui']) {
    background: var(--filet);
  }
  .titre {
    display: block;
    font-weight: 650;
    line-height: 1.25;
  }
  .detail {
    display: block;
    font-size: 0.875rem;
    line-height: 1.3;
    color: var(--ardoise);
  }
  .note,
  .vide {
    margin: 0.2rem 0.5rem 0.4rem;
    font-size: 0.875rem;
    color: var(--ardoise);
  }
</style>
