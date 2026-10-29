<!--
  Comparer deux députés, deux groupes, ou un député et un groupe : score d'ensemble, droit par
  droit, puis les textes où leurs votes s'écartent le plus. Données chargées à la demande
  (/comparer/donnees.json) ; le choix est gardé dans l'adresse (?a=…&b=…) pour être partagé.
-->
<script lang="ts">
  import { onMount } from 'svelte';
  import { replaceState } from '$app/navigation';
  import { page } from '$app/state';
  import { pourcent } from '$lib/format';
  import { NOM } from '$lib/site';

  interface Entite {
    cle: string;
    nom: string;
    sigle: string;
    couleur: string;
    lien: string;
    global: number | null;
    droits: (number | null)[];
    textes: (number | null)[];
  }
  interface Donnees {
    droits: { code: string; court: string }[];
    textes: { id: string; titre: string }[];
    entites: Entite[];
  }

  let donnees = $state<Donnees | null>(null);
  let erreur = $state('');
  let saisies = $state(['', '']);

  const libelle = (e: Entite) => (e.cle.startsWith('d:') ? `${e.nom} (${e.sigle})` : e.nom);
  const choisies = $derived(
    saisies.map((s) => donnees?.entites.find((e) => libelle(e) === s.trim()) ?? null)
  );
  const [a, b] = $derived(choisies);

  const droits = $derived(
    a && b && donnees
      ? donnees.droits
          .map((d, i) => ({ ...d, a: a.droits[i], b: b.droits[i] }))
          .filter((x) => x.a !== null || x.b !== null)
      : []
  );
  // Là où ils s'opposent : textes où les deux ont un score, du plus grand écart au plus petit.
  const ecarts = $derived(
    a && b && donnees
      ? donnees.textes
          .map((t, i) => ({ ...t, a: a.textes[i], b: b.textes[i] }))
          .filter((x) => x.a !== null && x.b !== null)
          .sort((x, y) => Math.abs(y.a! - y.b!) - Math.abs(x.a! - x.b!))
      : []
  );

  onMount(async () => {
    try {
      const r = await fetch('/comparer/donnees.json');
      donnees = await r.json();
    } catch {
      erreur = 'Les données n’ont pas pu être chargées.';
      return;
    }
    const q = page.url.searchParams;
    saisies = [q.get('a'), q.get('b')]
      .map((c) => donnees!.entites.find((e) => e.cle === c) ?? null)
      .map((e) => (e ? libelle(e) : ''));
  });

  $effect(() => {
    if (!a || !b) return;
    const url = new URL(page.url);
    url.searchParams.set('a', a.cle);
    url.searchParams.set('b', b.cle);
    replaceState(url, {});
  });
</script>

<svelte:head>
  <title>Comparer, {NOM}</title>
  <meta
    name="description"
    content="Comparer les votes de deux députés ou de deux groupes sur les droits et libertés."
  />
</svelte:head>

{#snippet duel(x: number | null, y: number | null)}
  <div class="piste" aria-hidden="true">
    {#each [0, 50, 100] as g (g)}<span class="grad" style:left="{g}%"></span>{/each}
    {#if y !== null}<span class="marque b" style:left="{y}%"></span>{/if}
    {#if x !== null}<span class="marque a" style:left="{x}%"></span>{/if}
  </div>
{/snippet}

<h1>Comparer</h1>
<p class="chapo">
  Deux députés, deux groupes, ou un député et son groupe : leurs votes sur les droits, côte à côte.
</p>

{#if erreur}
  <p>{erreur}</p>
{:else}
  <form class="choix" onsubmit={(e) => e.preventDefault()}>
    {#each [0, 1] as i (i)}
      <label>
        <span
          ><span class="pastille {i ? 'b' : 'a'}" aria-hidden="true"></span>{i
            ? 'Second'
            : 'Premier'}</span
        >
        <input
          list="entites"
          bind:value={saisies[i]}
          placeholder="Un nom, ou « Groupe »"
          autocomplete="off"
          disabled={!donnees}
        />
      </label>
    {/each}
    <datalist id="entites">
      {#each donnees?.entites ?? [] as e (e.cle)}<option value={libelle(e)}></option>{/each}
    </datalist>
  </form>

  {#if !donnees}
    <p class="discret">Chargement…</p>
  {:else if !a || !b}
    <p class="discret">Choisissez deux noms dans la liste.</p>
  {:else}
    <section class="face">
      {#each [a, b] as e, i (i)}
        <div>
          <p class="chiffre grand">{pourcent(e.global)}</p>
          <p>
            <span class="pastille {i ? 'b' : 'a'}" aria-hidden="true"></span>
            <a href={e.lien}>{e.nom}</a>
            <span class="sigle" style:--c={e.couleur}>{e.sigle}</span>
          </p>
        </div>
      {/each}
    </section>
    <p class="petit discret">
      Part des votes favorables aux droits, sur l’ensemble des textes qualifiés.
    </p>

    <h2>Droit par droit</h2>
    <ul class="lignes">
      {#each droits as d (d.code)}
        <li>
          <a href="/droits/{d.code}">{d.court}</a>
          {@render duel(d.a, d.b)}
          <span class="valeurs"
            ><span>{pourcent(d.a)}</span> <span class="discret">{pourcent(d.b)}</span></span
          >
        </li>
      {/each}
    </ul>

    <h2>Là où ils s’opposent</h2>
    {#if !ecarts.length}
      <p>Aucun texte sur lequel les deux ont voté.</p>
    {:else}
      <p>Les textes où leurs votes s’écartent le plus, puis les autres.</p>
      <ul class="lignes">
        {#each ecarts as t (t.id)}
          <li>
            <a href="/textes/{t.id}">{t.titre}</a>
            {@render duel(t.a, t.b)}
            <span class="valeurs"
              ><span>{pourcent(t.a)}</span> <span class="discret">{pourcent(t.b)}</span></span
            >
          </li>
        {/each}
      </ul>
    {/if}
  {/if}
{/if}

<style>
  .choix {
    display: flex;
    flex-wrap: wrap;
    gap: 1rem 2rem;
    margin: 1.5rem 0;
  }
  label {
    display: flex;
    flex-direction: column;
    gap: 0.3rem;
    font-weight: 650;
    flex: 1 1 16rem;
    max-width: 26rem;
  }
  input {
    font: inherit;
    font-weight: 400;
    padding: 0.55rem 0.7rem;
    border: 2px solid var(--encre);
    border-radius: 3px;
    background: var(--papier);
    color: var(--encre);
  }
  .pastille {
    display: inline-block;
    width: 0.6rem;
    height: 1.1rem;
    border: 2px solid var(--encre);
    vertical-align: -0.15rem;
    margin-right: 0.3rem;
  }
  .pastille.a {
    background: var(--encre);
  }
  .pastille.b {
    background: var(--papier);
  }
  .face {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
  }
  .face p {
    margin: 0;
  }
  .grand {
    font-size: clamp(3rem, 12vw, 6rem);
    line-height: 1;
  }
  .lignes {
    list-style: none;
    padding: 0;
  }
  .lignes li {
    display: grid;
    grid-template-columns: minmax(8rem, 2fr) 3fr 7rem;
    gap: 0.75rem;
    align-items: center;
    max-width: none;
    padding: 0.45rem 0;
    border-bottom: 1px solid var(--filet);
  }
  .piste {
    position: relative;
    height: 1.5rem;
    border-bottom: 1.5px solid var(--encre);
  }
  .grad {
    position: absolute;
    bottom: 0;
    width: 1px;
    height: 0.6rem;
    background: var(--ardoise);
  }
  .marque {
    position: absolute;
    bottom: -0.4rem;
    width: 0.55rem;
    height: 1.5rem;
    transform: translateX(-50%);
    border: 2px solid var(--encre);
    border-radius: 1px;
  }
  .marque.a {
    background: var(--encre);
  }
  .marque.b {
    background: var(--papier);
    height: 1.1rem;
  }
  .valeurs {
    text-align: right;
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
  }
  @media (max-width: 40rem) {
    .lignes li {
      grid-template-columns: 1fr 7rem;
    }
    .lignes li a {
      grid-column: 1 / -1;
    }
  }
</style>
