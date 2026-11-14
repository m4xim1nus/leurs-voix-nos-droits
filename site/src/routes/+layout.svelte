<script lang="ts">
  import '../app.css';
  import { page } from '$app/state';
  import CaseRecherche from '$lib/components/CaseRecherche.svelte';
  import { date, pluriel } from '$lib/format';
  import { DEPOT, NOM, OUVERT } from '$lib/site';

  let { data, children } = $props();

  // Cinq rubriques ; celles qui regroupent plusieurs pages ont des sous-onglets, sans menu déroulant.
  // Assemblée et Sénat ont la même organisation (groupes, élu·es, comparer), chacune son calcul.
  // `aussi` : autres adresses rangées sous l'onglet ; `exact` : l'onglet ne couvre que son adresse.
  interface Onglet {
    href: string;
    libelle: string;
    aussi?: string[];
    exact?: boolean;
  }
  const MENU: { href: string; libelle: string; sous: Onglet[] }[] = [
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
      libelle: 'Assemblée',
      sous: [
        { href: '/groupes', libelle: 'Groupes' },
        { href: '/circonscriptions', libelle: 'Député·es', aussi: ['/deputes'] },
        { href: '/comparer', libelle: 'Comparer' }
      ]
    },
    {
      href: '/senat',
      libelle: 'Sénat',
      sous: [
        { href: '/senat', libelle: 'Groupes', exact: true },
        { href: '/senat/senateurs', libelle: 'Sénateur·ices', aussi: ['/senat'] },
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
  // Longueur de l'adresse la plus précise d'un onglet qui couvre la page (0 : aucune).
  const portee = (o: Onglet) =>
    o.exact
      ? page.url.pathname === o.href
        ? o.href.length
        : 0
      : Math.max(0, ...[o.href, ...(o.aussi ?? [])].filter(dans).map((h) => h.length));
  const rubrique = $derived(
    MENU.find((m) => dans(m.href) || m.sous.some((s) => portee(s) > 0)) ?? null
  );
  // L'onglet courant : celui qui couvre la page au plus près (une fiche sénateur·ice va sous
  // « Sénateur·ices », la page de comparaison sous « Comparer »).
  const onglet = $derived.by(() => {
    if (!rubrique) return null;
    const scores = rubrique.sous.map((s) => [s, portee(s)] as const).filter(([, n]) => n > 0);
    return scores.sort((a, b) => b[1] - a[1])[0]?.[0] ?? null;
  });
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
          <li><a href={s.href} aria-current={s === onglet ? 'page' : undefined}>{s.libelle}</a></li>
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
