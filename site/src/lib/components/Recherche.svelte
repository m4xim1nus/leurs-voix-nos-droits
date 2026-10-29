<!--
  Recherche d'un député par code postal ou par nom, sans serveur : les tables sont des JSON
  statiques chargés à la demande (/recherche/deputes.json, /recherche/cp/<2 chiffres>.json).
  Code postal à plusieurs circonscriptions : on liste les députés possibles, avec les communes
  de chacune (docs/CONCEPTION.md, code postal).
-->
<script lang="ts">
  import { circonscription, normaliser } from '$lib/format';
  import type { EntreeIndex, TableCodesPostaux } from '$lib/types';

  let { grand = false }: { grand?: boolean } = $props();

  let saisie = $state('');
  let index: EntreeIndex[] | null = null;
  let tables = new Map<string, TableCodesPostaux>();
  let resultat = $state<
    | { type: 'vide' }
    | { type: 'attente' }
    | { type: 'erreur'; message: string }
    | { type: 'noms'; liste: EntreeIndex[] }
    | {
        type: 'cp';
        cp: string;
        circos: {
          id: string;
          libelle: string;
          communes: string[];
          depute: EntreeIndex | null;
        }[];
      }
  >({ type: 'vide' });

  async function json<T>(url: string): Promise<T> {
    const r = await fetch(url);
    if (!r.ok) throw new Error(String(r.status));
    return r.json();
  }

  async function chercher() {
    const q = saisie.trim();
    if (/^\d{5}$/.test(q)) {
      resultat = { type: 'attente' };
      const prefixe = q.slice(0, 2);
      try {
        if (!tables.has(prefixe))
          tables.set(prefixe, await json<TableCodesPostaux>(`/recherche/cp/${prefixe}.json`));
      } catch {
        resultat = { type: 'erreur', message: `Aucun code postal ne commence par ${prefixe}.` };
        return;
      }
      const t = tables.get(prefixe)!;
      const lignes = t.codes[q];
      if (!lignes) {
        resultat = {
          type: 'erreur',
          message: `Le code postal ${q} n’existe pas dans la base de La Poste.`
        };
        return;
      }
      const ids = [...new Set(lignes.map((l) => l.circo))];
      resultat = {
        type: 'cp',
        cp: q,
        circos: ids.map((id) => ({
          id,
          libelle: t.circos[id].libelle,
          communes: [...new Set(lignes.filter((l) => l.circo === id).map((l) => l.commune))],
          depute: t.circos[id].depute
        }))
      };
    } else if (normaliser(q).length >= 2) {
      try {
        index ??= await json<EntreeIndex[]>('/recherche/deputes.json');
      } catch {
        resultat = { type: 'erreur', message: 'La liste des députés n’a pas pu être chargée.' };
        return;
      }
      const mots = normaliser(q).split(' ');
      const liste = index
        .filter((e) => mots.every((m) => normaliser(e.nom).includes(m)))
        .sort((a, b) => Number(b.actuel) - Number(a.actuel))
        .slice(0, 12);
      resultat = liste.length
        ? { type: 'noms', liste }
        : { type: 'erreur', message: `Aucun député ne s’appelle « ${q} » depuis 2022.` };
    } else {
      resultat = { type: 'vide' };
    }
  }

  let minuterie: ReturnType<typeof setTimeout>;
  function frappe() {
    clearTimeout(minuterie);
    minuterie = setTimeout(chercher, 180);
  }
</script>

{#snippet carte(e: EntreeIndex)}
  <a class="depute" href="/deputes/{e.slug}">
    <span class="nom">{e.nom}</span>
    <span class="detail">
      <span class="sigle" style:--c={e.couleur}>{e.sigle}</span>
      {#if e.departement}{e.departement}{/if}{#if !e.actuel}, {e.feminin
          ? 'ancienne députée'
          : 'ancien député'}{/if}
    </span>
  </a>
{/snippet}

<form
  class="recherche"
  class:grand
  role="search"
  onsubmit={(ev) => {
    ev.preventDefault();
    chercher();
  }}
>
  <label for="recherche-{grand ? 'accueil' : 'page'}">Code postal ou nom du député</label>
  <div class="champ">
    <input
      id="recherche-{grand ? 'accueil' : 'page'}"
      type="search"
      autocomplete="off"
      placeholder="33000, ou un nom"
      bind:value={saisie}
      oninput={frappe}
    />
    <button type="submit">Chercher</button>
  </div>
</form>
<p class="etranger petit discret">
  Français établis hors de France : <a href="/circonscriptions#etranger"
    >vos onze circonscriptions</a
  >.
</p>

<div class="resultats" aria-live="polite">
  {#if resultat.type === 'attente'}
    <p class="discret">Recherche…</p>
  {:else if resultat.type === 'erreur'}
    <p>{resultat.message}</p>
  {:else if resultat.type === 'noms'}
    <ul>
      {#each resultat.liste as e (e.slug)}
        <li>{@render carte(e)}</li>
      {/each}
    </ul>
  {:else if resultat.type === 'cp'}
    {#if resultat.circos.length > 1}
      <p>
        Le code postal {resultat.cp} couvre {resultat.circos.length} circonscriptions. Votre député dépend
        {new Set(resultat.circos.flatMap((c) => c.communes)).size === 1
          ? 'de votre adresse'
          : 'de votre commune, voire de votre adresse'}.
      </p>
    {/if}
    <ul>
      {#each resultat.circos as c (c.id)}
        <li>
          {#if c.depute}
            {@render carte(c.depute)}
          {:else}
            <a class="depute" href="/circonscriptions/{c.id}">
              <span class="nom">Siège vacant</span>
              <span class="detail">{c.libelle}</span>
            </a>
          {/if}
          <p class="petit discret communes">
            <a href="/circonscriptions/{c.id}">{c.libelle}</a>
            {#if resultat.circos.length > 1}: {c.communes.join(', ')}{/if}
          </p>
        </li>
      {/each}
    </ul>
  {/if}
</div>
<noscript
  ><p class="petit">
    La recherche demande JavaScript. Les députés sont aussi listés par <a href="/circonscriptions"
      >circonscription</a
    >.
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
  .grand input {
    font-size: 1.4rem;
    padding: 0.75rem 0.9rem;
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
  .etranger {
    margin: 0.5rem 0 0;
  }
  .resultats ul {
    list-style: none;
    padding: 0;
    margin: 1rem 0 0;
    display: grid;
    gap: 0.75rem;
    max-width: 34rem;
  }
  .depute {
    display: block;
    padding: 0.6rem 0.8rem;
    border: 1.5px solid var(--filet);
    border-left: 5px solid var(--encre);
    border-radius: 3px;
    text-decoration: none;
  }
  .depute:hover {
    border-color: var(--encre);
  }
  .depute .nom {
    display: block;
    font-family: var(--titre);
    font-stretch: 80%;
    font-weight: 750;
    font-size: 1.3rem;
  }
  .detail {
    color: var(--ardoise);
  }
  .communes {
    margin: 0.3rem 0 0;
  }
  .resultats > p {
    margin-top: 1rem;
  }
</style>
