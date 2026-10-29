<script lang="ts">
  import { legislature, pourcent } from '$lib/format';
  import { NOM } from '$lib/site';

  let { data } = $props();
  // Cellule : teinte proportionnelle à l'écart à 50 %, dans la couleur du côté où penche le score.
  const fond = (s: number | null) =>
    s === null
      ? 'transparent'
      : `color-mix(in srgb, var(${s >= 50 ? '--favorable' : '--defavorable'}) ${Math.round(Math.abs(s - 50) * 1.1)}%, var(--papier))`;
</script>

<svelte:head><title>Les groupes, {NOM}</title></svelte:head>

<h1>Les groupes, droit par droit</h1>
<p class="chapo">
  Part des votes favorables aux droits de chaque groupe, sur chaque droit. Un vote compte pour le
  groupe où siégeait le député ce jour-là ; un groupe qui a changé de nom est réuni sous son nom le
  plus récent.
</p>

{#each [17, 16] as const as leg (leg)}
  <h2>{legislature(leg)} législature</h2>
  <div class="defile">
    <table>
      <thead>
        <tr>
          <th scope="col">Groupe</th>
          <th scope="col" class="nombre">Ensemble</th>
          {#each data.droits as d (d.code)}<th scope="col" class="nombre"
              ><a href="/droits/{d.code}">{d.court}</a></th
            >{/each}
        </tr>
      </thead>
      <tbody>
        {#each data.legislatures[leg] as g (g.groupe.id)}
          <tr>
            <th scope="row"
              ><a
                class="sigle"
                style:--c={g.groupe.couleur}
                href="/groupes/{g.groupe.slug}"
                title={g.groupe.nom}>{g.groupe.sigle}</a
              ></th
            >
            <td class="nombre fort" style:background={fond(g.global?.score ?? null)}
              >{pourcent(g.global?.score ?? null)}</td
            >
            {#each data.droits as d (d.code)}
              {@const s = g.droits[d.code]}
              <td
                class="nombre"
                style:background={fond(s?.score ?? null)}
                title={s ? `${s.n_textes} texte(s)` : 'aucun texte'}
                >{s ? pourcent(s.score) : ''}</td
              >
            {/each}
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
{/each}
<p class="petit discret">
  Case vide : aucun texte qualifié ne touche ce droit sur la législature. Survolez une case pour le
  nombre de textes.
</p>

<style>
  th a {
    color: inherit;
  }
  thead th {
    vertical-align: bottom;
    min-width: 5.5rem;
  }
  th[scope='row'] {
    font-size: inherit;
  }
  th[scope='row'] a {
    text-decoration: none;
  }
  td.fort {
    font-weight: 750;
  }
</style>
