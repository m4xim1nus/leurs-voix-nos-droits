<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import Regle from '$lib/components/Regle.svelte';
  import { ancreGroupe } from '$lib/comparer';
  import { pluriel, pourcent } from '$lib/format';
  import { NOM } from '$lib/site';

  let { data } = $props();
  // Cellule : teinte proportionnelle à l'écart à 50 %, dans la couleur du côté où penche le score.
  const fond = (s: number | null) =>
    s === null
      ? 'transparent'
      : `color-mix(in srgb, var(${s >= 50 ? '--favorable' : '--defavorable'}) ${Math.round(Math.abs(s - 50) * 1.1)}%, var(--papier))`;

  // Comme la page des groupes de l'Assemblée : une période et un droit à la fois, groupes classés ;
  // le tableau complet reste dessous, replié.
  let periode = $state(''); // vide : la période en cours
  let droit = $state('');
  const p = $derived(data.periodes.find((x) => x.id === periode) ?? data.periodes[0]);
  const libelleDroit = $derived(data.droits.find((d) => d.code === droit)?.court ?? null);
  const lignes = $derived(
    (p?.groupes ?? [])
      .map((g) => {
        const s = droit ? g.droits[droit] : g.global;
        return {
          cle: g.groupe.id,
          libelle: g.groupe.sigle,
          couleur: g.groupe.couleur,
          href: `#${ancreGroupe(g.groupe.id, p.id)}`,
          score: s?.score ?? null,
          n_textes: s?.n_textes ?? 0
        };
      })
      .filter((l) => l.n_textes > 0)
      .sort((a, b) => (b.score ?? -1) - (a.score ?? -1))
  );

  // Les liens vers une ligne du tableau (#groupe-…) ouvrent le tableau replié ; les anciens liens
  // vers un département (#dep-…) mènent à la page des sénateur·ices.
  let complet = $state(false);
  function suivreAncre() {
    const h = location.hash.slice(1);
    if (h.startsWith('dep-')) {
      goto(`/senat/senateurs#${h}`, { replaceState: true });
    } else if (h.startsWith('groupe-')) {
      complet = true;
      requestAnimationFrame(() => document.getElementById(h)?.scrollIntoView());
    }
  }
  onMount(() => {
    suivreAncre();
    addEventListener('hashchange', suivreAncre);
    return () => removeEventListener('hashchange', suivreAncre);
  });
</script>

<svelte:head>
  <title>Le Sénat, {NOM}</title>
  <meta
    name="description"
    content="Comment les groupes du Sénat votent sur les textes qui touchent aux droits et libertés, droit par droit, et les votes enregistrés au nom de chaque sénateur·ice."
  />
</svelte:head>

<p class="surtitre">Sénat</p>
<h1>Les groupes, droit par droit</h1>
<p class="chapo">
  Comment les groupes du Sénat votent sur les textes qui touchent aux droits et libertés, depuis
  juin 2017 : {pluriel(
    data.n_textes,
    'vote décisif compté',
    'votes décisifs comptés',
    'aucun vote décisif compté pour l’instant'
  )}. Le calcul est à part de celui de l’Assemblée : les textes comptés diffèrent, et les scores ne
  se comparent pas d’une chambre à l’autre.
</p>

{#if p}
  <div class="choix">
    {#if data.periodes.length > 1}
      <div class="rangee" role="group" aria-label="Période">
        {#each data.periodes as x (x.id)}
          <button type="button" aria-pressed={p?.id === x.id} onclick={() => (periode = x.id)}
            >{x.libelle}</button
          >
        {/each}
      </div>
    {/if}
    <label class="droit"
      >Droit
      <select bind:value={droit}>
        <option value="">Tous les droits</option>
        {#each data.droits as d (d.code)}<option value={d.code}>{d.court}</option>{/each}
      </select></label
    >
  </div>

  <h2 aria-live="polite">{libelleDroit ?? 'Tous les droits'}, {p.libelle.toLowerCase()}</h2>
  <p class="petit discret">
    {pluriel(p.n_textes, 'vote décisif compté', 'votes décisifs comptés')} sur la période.
  </p>
  {#if lignes.length}
    <Regle comptes {lignes} />
  {:else}
    <p>Aucun texte compté ne touche ce droit sur cette période.</p>
  {/if}
{:else}
  <p>Aucun vote du Sénat n’est compté pour l’instant.</p>
{/if}

<h2>Un vote enregistré n’est pas une présence</h2>
<p>
  Sur presque chaque scrutin public du Sénat, un vote est enregistré pour presque tous les sièges,
  et il suit presque toujours la majorité du groupe. Le règlement permet de voter par délégation et
  par procédé électronique. Ces votes sont les résultats officiels, et le site les compte tels
  quels. Ils ne disent pas qui était présent et peuvent ne pas refléter un choix individuel. C’est
  pourquoi cette page présente d’abord les groupes, et qu’une fiche de sénateur·ice n’affiche aucun
  taux de participation (<a href="/methodologie#regle-27">règle 27</a>).
</p>
<p>
  <a href="/senat/senateurs">Les sénateur·ices en poste, par département</a> ·
  <a href="/senat/comparer">Comparer deux sénateur·ices ou deux groupes du Sénat</a>
</p>

{#if data.periodes.length}
  <details class="complet" bind:open={complet}>
    <summary>Le tableau complet : tous les groupes, tous les droits</summary>
    {#each data.periodes as per (per.id)}
      {@const presents = data.droits.filter((d) =>
        per.groupes.some((g) => g.droits[d.code] !== null)
      )}
      <h3>{per.libelle}</h3>
      <p class="petit discret">
        {pluriel(per.n_textes, 'vote décisif compté', 'votes décisifs comptés')}.
      </p>
      <div class="defile">
        <table>
          <thead>
            <tr>
              <th scope="col">Groupe</th>
              <th scope="col" class="nombre">Ensemble</th>
              {#each presents as d (d.code)}<th scope="col" class="nombre">{d.court}</th>{/each}
            </tr>
          </thead>
          <tbody>
            {#each per.groupes as g (g.groupe.id)}
              <tr id={ancreGroupe(g.groupe.id, per.id)}>
                <th scope="row" title={g.groupe.nom}>{g.groupe.sigle}</th>
                <td class="nombre fort" style:background={fond(g.global?.score ?? null)}
                  >{pourcent(g.global?.score ?? null)}</td
                >
                {#each presents as d (d.code)}
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
      Part des votes favorables aux droits. Chaque texte pèse 1, partagé entre son vote décisif et
      ses amendements clés. Abstentions et non-votants hors calcul. Un vote compte pour le groupe du
      jour du vote, et un texte pour la période de son vote décisif. Les groupes portent leur nom
      actuel, même pour les années où ils s’appelaient autrement. Case vide : aucun texte compté ne
      touche ce droit.
    </p>
  </details>
{/if}

<style>
  .fort {
    font-weight: 700;
  }
  tr {
    scroll-margin-top: 1rem;
  }
  tr:target th {
    text-decoration: underline;
  }
  th[scope='row'] {
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
  .rangee button:hover {
    border-color: var(--encre);
  }
  .rangee button[aria-pressed='true'] {
    border-color: var(--encre);
    background: var(--encre);
    color: var(--papier);
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
  .complet {
    margin-top: 2.5rem;
    border-top: 1px solid var(--filet);
    padding-top: 1rem;
  }
  .complet summary {
    cursor: pointer;
    font-weight: 650;
  }
</style>
