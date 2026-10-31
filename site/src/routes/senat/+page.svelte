<script lang="ts">
  import RechercheSenat from '$lib/components/RechercheSenat.svelte';
  import { pluriel, pourcent } from '$lib/format';
  import { NOM } from '$lib/site';

  let { data } = $props();
  // Cellule : teinte proportionnelle à l'écart à 50 %, dans la couleur du côté où penche le score.
  const fond = (s: number | null) =>
    s === null
      ? 'transparent'
      : `color-mix(in srgb, var(${s >= 50 ? '--favorable' : '--defavorable'}) ${Math.round(Math.abs(s - 50) * 1.1)}%, var(--papier))`;
  const presents = $derived(
    data.droits.filter((d) => data.groupes.some((g) => g.droits[d.code] !== null))
  );
</script>

<svelte:head>
  <title>Le Sénat, {NOM}</title>
  <meta
    name="description"
    content="Comment les groupes du Sénat votent sur les textes qui touchent aux droits et libertés, droit par droit, et les votes enregistrés au nom de chaque sénateur·ice."
  />
</svelte:head>

<h1>Le Sénat</h1>
<p class="chapo">
  Comment les groupes du Sénat votent sur les textes qui touchent aux droits et libertés, depuis
  juin 2022 : {pluriel(
    data.n_textes,
    'vote décisif compté',
    'votes décisifs comptés',
    'aucun vote décisif compté pour l’instant'
  )}. Le calcul est à part de celui de l’Assemblée : les textes comptés diffèrent, et les scores ne
  se comparent pas d’une chambre à l’autre.
</p>

<h2>Les groupes, droit par droit</h2>
{#if data.groupes.length}
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
        {#each data.groupes as g (g.groupe.id)}
          <tr id="groupe-{g.groupe.id}">
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
  <p class="petit discret">
    Part des votes favorables aux droits. Chaque texte pèse 1 et ne compte que son vote décisif.
    Abstentions et non-votants hors calcul. Un vote compte pour le groupe du jour du vote. Case
    vide : aucun texte compté ne touche ce droit.
  </p>
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

<h2>Trouver ses sénateur·ices</h2>
<RechercheSenat />

<h2>Sénateur·ices en poste, par département</h2>
{#each data.departements as dep (dep.code)}
  <section class="departement" id="dep-{dep.code}">
    <h3>{dep.nom}</h3>
    <ul>
      {#each dep.senateurs as s (s.slug)}
        <li>
          <a href="/senat/{s.slug}">{s.nom}</a>
          <span class="discret petit"
            >{s.sigle}{s.score?.score != null ? `, ${pourcent(s.score.score)}` : ''}</span
          >
        </li>
      {/each}
    </ul>
  </section>
{/each}

<style>
  .fort {
    font-weight: 700;
  }
  .departement h3 {
    margin-bottom: 0.25rem;
    font-size: 1.1rem;
  }
  .departement ul {
    list-style: none;
    padding: 0;
    margin: 0 0 1rem;
    columns: 2 16rem;
  }
  .departement {
    scroll-margin-top: 1rem;
  }
</style>
