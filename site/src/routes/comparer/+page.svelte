<!--
  Comparer deux députés, deux groupes, ou un député et un groupe : score d'ensemble, droit par
  droit, puis les textes où leurs votes s'écartent le plus. Chaque ligne porte deux règles, le
  premier en haut (curseur plein), le second en bas (curseur creux) ; un bandeau fixe les rappelle
  quand les grands chiffres sortent de l'écran. Données chargées à la demande
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

  // Le bandeau apparaît dès que le bloc des grands chiffres n'est plus visible.
  let face = $state<HTMLElement>();
  let faceVisible = $state(true);
  $effect(() => {
    if (!face) return;
    const o = new IntersectionObserver(([e]) => (faceVisible = e.isIntersecting));
    o.observe(face);
    return () => {
      o.disconnect();
      faceVisible = true;
    };
  });

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
    content="Comparer les votes de deux député·es ou de deux groupes sur les droits et libertés."
  />
</svelte:head>

{#snippet duel(x: number | null, y: number | null)}
  {#each [x, y] as v, i (i)}
    <span class="piste {i ? 'b' : 'a'}" aria-hidden="true">
      {#each [0, 50, 100] as g (g)}<span class="grad" style:left="{g}%"></span>{/each}
      {#if v !== null}<span class="marque" style:left="{v}%"></span>{/if}
    </span>
    <span class="valeur {i ? 'b' : 'a'}"
      ><span class="visuellement-cache">{[a, b][i]?.nom}&nbsp;:</span>
      {pourcent(v)}</span
    >
  {/each}
{/snippet}

{#snippet pastille(i: number, couleur?: string)}
  <span class="pastille {i ? 'b' : 'a'}" style:--c={couleur} aria-hidden="true"></span>
{/snippet}

<h1>Comparer</h1>
<p class="chapo">
  Deux député·es, deux groupes, ou un·e député·e et son groupe : leurs votes sur les droits, côte à
  côte.
</p>

{#if erreur}
  <p>{erreur}</p>
{:else}
  <form class="choix" onsubmit={(e) => e.preventDefault()}>
    {#each [0, 1] as i (i)}
      <label>
        <span>{@render pastille(i, choisies[i]?.couleur)}{i ? 'Second' : 'Premier'}</span>
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
    <section class="face" bind:this={face}>
      {#each [a, b] as e, i (i)}
        <div>
          <p class="chiffre grand">{pourcent(e.global)}</p>
          <p>
            {@render pastille(i, e.couleur)}
            <a href={e.lien}>{e.nom}</a>
            <span class="sigle" style:--c={e.couleur}>{e.sigle}</span>
          </p>
        </div>
      {/each}
    </section>
    <p class="petit discret">
      Part des votes favorables aux droits, sur l’ensemble des textes qualifiés. Sur chaque ligne
      ci-dessous, le premier en haut (curseur plein), le second en bas (curseur creux).
    </p>
    <div class="bandeau" class:visible={!faceVisible} aria-hidden="true">
      <div>
        {#each [a, b] as e, i (i)}
          <span class="qui"
            >{@render pastille(i, e.couleur)}<span class="nom">{e.nom}</span>
            <span class="chiffre">{pourcent(e.global)}</span>
            <span class="discret petit">{i ? 'en bas' : 'en haut'}</span></span
          >
        {/each}
      </div>
    </div>

    <h2>Droit par droit</h2>
    <ul class="lignes" style:--ca={a.couleur} style:--cb={b.couleur}>
      {#each droits as d (d.code)}
        <li>
          <a href="/droits/{d.code}">{d.court}</a>
          {@render duel(d.a, d.b)}
        </li>
      {/each}
    </ul>

    <h2>Là où ils s’opposent</h2>
    {#if !ecarts.length}
      <p>Aucun texte sur lequel les deux ont voté.</p>
    {:else}
      <p>Les textes où leurs votes s’écartent le plus, puis les autres.</p>
      <ul class="lignes" style:--ca={a.couleur} style:--cb={b.couleur}>
        {#each ecarts as t (t.id)}
          <li>
            <a href="/textes/{t.id}">{t.titre}</a>
            {@render duel(t.a, t.b)}
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
    vertical-align: -0.15rem;
    margin-right: 0.35rem;
    box-sizing: border-box;
    border-radius: 1px;
  }
  /* Premier : curseur plein à sa couleur ; second : curseur creux bordé de la sienne. */
  .pastille.a,
  .piste.a .marque {
    background: var(--c, var(--encre));
    border: 1.5px solid var(--encre);
  }
  .pastille.b,
  .piste.b .marque {
    background: var(--papier);
    border: 3px solid var(--c, var(--encre));
  }
  .piste.a .marque {
    --c: var(--ca);
  }
  .piste.b .marque {
    --c: var(--cb);
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
  .bandeau {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 10;
    background: var(--papier);
    border-bottom: 1.5px solid var(--encre);
    transform: translateY(-110%);
    transition: transform 0.15s ease-out;
  }
  .bandeau.visible {
    transform: none;
  }
  .bandeau > div {
    display: flex;
    flex-wrap: wrap;
    gap: 0.25rem 2rem;
    max-width: var(--large);
    margin: 0 auto;
    padding: 0.55rem var(--gouttiere);
  }
  .qui {
    display: inline-flex;
    align-items: baseline;
    gap: 0.4rem;
    min-width: 0;
  }
  .qui .nom {
    font-weight: 650;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .qui .chiffre {
    font-size: 1.15rem;
  }
  .lignes {
    list-style: none;
    padding: 0;
  }
  .lignes li {
    display: grid;
    grid-template-columns: minmax(8rem, 2fr) 3fr 4rem;
    gap: 0.1rem 0.75rem;
    align-items: center;
    max-width: none;
    padding: 0.5rem 0;
    border-bottom: 1px solid var(--filet);
  }
  .lignes li > a {
    grid-row: span 2;
  }
  .piste {
    display: block;
    position: relative;
    height: 1.15rem;
    border-bottom: 1.5px solid var(--ardoise);
  }
  .grad {
    position: absolute;
    bottom: 0;
    width: 1px;
    height: 0.45rem;
    background: var(--ardoise);
  }
  .marque {
    position: absolute;
    bottom: -0.3rem;
    width: 0.6rem;
    height: 1.15rem;
    transform: translateX(-50%);
    box-sizing: border-box;
    border-radius: 1px;
  }
  .valeur {
    text-align: right;
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
    line-height: 1.2;
  }
  .valeur.a {
    font-weight: 700;
  }
  /* Les deux règles restent collées au milieu de la ligne, même sous un long titre. */
  .piste.a,
  .valeur.a {
    align-self: end;
  }
  .piste.b,
  .valeur.b {
    align-self: start;
  }
  @media (max-width: 40rem) {
    .face {
      gap: 0.5rem;
    }
    .bandeau > div {
      flex-direction: column;
    }
    .qui .petit {
      display: none;
    }
    .lignes li {
      grid-template-columns: 1fr 3.5rem;
    }
    .lignes li > a {
      grid-column: 1 / -1;
      grid-row: auto;
      margin-bottom: 0.2rem;
    }
  }
</style>
