<!--
  Case de recherche de l'en-tête, sur toutes les pages : élu·es, code postal, pays, textes qualifiés et écartés. Les index
  sont des JSON statiques, chargés à la première frappe (docs/CONCEPTION.md, recherche).
  Motif « combobox » de l'ARIA : le focus reste dans le champ, les flèches parcourent les résultats.
-->
<script lang="ts">
  import { afterNavigate, goto } from '$app/navigation';
  import { page } from '$app/state';
  import { chargerMoteur, chercherCodePostal, type ResultatCP } from '$lib/charge-recherche';
  import { pluriel } from '$lib/format';
  import { estCodePostal, nombreResultats, type Resultats } from '$lib/recherche';
  import ResultatsRecherche from './ResultatsRecherche.svelte';

  const LIMITES = { elus: 4, pays: 3, textes: 5, ecartes: 3 };
  const VIDE: Resultats = { elus: [], pays: [], textes: [], ecartes: [] };

  let saisie = $state('');
  let ouvert = $state(false);
  let etat = $state<'repos' | 'attente' | 'erreur' | 'pret'>('repos');
  let r = $state<Resultats>(VIDE);
  let cp = $state<ResultatCP | null>(null);
  let panneau = $state<HTMLElement>();
  let actif = $state(-1);
  let requete = 0;

  const q = $derived(saisie.trim());
  const total = $derived(nombreResultats(r) + (cp && 'cp' in cp ? cp.circos.length : 0));

  async function chercher() {
    const n = ++requete;
    marquer(-1);
    if (q.length < 2) {
      etat = 'repos';
      ouvert = false;
      return;
    }
    ouvert = true;
    if (etat !== 'pret') etat = 'attente';
    try {
      const [moteur, parCode] = await Promise.all([
        chargerMoteur(),
        estCodePostal(q) ? chercherCodePostal(q) : null
      ]);
      if (n !== requete) return;
      cp = parCode;
      r = estCodePostal(q) ? VIDE : moteur.chercher(q);
      etat = 'pret';
    } catch {
      if (n === requete) etat = 'erreur';
    }
  }

  let minuterie: ReturnType<typeof setTimeout>;
  function frappe() {
    clearTimeout(minuterie);
    minuterie = setTimeout(chercher, 120);
  }

  const options = () => [...(panneau?.querySelectorAll<HTMLAnchorElement>('a[data-option]') ?? [])];

  function marquer(i: number) {
    const liste = options();
    for (const o of liste) {
      o.removeAttribute('data-actif');
      o.removeAttribute('id');
    }
    actif = i;
    if (i >= 0 && liste[i]) {
      liste[i].setAttribute('data-actif', 'oui');
      liste[i].id = 'option-active';
      liste[i].scrollIntoView({ block: 'nearest' });
    }
  }

  function clavier(ev: KeyboardEvent) {
    if (ev.key === 'Escape') {
      if (ouvert) ev.preventDefault();
      ouvert = false;
      marquer(-1);
      return;
    }
    if ((ev.key !== 'ArrowDown' && ev.key !== 'ArrowUp') || !q) return;
    ev.preventDefault();
    if (!ouvert) {
      ouvert = true;
      return;
    }
    const n = options().length;
    if (!n) return;
    const pas = ev.key === 'ArrowDown' ? 1 : -1;
    marquer(actif < 0 && pas < 0 ? n - 1 : (actif + pas + n) % n);
  }

  function valider(ev: SubmitEvent) {
    ev.preventDefault();
    clearTimeout(minuterie);
    const lien = actif >= 0 ? options()[actif] : null;
    if (lien) {
      lien.click();
      return;
    }
    if (q.length >= 2) {
      ouvert = false;
      goto(`/recherche?q=${encodeURIComponent(q)}`);
    }
  }

  // Le menu se ferme en changeant de page, et un clic ailleurs le ferme aussi.
  afterNavigate(() => {
    ouvert = false;
    marquer(-1);
  });
</script>

<svelte:document
  onclick={(ev) => {
    if (!(ev.target as Element).closest?.('.case-recherche')) ouvert = false;
  }}
/>

<form class="case-recherche" role="search" onsubmit={valider}>
  <label class="invisible" for="case-recherche"
    >Chercher un·e élu·e, un texte, un code postal ou un pays</label
  >
  <input
    id="case-recherche"
    type="search"
    role="combobox"
    autocomplete="off"
    spellcheck="false"
    placeholder="Élu·e, texte, code postal…"
    aria-expanded={ouvert}
    aria-controls="resultats-en-tete"
    aria-autocomplete="list"
    aria-activedescendant={actif >= 0 ? 'option-active' : undefined}
    bind:value={saisie}
    oninput={frappe}
    onfocus={() => {
      if (q.length >= 2 && etat === 'pret') ouvert = true;
    }}
    onkeydown={clavier}
  />
  <div id="resultats-en-tete" class="panneau" hidden={!ouvert} bind:this={panneau}>
    {#if etat === 'attente'}
      <p class="message">Recherche…</p>
    {:else if etat === 'erreur'}
      <p class="message">La recherche n’a pas pu se charger. Vérifiez votre connexion.</p>
    {:else if etat === 'pret'}
      <ResultatsRecherche {r} {cp} limites={LIMITES} compact />
      {#if !total && !(cp && 'erreur' in cp)}
        <p class="message">
          Rien pour « {q} ». Essayez un autre mot, ou parcourez les <a href="/textes">textes</a>.
        </p>
      {:else if nombreResultats(r) > 0}
        <a class="tous" href="/recherche?q={encodeURIComponent(q)}">
          Voir tout ({pluriel(nombreResultats(r), 'résultat')})
        </a>
      {/if}
    {/if}
  </div>
  <p class="invisible" aria-live="polite">
    {#if ouvert && etat === 'pret'}{pluriel(total, 'résultat')}{/if}
  </p>
</form>
<noscript
  ><style>
    .case-recherche {
      display: none;
    }
  </style></noscript
>

<style>
  .case-recherche {
    position: relative;
    flex: 1 1 14rem;
    max-width: 22rem;
  }
  input {
    width: 100%;
    box-sizing: border-box;
    font: inherit;
    font-size: 0.95rem;
    padding: 0.3rem 0.6rem;
    border: 1.5px solid var(--encre);
    border-radius: 3px;
    background: var(--papier);
    color: var(--encre);
  }
  .panneau {
    position: absolute;
    z-index: 20;
    top: calc(100% + 0.3rem);
    right: 0;
    width: min(34rem, calc(100vw - 2 * var(--gouttiere)));
    max-height: min(32rem, 75vh);
    overflow-y: auto;
    box-sizing: border-box;
    padding: 0.6rem;
    background: var(--papier);
    border: 1.5px solid var(--encre);
    border-radius: 3px;
    box-shadow: 0 6px 20px rgb(0 0 0 / 0.18);
  }
  .panneau[hidden] {
    display: none;
  }
  .message {
    margin: 0.2rem 0.5rem;
  }
  .tous {
    display: block;
    margin-top: 0.6rem;
    padding: 0.4rem 0.5rem;
    border-top: 1px solid var(--filet);
    font-weight: 650;
  }
  .invisible {
    position: absolute;
    width: 1px;
    height: 1px;
    overflow: hidden;
    clip-path: inset(50%);
    white-space: nowrap;
    margin: 0;
  }
  @media (max-width: 40rem) {
    .case-recherche {
      flex-basis: 100%;
      max-width: none;
    }
    .panneau {
      left: 0;
      right: auto;
      width: 100%;
    }
  }
</style>
