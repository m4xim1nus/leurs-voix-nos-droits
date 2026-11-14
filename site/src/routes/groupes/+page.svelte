<script lang="ts">
  import Regle from '$lib/components/Regle.svelte';
  import { legislature, pourcent } from '$lib/format';
  import { NOM } from '$lib/site';

  let { data } = $props();
  // Cellule : teinte proportionnelle à l'écart à 50 %, dans la couleur du côté où penche le score.
  const fond = (s: number | null) =>
    s === null
      ? 'transparent'
      : `color-mix(in srgb, var(${s >= 50 ? '--favorable' : '--defavorable'}) ${Math.round(Math.abs(s - 50) * 1.1)}%, var(--papier))`;

  // Vue d'abord lisible : un droit (ou l'ensemble) et une législature à la fois, groupes classés.
  // Le tableau complet reste dessous, replié.
  const LEGS = [17, 16, 15] as const;
  let leg = $state<17 | 16 | 15>(17);
  let droit = $state('');
  const libelleDroit = $derived(data.droits.find((d) => d.code === droit)?.court ?? null);
  const lignes = $derived(
    data.legislatures[leg]
      .map((g) => {
        const s = droit ? g.droits[droit] : g.global;
        return {
          cle: g.groupe.id,
          libelle: g.groupe.sigle,
          couleur: g.groupe.couleur,
          href: `/groupes/${g.groupe.slug}`,
          score: s?.score ?? null,
          n_textes: s?.n_textes ?? 0
        };
      })
      .filter((l) => l.n_textes > 0)
      .sort((a, b) => (b.score ?? -1) - (a.score ?? -1))
  );
</script>

<svelte:head><title>Les groupes, {NOM}</title></svelte:head>

<p class="surtitre">Assemblée nationale</p>
<h1>Les groupes, droit par droit</h1>
<p class="chapo">
  Part des votes favorables aux droits de chaque groupe, sur chaque droit. Un vote compte pour le
  groupe où siégeait l’élu·e ce jour-là ; un groupe qui a changé de nom est réuni sous son nom le
  plus récent. Le calcul est propre à l’Assemblée : ces scores ne se comparent pas à ceux du
  <a href="/senat">Sénat</a>.
</p>

<div class="choix">
  <div class="rangee" role="group" aria-label="Législature">
    {#each LEGS as l (l)}
      {#if data.legislatures[l].length}
        <button type="button" aria-pressed={leg === l} onclick={() => (leg = l)}
          >{legislature(l)}</button
        >
      {/if}
    {/each}
  </div>
  <label class="droit"
    >Droit
    <select bind:value={droit}>
      <option value="">Tous les droits</option>
      {#each data.droits as d (d.code)}<option value={d.code}>{d.court}</option>{/each}
    </select></label
  >
</div>

<h2 aria-live="polite">
  {libelleDroit ?? 'Tous les droits'}, {legislature(leg)} législature
</h2>
{#if lignes.length}
  <Regle comptes {lignes} />
  {#if droit}
    <p><a href="/droits/{droit}">{libelleDroit} : les textes et leurs sources</a></p>
  {/if}
{:else}
  <p>Aucun texte qualifié ne touche ce droit sur cette législature.</p>
{/if}

<details class="complet">
  <summary>Le tableau complet : tous les groupes, tous les droits</summary>
  {#each LEGS as leg (leg)}
    {#if data.legislatures[leg].length}
      <h3>{legislature(leg)} législature</h3>
      <div class="defile">
        <table>
          <thead>
            <tr>
              <th scope="col">Groupe</th>
              <th scope="col" class="nombre">Ensemble</th>
              <th scope="col" class="nombre">Textes</th>
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
                <td class="nombre">{g.global?.n_textes ?? ''}</td>
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
    {/if}
  {/each}
  <p class="petit discret">
    Case vide : aucun texte qualifié ne touche ce droit sur la législature. Survolez une case pour
    le nombre de textes.
  </p>
</details>

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
    position: sticky;
    left: 0;
    z-index: 1;
    background: var(--papier);
  }
  .choix {
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
    margin: 1.5rem 0 0.5rem;
  }
  .rangee {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
  }
  .rangee button {
    font: inherit;
    font-weight: 650;
    min-height: 2.75rem;
    padding: 0 0.9rem;
    border: 1.5px solid var(--filet);
    border-radius: 999px;
    background: var(--papier);
    color: var(--encre);
    cursor: pointer;
  }
  .droit {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.6rem;
    font-weight: 650;
  }
  .droit select {
    font: inherit;
    font-weight: 600;
    min-height: 2.75rem;
    padding: 0 0.6rem;
    border: 1.5px solid var(--encre);
    border-radius: 6px;
    background: var(--papier);
    color: var(--encre);
    max-width: 100%;
  }
  .rangee button:hover {
    border-color: var(--encre);
  }
  .rangee button[aria-pressed='true'] {
    border-color: var(--encre);
    background: var(--encre);
    color: var(--papier);
  }
  .complet {
    margin-top: 2.5rem;
    border-top: 1px solid var(--filet);
    padding-top: 1rem;
  }
  .complet summary {
    cursor: pointer;
    font-weight: 650;
  }
  th[scope='row'] a {
    text-decoration: none;
  }
  td.fort {
    font-weight: 750;
  }
</style>
