<!--
  Recherche d'un·e sénateur·ice par code postal (→ département) ou par nom, sans serveur : JSON statiques
  chargés à la demande (/recherche/senateurs.json, /recherche/departements/<2 chiffres>.json).
-->
<script lang="ts">
  import { normaliser } from '$lib/format';
  import type { EntreeIndex } from '$lib/types';

  let saisie = $state('');
  let index: EntreeIndex[] | null = null;
  let tables = new Map<string, Record<string, string[]>>();
  let liste = $state<EntreeIndex[] | null>(null);
  let message = $state('');

  async function json<T>(url: string): Promise<T> {
    const r = await fetch(url);
    if (!r.ok) throw new Error(String(r.status));
    return r.json();
  }

  async function chercher() {
    const q = saisie.trim();
    liste = null;
    message = '';
    try {
      if (/^\d{5}$/.test(q)) {
        const prefixe = q.slice(0, 2);
        if (!tables.has(prefixe))
          tables.set(prefixe, await json(`/recherche/departements/${prefixe}.json`));
        const deps = tables.get(prefixe)![q];
        if (!deps) {
          message = `Le code postal ${q} n’existe pas dans la base de La Poste.`;
          return;
        }
        index ??= await json<EntreeIndex[]>('/recherche/senateurs.json');
        liste = index.filter((e) => e.actuel && deps.includes(e.circo));
        if (!liste.length) message = 'Aucun·e sénateur·ice en poste trouvé·e pour ce code postal.';
      } else if (normaliser(q).length >= 2) {
        index ??= await json<EntreeIndex[]>('/recherche/senateurs.json');
        const mots = normaliser(q).split(' ');
        liste = index
          .filter((e) => mots.every((m) => normaliser(e.nom).includes(m)))
          .sort((a, b) => Number(b.actuel) - Number(a.actuel))
          .slice(0, 12);
        if (!liste.length) message = `Aucun·e sénateur·ice ne s’appelle « ${q} » depuis 2022.`;
      }
    } catch {
      message = 'La recherche n’a pas pu aboutir.';
    }
  }

  let minuterie: ReturnType<typeof setTimeout>;
  function frappe() {
    clearTimeout(minuterie);
    minuterie = setTimeout(chercher, 180);
  }
</script>

<form
  role="search"
  onsubmit={(e) => {
    e.preventDefault();
    chercher();
  }}
>
  <label for="recherche-senat">Code postal ou nom de votre sénateur·ice</label>
  <div class="champ">
    <input
      id="recherche-senat"
      type="search"
      autocomplete="off"
      placeholder="33000, ou un nom"
      bind:value={saisie}
      oninput={frappe}
    />
    <button type="submit">Chercher</button>
  </div>
</form>
<div aria-live="polite">
  {#if message}<p>{message}</p>{/if}
  {#if liste?.length}
    <ul>
      {#each liste as e (e.slug)}
        <li>
          <a href="/senat/{e.slug}">{e.nom}</a>
          <span class="discret petit"
            ><span class="sigle" style:--c={e.couleur}>{e.sigle}</span>
            {e.departement}{e.actuel
              ? ''
              : e.feminin
                ? ', ancienne sénatrice'
                : ', ancien sénateur'}</span
          >
        </li>
      {/each}
    </ul>
  {/if}
</div>
<noscript
  ><p class="petit">
    La recherche demande JavaScript. La liste par département est plus bas.
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
  ul {
    list-style: none;
    padding: 0;
    margin: 1rem 0 0;
    display: grid;
    gap: 0.4rem;
  }
</style>
