<!-- Position de chaque groupe sur un scrutin : majorité des exprimés et cohésion (règle 12). -->
<script lang="ts">
  import { entier, POSITION_GROUPE } from '$lib/format';
  import type { Ventilation } from '$lib/types';

  let {
    ventilations,
    favorable,
    censure = false
  }: {
    ventilations: Ventilation[];
    favorable: 'pour' | 'contre' | null;
    /** Motion de censure : seules les voix pour sont enregistrées, ni position ni cohésion. */
    censure?: boolean;
  } = $props();

  const presents = $derived(
    ventilations.filter((v) => v.pour + v.contre + v.abstention + v.non_votants > 0)
  );
  const absents = $derived(
    ventilations.filter((v) => v.pour + v.contre + v.abstention + v.non_votants === 0)
  );
  const classe = (p: string) =>
    favorable && (p === 'pour' || p === 'contre')
      ? p === favorable
        ? 'favorable'
        : 'defavorable'
      : '';
</script>

<div class="defile">
  <table>
    <thead>
      <tr>
        <th scope="col">Groupe</th>
        {#if censure}
          <th scope="col" class="nombre">Membres</th>
          <th scope="col" class="nombre">Voix pour la censure</th>
        {:else}
          <th scope="col">Position</th>
          <th scope="col" class="nombre">Cohésion</th>
          <th scope="col" class="nombre">Pour</th>
          <th scope="col" class="nombre">Contre</th>
          <th scope="col" class="nombre">Abst.</th>
        {/if}
      </tr>
    </thead>
    <tbody>
      {#each presents as v (v.groupe.id)}
        <tr>
          <th scope="row"
            ><span class="sigle" style:--c={v.groupe.couleur} title={v.groupe.nom}
              >{v.groupe.sigle}</span
            ></th
          >
          {#if censure}
            <td class="nombre">{v.membres}</td>
            <td class="nombre">{v.pour}</td>
          {:else}
            <td class={classe(v.position)}>{POSITION_GROUPE[v.position]}</td>
            <td class="nombre">{v.cohesion === null ? '–' : `${entier(v.cohesion * 100)} %`}</td>
            <td class="nombre">{v.pour}</td>
            <td class="nombre">{v.contre}</td>
            <td class="nombre">{v.abstention}</td>
          {/if}
        </tr>
      {/each}
    </tbody>
  </table>
</div>
{#if absents.length}
  <p class="petit discret">
    {censure ? 'Aucune voix pour la censure' : 'Aucun votant'} : {absents
      .map((v) => v.groupe.sigle)
      .join(', ')}.
  </p>
{/if}

<style>
  table {
    font-size: 0.93rem;
    margin: 0.5rem 0;
    max-width: 42rem;
  }
  th[scope='row'] {
    color: var(--encre);
    font-size: inherit;
  }
  td.favorable,
  td.defavorable {
    font-weight: 650;
  }
</style>
