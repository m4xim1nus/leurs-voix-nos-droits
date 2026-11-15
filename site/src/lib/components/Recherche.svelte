<!--
  Recherche d'un député par code postal, par nom ou par pays, sans serveur : les tables sont des JSON
  statiques chargés à la demande ($lib/charge-recherche). La recherche par nom trouve aussi les
  sénateur·ices, signalé·es comme tel·les. La case de l'en-tête (CaseRecherche) cherche aussi les textes.
  Code postal à plusieurs circonscriptions : on liste les députés possibles, avec les communes
  de chacune (docs/CONCEPTION.md, code postal).
-->
<script lang="ts">
  import { chargerMoteur, chercherCodePostal, type CircoTrouvee } from '$lib/charge-recherche';
  import { normaliser, pluriel } from '$lib/format';
  import { estCodePostal } from '$lib/recherche';
  import type { EntreeIndex, PaysIndex } from '$lib/types';

  let { grand = false }: { grand?: boolean } = $props();

  let saisie = $state('');
  let resultat = $state<
    | { type: 'vide' }
    | { type: 'attente' }
    | { type: 'erreur'; message: string }
    | { type: 'noms'; liste: EntreeIndex[]; pays: PaysIndex[]; approche: boolean }
    | { type: 'cp'; cp: string; circos: CircoTrouvee[]; senateurs: EntreeIndex[] }
  >({ type: 'vide' });

  async function chercher() {
    const q = saisie.trim();
    if (estCodePostal(q)) {
      resultat = { type: 'attente' };
      const t = await chercherCodePostal(q);
      resultat = 'erreur' in t ? { type: 'erreur', message: t.erreur } : { type: 'cp', ...t };
    } else if (normaliser(q).length >= 2) {
      try {
        const { elus, pays, approche } = (await chargerMoteur()).chercher(q);
        resultat =
          elus.length || pays.length
            ? { type: 'noms', liste: elus.slice(0, 12), pays, approche: !!approche }
            : {
                type: 'erreur',
                message: `Aucun·e député·e ni sénateur·ice depuis 2017 ne s’appelle « ${q} », et aucun pays ne porte ce nom.`
              };
      } catch {
        resultat = { type: 'erreur', message: 'La liste des élu·es n’a pas pu être chargée.' };
      }
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
  <a class="depute" href="{e.senat ? '/senat' : '/deputes'}/{e.slug}">
    <span class="nom">{e.nom}</span>
    <span class="detail">
      <span class="sigle" style:--c={e.couleur}>{e.sigle}</span>
      {#if e.senat}{e.feminin
          ? e.actuel
            ? 'sénatrice'
            : 'ancienne sénatrice'
          : e.actuel
            ? 'sénateur'
            : 'ancien sénateur'},{' '}{/if}{#if e.departement}{e.departement}{/if}{#if !e.actuel && !e.senat},
        {e.feminin ? 'ancienne députée' : 'ancien député'}{/if}
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
  <label for="recherche-{grand ? 'accueil' : 'page'}">Code postal, pays ou nom de votre élu·e</label
  >
  <div class="champ">
    <input
      id="recherche-{grand ? 'accueil' : 'page'}"
      type="search"
      autocomplete="off"
      placeholder="33000, Allemagne, ou un nom"
      bind:value={saisie}
      oninput={frappe}
    />
    <button type="submit">Chercher</button>
  </div>
</form>
<p class="etranger petit discret">
  Vous vivez hors de France : tapez votre pays, ou voyez
  <a href="/circonscriptions#etranger">les onze circonscriptions</a>.
</p>

<div class="resultats" aria-live="polite">
  {#if resultat.type === 'attente'}
    <p class="discret">Recherche…</p>
  {:else if resultat.type === 'erreur'}
    <p>{resultat.message}</p>
  {:else if resultat.type === 'noms'}
    {#if resultat.approche}
      <p class="petit discret">
        Rien d’exact : voici les résultats les plus proches de votre saisie.
      </p>
    {/if}
    <ul>
      {#each resultat.pays as p (p.pays)}
        <li>
          {#if p.depute}
            {@render carte(p.depute)}
          {:else}
            <a class="depute" href="/circonscriptions/{p.circo}">
              <span class="nom">Siège vacant</span>
            </a>
          {/if}
          <p class="petit discret communes">
            {p.pays} : <a href="/circonscriptions/{p.circo}">{p.libelle}</a>{#if p.hors_tableau}.
              Absent du tableau du code électoral, rattaché d’après le poste consulaire qui le
              couvre{/if}
          </p>
        </li>
      {/each}
      {#each resultat.liste as e (`${e.senat ? 's' : 'd'}-${e.slug}`)}
        <li>{@render carte(e)}</li>
      {/each}
    </ul>
  {:else if resultat.type === 'cp'}
    {#if resultat.senateurs.length}<p class="chambre">À l’Assemblée nationale</p>{/if}
    {#if resultat.circos.length > 1}
      <p>
        Le code postal {resultat.cp} couvre {resultat.circos.length} circonscriptions. Votre député·e
        dépend
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
    {#if resultat.senateurs.length}
      <p class="chambre">
        Au Sénat, {pluriel(resultat.senateurs.length, 'sénateur·ice', 'sénateur·ices')} de votre département
      </p>
      <ul>
        {#each resultat.senateurs as e (e.slug)}
          <li>{@render carte(e)}</li>
        {/each}
      </ul>
    {/if}
  {/if}
</div>
<noscript
  ><p class="petit">
    La recherche demande JavaScript. Les député·es sont aussi listé·es par <a
      href="/circonscriptions">circonscription</a
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
  .chambre {
    margin: 1rem 0 0.25rem;
    font-weight: 650;
  }
</style>
