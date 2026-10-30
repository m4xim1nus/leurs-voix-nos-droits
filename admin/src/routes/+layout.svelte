<script lang="ts">
  import '../app.css';
  import { page } from '$app/state';
  import { dateHeure } from '$lib/format';

  let { data, children } = $props();

  const liens = [
    { href: '/', libelle: 'Textes' },
    { href: '/a-traiter', libelle: 'À traiter' },
    { href: '/apercu', libelle: 'Aperçu des scores' },
    { href: '/publier', libelle: 'Publier' },
    { href: '/journal', libelle: 'Journal' }
  ];
  const actif = (href: string) =>
    href === '/'
      ? page.url.pathname === '/' || page.url.pathname.startsWith('/textes')
      : page.url.pathname.startsWith(href);
</script>

<header>
  <a class="marque" href="/">Leurs voix, nos droits <span>admin</span></a>
  <nav aria-label="Sections">
    {#each liens as l (l.href)}
      <a href={l.href} aria-current={actif(l.href) ? 'page' : undefined}>{l.libelle}</a>
    {/each}
  </nav>
  <p class="discret">
    {data.email}
    {#if data.donnees}· données du {dateHeure(data.donnees)}{/if}
  </p>
</header>

<main>
  {@render children()}
</main>

<style>
  header {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.4rem 1.4rem;
    padding: 0.6rem 1rem;
    border-bottom: 1px solid var(--bord);
    background: var(--surface);
  }
  .marque {
    font-weight: 700;
    color: var(--texte);
    text-decoration: none;
  }
  .marque span {
    font-weight: 400;
    color: var(--texte-2);
  }
  nav {
    display: flex;
    gap: 0.2rem;
    flex-wrap: wrap;
  }
  nav a {
    padding: 0.25rem 0.6rem;
    border-radius: var(--rayon);
    text-decoration: none;
    color: var(--texte);
  }
  nav a[aria-current='page'] {
    background: var(--accent);
    color: var(--accent-texte);
  }
  header p {
    margin: 0 0 0 auto;
  }
  main {
    padding: 0 1rem 3rem;
    max-width: 1400px;
    margin: 0 auto;
  }
</style>
