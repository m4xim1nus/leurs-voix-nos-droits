<script lang="ts">
  // Textes qualifiés : la recherche au centre, les droits en tuiles, chaque texte en carte (le
  // droit et son sens d'abord). La recherche est celle de l'en-tête (mêmes index, mêmes termes),
  // limitée ici aux textes qualifiés.
  import TexteCarte from '$lib/components/TexteCarte.svelte';
  import { chargerMoteur } from '$lib/charge-recherche';
  import { sousAngle } from '$lib/droits';
  import { etatTexte, legislature, normaliser, pluriel } from '$lib/format';
  import { NOM } from '$lib/site';
  import type { Sens } from '$lib/types';

  let { data } = $props();

  let saisie = $state('');
  let droit = $state('');
  let sens = $state<'' | Sens>('');
  let leg = $state('');
  let chambre = $state('');

  // Sens d'un texte sous l'angle du droit choisi (ou de son droit principal) : celui que montre sa carte.
  const sensVu = (t: (typeof data.textes)[number], code: string | null) =>
    t.principal ? sousAngle({ ...t, principal: t.principal }, code).sens : null;

  // Tuiles : pour chaque droit, les textes qui le touchent, selon le sens qu'ils lui donnent.
  const tuiles = $derived(
    data.droits
      .map((d) => {
        const touches = data.textes.filter(
          (t) => t.principal && t.droits.some((x) => x.code === d.code)
        );
        const r = touches.filter((t) => sensVu(t, d.code) === 'restreint').length;
        return { ...d, r, e: touches.length - r, total: touches.length };
      })
      .filter((d) => d.total > 0)
      .sort((a, b) => b.total - a.total)
  );

  // Recherche : le moteur se charge à la première frappe ; l'ordre des résultats est le sien.
  const q = $derived(saisie.trim());
  let rangs = $state<Map<string, number> | null>(null);
  let attente = $state(false);
  let requete = 0;
  $effect(() => {
    const cherche = q;
    const n = ++requete;
    if (normaliser(cherche).length < 2) {
      rangs = null;
      attente = false;
      return;
    }
    attente = true;
    chargerMoteur()
      .then((m) => {
        if (n !== requete) return;
        rangs = new Map(m.chercher(cherche).textes.map((t, i) => [t.id, i]));
      })
      .catch(() => {
        // Index indisponible : repli sur le titre et la phrase en mots simples.
        if (n !== requete) return;
        const mots = normaliser(cherche).split(' ');
        rangs = new Map(
          data.textes
            .filter((t) =>
              mots.every((m) => normaliser(`${t.titre} ${t.simple ?? ''}`).includes(m))
            )
            .map((t, i) => [t.id, i])
        );
      })
      .finally(() => {
        if (n === requete) attente = false;
      });
  });

  const textes = $derived.by(() => {
    const liste = data.textes.filter(
      (t) =>
        (!rangs || rangs.has(t.id)) &&
        (!droit || t.droits.some((d) => d.code === droit)) &&
        (!sens || sensVu(t, droit || null) === sens) &&
        (!leg || (!t.seul && String(t.legislature) === leg)) &&
        (!chambre || (chambre === 'senat') === t.seul)
    );
    return rangs ? liste.sort((a, b) => rangs!.get(a.id)! - rangs!.get(b.id)!) : liste;
  });

  const nomDroit = $derived(data.droits.find((d) => d.code === droit)?.court ?? '');
  const filtre = $derived(Boolean(q || droit || sens || leg || chambre));
  const autresFiltres = $derived(Boolean(leg || chambre));
  const titreResultats = $derived(
    attente
      ? 'Recherche…'
      : filtre
        ? [pluriel(textes.length, 'texte', 'textes', 'Aucun texte'), nomDroit, q && `« ${q} »`]
            .filter(Boolean)
            .join(' · ')
        : 'Du plus récent au plus ancien'
  );

  function toutRetirer() {
    saisie = '';
    droit = '';
    sens = '';
    leg = '';
    chambre = '';
  }
</script>

<svelte:head><title>Textes qualifiés, {NOM}</title></svelte:head>

<h1>Textes qualifiés</h1>
<p class="chapo">
  {pluriel(data.textes.length, 'texte', 'textes', 'Aucun texte')} de loi examinés et qualifiés. Chaque
  carte dit quel droit le texte touche, et s'il l'étend ou le restreint. Les textes votés au seul Sénat
  ne comptent que dans les scores du Sénat.
</p>

<form class="recherche" role="search" onsubmit={(e) => e.preventDefault()}>
  <label for="recherche-textes">Quelle loi cherchez-vous ?</label>
  <div class="case">
    <svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true"
      ><circle cx="10.5" cy="10.5" r="6.5" /><path d="M15.5 15.5 21 21" /></svg
    >
    <input
      id="recherche-textes"
      type="search"
      bind:value={saisie}
      autocomplete="off"
      spellcheck="false"
      placeholder="Drones, logement, pesticides…"
    />
  </div>
</form>

<section class="par-droit" aria-labelledby="titre-droits">
  <div class="entete">
    <h2 id="titre-droits">Par droit</h2>
    <div class="sens-choix" role="group" aria-label="Sens">
      <button type="button" aria-pressed={sens === ''} onclick={() => (sens = '')}>Les deux</button>
      <button
        type="button"
        class="restreint"
        aria-pressed={sens === 'restreint'}
        onclick={() => (sens = 'restreint')}>▼ Restreignent</button
      >
      <button
        type="button"
        class="etend"
        aria-pressed={sens === 'etend'}
        onclick={() => (sens = 'etend')}>▲ Étendent</button
      >
    </div>
  </div>
  <ul class="tuiles">
    {#each tuiles as d (d.code)}
      <li>
        <button
          type="button"
          class="tuile"
          aria-pressed={droit === d.code}
          onclick={() => (droit = droit === d.code ? '' : d.code)}
        >
          <span class="nom">{d.court}</span>
          <span class="barre" aria-hidden="true"
            ><span class="r" style:width="{(100 * d.r) / d.total}%"></span><span
              class="e"
              style:width="{(100 * d.e) / d.total}%"
            ></span></span
          >
          <span class="compte" aria-hidden="true"
            ><span class="defavorable">▼ {d.r}</span><span class="favorable">▲ {d.e}</span></span
          ><span class="visuellement-cache"
            >{pluriel(d.r, 'texte restreint', 'textes restreignent', 'aucun texte ne restreint')} ce droit,
            {pluriel(d.e, 'texte l’étend', 'textes l’étendent', 'aucun ne l’étend')}.</span
          >
        </button>
      </li>
    {/each}
  </ul>
  <details class="plus" open={autresFiltres}>
    <summary>Autres filtres</summary>
    <div class="selects">
      <label>
        Législature
        <select bind:value={leg}>
          <option value="">Toutes</option>
          {#each data.legislatures as l (l)}<option value={String(l)}>{legislature(l)}</option
            >{/each}
        </select>
      </label>
      <label>
        Vote
        <select bind:value={chambre}>
          <option value="">Tous</option>
          <option value="an">À l’Assemblée</option>
          <option value="senat">Au seul Sénat</option>
        </select>
      </label>
    </div>
  </details>
</section>

<div class="resultats-entete">
  <h2 aria-live="polite">{titreResultats}</h2>
  {#if filtre}<button type="button" class="lien" onclick={toutRetirer}>Tout afficher</button>{/if}
</div>
{#if !attente && filtre && !textes.length}
  <p>Aucun texte ne correspond. Essayez un autre mot, ou retirez un filtre.</p>
{/if}
<ul class="cartes">
  {#each textes as t (t.id)}
    <li><TexteCarte texte={t} droit={droit || null} /></li>
  {/each}
</ul>

{#if data.ecartes.length}
  <h2>Textes examinés et écartés</h2>
  <p>
    Ces textes ont été examinés, mais pas qualifiés : textes organisationnels, résolutions,
    conventions internationales, vote décisif sans opposition, ou droit hors de la grille. Le motif
    est donné pour chacun.
  </p>
  <details>
    <summary>{pluriel(data.ecartes.length, 'texte écarté', 'textes écartés')}</summary>
    <ul class="ecartes">
      {#each data.ecartes as e (e.dossier_an)}
        <li>
          {#if e.url_an}<a href={e.url_an} rel="external">{e.titre}</a>{:else}{e.titre}{/if}
          <span class="discret petit"
            >{e.motif}{#if etatTexte(e.etat)}
              {etatTexte(e.etat)}.{/if}</span
          >
        </li>
      {/each}
    </ul>
  </details>
{/if}

<style>
  summary {
    cursor: pointer;
    font-weight: 650;
  }
  .ecartes li {
    margin-bottom: 0.6rem;
  }
  .ecartes span {
    display: block;
  }

  .recherche {
    margin: 2rem 0 1rem;
  }
  .recherche label {
    display: block;
    font-family: var(--titre);
    font-stretch: 72%;
    font-weight: 800;
    font-size: clamp(1.6rem, 4vw, 2.3rem);
    margin-bottom: 0.6rem;
  }
  .case {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    border: 3px solid var(--encre);
    border-radius: 999px;
    padding: 0 1.25rem;
    background: var(--papier);
  }
  .case:focus-within {
    outline: 3px solid var(--focus);
    outline-offset: 2px;
  }
  .case svg {
    flex: none;
    fill: none;
    stroke: var(--encre);
    stroke-width: 2.4;
    stroke-linecap: round;
  }
  .case input {
    flex: 1;
    min-width: 0;
    height: 3.6rem;
    border: 0;
    outline: none;
    background: transparent;
    color: var(--encre);
    font: inherit;
    font-size: 1.2rem;
  }

  .entete,
  .resultats-entete {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    align-items: baseline;
    gap: 0.75rem 1.5rem;
  }
  .entete h2,
  .resultats-entete h2 {
    margin: 0;
    font-size: clamp(1.4rem, 3vw, 1.8rem);
  }
  .par-droit {
    margin: 2rem 0;
  }
  .sens-choix {
    display: flex;
    border: 2px solid var(--encre);
    border-radius: 999px;
    overflow: hidden;
  }
  .sens-choix button {
    white-space: nowrap;
    font: inherit;
    font-size: 0.95rem;
    font-weight: 650;
    min-height: 2.75rem;
    padding: 0 clamp(0.6rem, 2vw, 1rem);
    border: 0;
    background: var(--papier);
    color: var(--encre);
    cursor: pointer;
  }
  .sens-choix button[aria-pressed='true'] {
    background: var(--encre);
    color: var(--papier);
  }
  .sens-choix button.restreint[aria-pressed='true'] {
    background: var(--defavorable);
  }
  .sens-choix button.etend[aria-pressed='true'] {
    background: var(--favorable);
  }
  .tuiles {
    list-style: none;
    padding: 0;
    margin: 1rem 0 0;
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(min(100% / 2 - 0.3rem, 13rem), 1fr));
    gap: 0.6rem;
  }
  .tuile {
    width: 100%;
    height: 100%;
    font: inherit;
    text-align: left;
    color: var(--encre);
    background: var(--papier);
    border: 1px solid var(--filet);
    border-radius: 10px;
    padding: 0.8rem 0.9rem;
    cursor: pointer;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  .tuile:hover {
    border-color: var(--encre);
  }
  .tuile[aria-pressed='true'] {
    border: 2px solid var(--encre);
    background: var(--plan);
  }
  .nom {
    font-weight: 700;
    line-height: 1.2;
  }
  .barre {
    display: flex;
    height: 6px;
    border-radius: 3px;
    overflow: hidden;
    background: var(--filet);
  }
  .barre .r {
    background: var(--defavorable);
  }
  .barre .e {
    background: var(--favorable);
  }
  .compte {
    display: flex;
    gap: 1rem;
    font-size: 0.95rem;
    font-weight: 700;
  }
  .plus {
    margin-top: 1rem;
  }
  .selects {
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem 1.5rem;
    margin-top: 0.75rem;
  }
  .selects label {
    display: flex;
    flex-direction: column;
    font-weight: 650;
    font-size: 0.9rem;
  }
  select {
    font: inherit;
    font-weight: 400;
    font-size: 1rem;
    padding: 0.35rem 0.5rem;
    border: 1.5px solid var(--encre);
    border-radius: 3px;
    background: var(--papier);
    color: var(--encre);
    min-width: 11rem;
  }
  .resultats-entete {
    border-top: 1px solid var(--filet);
    padding-top: 1.25rem;
    margin-bottom: 1rem;
  }
  .lien {
    font: inherit;
    font-weight: 650;
    background: none;
    border: 0;
    padding: 0;
    color: var(--lien);
    text-decoration: underline;
    cursor: pointer;
    min-height: 2.75rem;
  }
  .cartes {
    list-style: none;
    padding: 0;
    margin: 0;
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(min(100%, 28rem), 1fr));
    gap: 0.75rem;
  }
  .cartes li {
    display: flex;
  }
  .cartes li > :global(a) {
    flex: 1;
  }
</style>
