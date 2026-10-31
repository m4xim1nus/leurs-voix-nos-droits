<script lang="ts">
  import { LIBELLES_STATUT } from '$lib/format';

  let { data } = $props();

  const groupes = $derived(new Map(data.groupes.map((g) => [g.id, g])));
  const droits = $derived(['global', ...data.droits.map((d) => d.code)]);
  const presents = $derived(droits.filter((d) => data.scores.some((s) => s.droit === d)));
  // Lignées triées par score global décroissant.
  const lignees = $derived(
    [...new Set(data.scores.map((s) => s.lignee))].sort(
      (a, b) => (score(b, 'global')?.score ?? -1) - (score(a, 'global')?.score ?? -1)
    )
  );
  const parCle = $derived(new Map(data.scores.map((s) => [`${s.lignee}|${s.droit}`, s])));
  function score(l: string, d: string) {
    return parCle.get(`${l}|${d}`);
  }
  const libelle = (l: string) => {
    const g = groupes.get(l);
    return g ? `${g.sigle} (${['', 'XV', 'XVI', 'XVII'][g.legislature - 14]}e)` : l;
  };
  const groupesSenat = $derived(new Map(data.groupesSenat.map((g) => [g.id, g])));
  const droitsSenat = $derived(droits.filter((d) => data.scoresSenat.some((s) => s.droit === d)));
  const parCleSenat = $derived(new Map(data.scoresSenat.map((s) => [`${s.lignee}|${s.droit}`, s])));
  const lignesSenat = $derived(
    [...new Set(data.scoresSenat.map((s) => s.lignee))].sort(
      (a, b) =>
        (parCleSenat.get(`${b}|global`)?.score ?? -1) -
        (parCleSenat.get(`${a}|global`)?.score ?? -1)
    )
  );
</script>

<svelte:head><title>Aperçu des scores · admin</title></svelte:head>

<h1>Aperçu des scores de groupe</h1>
<p class="discret">
  Calculés depuis les ventilations officielles, avec les règles 14 à 19 de la méthode, sur
  {data.textes.length} textes
  {data.brouillons ? 'validés, à relire ou en brouillon' : 'validés'}. Les scores publiés sont
  recalculés par le pipeline depuis les votes nominatifs ; les deux concordent (test croisé). Les
  scores des députés n'apparaissent qu'après publication.
</p>
<p>
  {#if data.brouillons}
    <a href="?">Validés seulement</a>
  {:else}
    <a href="?brouillons=oui">Inclure brouillons et textes à relire</a>
  {/if}
</p>

<div class="defile">
  <table>
    <thead>
      <tr>
        <th>Groupe (lignée)</th>
        {#each presents as d (d)}<th class="nombre">{d}</th>{/each}
      </tr>
    </thead>
    <tbody>
      {#each lignees as l (l)}
        <tr>
          <td>{libelle(l)}</td>
          {#each presents as d (d)}
            {@const s = score(l, d)}
            <td
              class="nombre"
              title={s
                ? `${s.n_textes} texte(s), ${s.votes_favorables} votes favorables, ${s.votes_defavorables} défavorables, ${s.abstentions} abstentions, ${s.non_votants} non-votants`
                : ''}
            >
              {#if s?.score != null}
                <span class="barre" style:--v="{s.score}%">{s.score}</span>
              {:else}–{/if}
            </td>
          {/each}
        </tr>
      {/each}
    </tbody>
  </table>
</div>

<h2>Sénat (règle 26)</h2>
<p class="discret">
  Calcul à part, sur le seul décisif de chaque texte. Aucune correspondance avec les groupes de
  l'Assemblée (règle 28). Score individuel des sénateur·ices : après publication.
</p>
{#if lignesSenat.length}
  <div class="defile">
    <table>
      <thead>
        <tr>
          <th>Groupe</th>
          {#each droitsSenat as d (d)}<th class="nombre">{d}</th>{/each}
        </tr>
      </thead>
      <tbody>
        {#each lignesSenat as g (g)}
          <tr>
            <td>{groupesSenat.get(g)?.sigle ?? g}</td>
            {#each droitsSenat as d (d)}
              {@const s = parCleSenat.get(`${g}|${d}`)}
              <td
                class="nombre"
                title={s
                  ? `${s.n_textes} texte(s), ${s.votes_favorables} votes favorables, ${s.votes_defavorables} défavorables, ${s.abstentions} abstentions, ${s.non_votants} non-votants`
                  : ''}
              >
                {#if s?.score != null}
                  <span class="barre" style:--v="{s.score}%">{s.score}</span>
                {:else}–{/if}
              </td>
            {/each}
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
{:else}
  <p class="discret">Aucun décisif du Sénat parmi ces textes.</p>
{/if}

<h2>Textes pris en compte</h2>
<p>
  {#each data.textes as t (t.dossier_an)}
    <a href="/textes/{t.dossier_an}" class="pastille {t.statut}" title={LIBELLES_STATUT[t.statut]}
      >{t.id}</a
    >
    {' '}
  {/each}
</p>

<style>
  .defile {
    overflow-x: auto;
  }
  .barre {
    display: inline-block;
    min-width: 3.2rem;
    background: linear-gradient(to right, var(--ok-fond) var(--v), transparent var(--v));
    padding: 0 0.2rem;
  }
</style>
