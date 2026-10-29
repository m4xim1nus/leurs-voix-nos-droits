<script lang="ts">
  // Positions de groupe sur un scrutin (règle 12) : sigle, position majoritaire parmi les exprimés,
  // cohésion. Le détail du décompte est dans l'infobulle.
  import { couleur, LIBELLES_POSITION, pourcent } from '$lib/format';
  import type { Groupe, PositionGroupe } from '$lib/types';

  let {
    positions,
    groupes,
    favorable = null
  }: {
    positions: PositionGroupe[];
    groupes: Map<string, Groupe>;
    favorable?: 'pour' | 'contre' | null;
  } = $props();

  const tries = $derived([...positions].sort((a, b) => b[1] + b[2] + b[3] - (a[1] + a[2] + a[3])));
</script>

<ul class="positions">
  {#each tries as [g, pour, contre, abst, nv, position, cohesion] (g)}
    {@const gr = groupes.get(g)}
    <li
      class={position}
      class:favorable={favorable && position === favorable}
      class:defavorable={favorable &&
        (position === 'pour' || position === 'contre') &&
        position !== favorable}
      style:--couleur={couleur(gr)}
      title="{gr?.nom ??
        g} : {pour} pour, {contre} contre, {abst} abstention(s), {nv} non-votant(s)"
    >
      <b>{gr?.sigle ?? g}</b>
      {LIBELLES_POSITION[position] ?? position}
      {#if cohesion != null && position !== 'absent'}<small>{pourcent(cohesion)}</small>{/if}
    </li>
  {/each}
</ul>

<style>
  .positions {
    list-style: none;
    margin: 0.2rem 0 0;
    padding: 0;
    display: flex;
    flex-wrap: wrap;
    gap: 0.2rem;
  }
  li {
    font-size: 0.78rem;
    border: 1px solid var(--bord);
    border-left: 4px solid var(--couleur);
    border-radius: 4px;
    padding: 0 0.3rem;
    white-space: nowrap;
    background: var(--surface);
  }
  li.absent,
  li.abstention,
  li.partage {
    color: var(--texte-2);
  }
  li.favorable {
    background: var(--ok-fond);
  }
  li.defavorable {
    background: var(--erreur-fond);
  }
  small {
    color: var(--texte-2);
  }
</style>
