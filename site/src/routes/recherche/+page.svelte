<!--
  Tous les résultats d'une recherche. La page est statique : la requête se lit dans l'adresse côté navigateur, et les index
  sont les mêmes JSON que pour la case de l'en-tête. Rien n'est envoyé à un serveur.
-->
<script lang="ts">
  import { afterNavigate, goto } from '$app/navigation';
  import { chargerMoteur, chercherCodePostal, type ResultatCP } from '$lib/charge-recherche';
  import ResultatsRecherche from '$lib/components/ResultatsRecherche.svelte';
  import { pluriel } from '$lib/format';
  import { estCodePostal, nombreResultats, type Resultats } from '$lib/recherche';
  import { NOM } from '$lib/site';

  let saisie = $state('');
  let etat = $state<'repos' | 'attente' | 'erreur' | 'pret'>('repos');
  let r = $state<Resultats>({ elus: [], pays: [], textes: [], ecartes: [] });
  let cp = $state<ResultatCP | null>(null);
  let cherche = $state('');
  let requete = 0;

  const total = $derived(nombreResultats(r) + (cp && 'cp' in cp ? cp.circos.length : 0));

  async function lancer(q: string) {
    const n = ++requete;
    cherche = q;
    if (q.length < 2) {
      etat = 'repos';
      return;
    }
    etat = 'attente';
    try {
      const [moteur, parCode] = await Promise.all([
        chargerMoteur(),
        estCodePostal(q) ? chercherCodePostal(q) : null
      ]);
      if (n !== requete) return;
      cp = parCode;
      r = estCodePostal(q) ? { elus: [], pays: [], textes: [], ecartes: [] } : moteur.chercher(q);
      etat = 'pret';
    } catch {
      if (n === requete) etat = 'erreur';
    }
  }

  afterNavigate(() => {
    const q = (new URL(location.href).searchParams.get('q') ?? '').trim();
    saisie = q;
    lancer(q);
  });
</script>

<svelte:head>
  <title>Recherche, {NOM}</title>
  <meta name="robots" content="noindex" />
</svelte:head>

<h1>Recherche</h1>
<p class="chapo">
  Élu·es, textes qualifiés et écartés, code postal, pays. La recherche se fait dans votre navigateur
  : ce que vous tapez n’est envoyé nulle part.
</p>

<form
  role="search"
  onsubmit={(ev) => {
    ev.preventDefault();
    goto(`/recherche?q=${encodeURIComponent(saisie.trim())}`, { keepFocus: true });
  }}
>
  <label for="recherche-page">Votre recherche</label>
  <div class="champ">
    <input id="recherche-page" type="search" autocomplete="off" bind:value={saisie} />
    <button type="submit">Chercher</button>
  </div>
</form>

<div class="resultats" aria-live="polite">
  {#if etat === 'attente'}
    <p class="discret">Recherche…</p>
  {:else if etat === 'erreur'}
    <p>La recherche n’a pas pu se charger. Vérifiez votre connexion.</p>
  {:else if etat === 'pret'}
    {#if total}
      <p class="discret petit">{pluriel(total, 'résultat')} pour « {cherche} »</p>
    {:else if !(cp && 'erreur' in cp)}
      <p>
        Rien pour « {cherche} ». La recherche porte sur les noms des élu·es, les titres et résumés des
        textes qualifiés, et les titres des textes écartés ; pas sur les 18 000 scrutins. Parcourez aussi
        les
        <a href="/textes">textes</a> ou les <a href="/droits">droits</a>.
      </p>
    {/if}
    <ResultatsRecherche {r} {cp} />
  {/if}
</div>
<noscript
  ><p>
    La recherche demande JavaScript. Les <a href="/textes">textes</a> et les
    <a href="/circonscriptions">circonscriptions</a> sont listés sans.
  </p></noscript
>

<style>
  label {
    display: block;
    font-weight: 650;
    margin-bottom: 0.35rem;
  }
  .champ {
    display: flex;
    gap: 0.5rem;
    max-width: 34rem;
  }
  input {
    flex: 1;
    min-width: 0;
    font: inherit;
    font-size: 1.15rem;
    padding: 0.6rem 0.75rem;
    border: 2px solid var(--encre);
    border-radius: 3px;
    background: var(--papier);
    color: var(--encre);
  }
  button {
    font: inherit;
    font-weight: 700;
    padding: 0 1.1rem;
    border: 2px solid var(--encre);
    border-radius: 3px;
    background: var(--encre);
    color: var(--papier);
    cursor: pointer;
  }
  .resultats {
    margin-top: 1.25rem;
    max-width: 44rem;
  }
</style>
