<script lang="ts">
  import '../app.css';
  import { page } from '$app/state';
  import CaseRecherche from '$lib/components/CaseRecherche.svelte';
  import { date, pluriel } from '$lib/format';
  import { DEPOT, NOM, OUVERT } from '$lib/site';

  let { data, children } = $props();

  // Cinq rubriques ; celles qui regroupent deux pages ont des sous-onglets, sans menu déroulant.
  const MENU = [
    { href: '/droits', libelle: 'Droits', sous: [] },
    {
      href: '/textes',
      libelle: 'Textes',
      sous: [
        { href: '/textes', libelle: 'Textes qualifiés' },
        { href: '/en-cours', libelle: 'En cours' }
      ]
    },
    {
      href: '/groupes',
      libelle: 'Groupes',
      sous: [
        { href: '/groupes', libelle: 'Groupes' },
        { href: '/comparer', libelle: 'Comparer' }
      ]
    },
    {
      href: '/senat',
      libelle: 'Sénat',
      sous: [
        { href: '/senat', libelle: 'Groupes et sénateur·ices' },
        { href: '/senat/comparer', libelle: 'Comparer' }
      ]
    },
    {
      href: '/methodologie',
      libelle: 'Méthode',
      sous: [
        { href: '/methodologie', libelle: 'Méthodologie' },
        { href: '/donnees', libelle: 'Données' }
      ]
    }
  ];
  const dans = (href: string) =>
    page.url.pathname === href || page.url.pathname.startsWith(`${href}/`);
  const rubrique = $derived(
    MENU.find((m) => dans(m.href) || m.sous.some((s) => dans(s.href))) ?? null
  );
</script>

<a class="evitement" href="#contenu">Aller au contenu</a>

{#if !OUVERT}
  <p class="bandeau">
    Site en préparation : {pluriel(data.nTextes, 'texte qualifié', 'textes qualifiés')} à ce jour. Les
    scores changeront à mesure que d’autres textes seront qualifiés.
  </p>
{/if}

<header>
  <a class="marque" href="/">{NOM}</a>
  <CaseRecherche />
  <nav aria-label="Principale">
    <ul>
      {#each MENU as m (m.href)}
        <li>
          <a href={m.href} aria-current={m === rubrique ? 'true' : undefined}>{m.libelle}</a>
        </li>
      {/each}
    </ul>
  </nav>
  {#if rubrique?.sous.length}
    <nav class="sous" aria-label={rubrique.libelle}>
      <ul>
        {#each rubrique.sous as s (s.href)}
          <li><a href={s.href} aria-current={dans(s.href) ? 'page' : undefined}>{s.libelle}</a></li>
        {/each}
      </ul>
    </nav>
  {/if}
</header>

<main id="contenu" class="page">
  {@render children()}
</main>

<footer>
  <div class="page">
    <p>
      Votes : open data de l’<a href="https://data.assemblee-nationale.fr">Assemblée nationale</a>
      et du <a href="https://data.senat.fr">Sénat</a>, données du {date(
        data.genereLe.slice(0, 10)
      )}. Chaque qualification de texte cite ses sources.
    </p>
    <p>
      Règles de calcul dans la <a href="/methodologie">méthodologie</a>, tout est
      <a href="/donnees">téléchargeable</a>, <a href={DEPOT}>code source</a> sous licence MIT. Aucun traceur,
      aucune publicité.
    </p>
  </div>
</footer>

<style>
  .evitement {
    position: absolute;
    left: -100vw;
  }
  .evitement:focus {
    left: 1rem;
    top: 1rem;
    z-index: 10;
    background: var(--papier);
    padding: 0.5rem;
  }
  .bandeau {
    margin: 0;
    max-width: none;
    padding: 0.5rem var(--gouttiere);
    background: var(--encre);
    color: var(--papier);
    font-size: 0.9rem;
  }
  header {
    max-width: var(--large);
    margin: 0 auto;
    padding: 1.1rem var(--gouttiere) 0.9rem;
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    justify-content: space-between;
    gap: 0.5rem 2rem;
    border-bottom: 3px solid var(--encre);
    margin-bottom: 2rem;
  }
  .marque {
    font-family: var(--titre);
    font-stretch: 68%;
    font-weight: 850;
    font-size: 1.75rem;
    line-height: 1;
    text-decoration: none;
  }
  nav ul {
    list-style: none;
    margin: 0;
    padding: 0;
    display: flex;
    flex-wrap: wrap;
    gap: 0.25rem 1.1rem;
  }
  nav a {
    text-decoration: none;
    font-weight: 600;
  }
  nav a:hover,
  nav a[aria-current] {
    text-decoration: underline;
    text-decoration-thickness: 2px;
  }
  .sous {
    flex: 1 0 100%;
    font-size: 0.95rem;
  }
  .sous a {
    font-weight: 500;
    color: var(--ardoise);
  }
  .sous a[aria-current] {
    font-weight: 650;
    color: var(--encre);
  }
  footer {
    border-top: 1px solid var(--filet);
    padding-top: 1.5rem;
    color: var(--ardoise);
    font-size: 0.9rem;
  }
  footer a {
    color: inherit;
  }
</style>
