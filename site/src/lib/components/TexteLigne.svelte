<!-- Un texte qualifié dans une liste : titre, date du vote décisif, droit principal et son sens. -->
<script lang="ts">
  import { court, phrase } from '$lib/droits';
  import { date, legislature } from '$lib/format';
  import type { TexteCourt } from '$lib/server/vues';

  let { texte }: { texte: TexteCourt } = $props();
</script>

<a class="texte" href="/textes/{texte.id}">
  <span class="titre">{texte.titre}</span>
  <span class="meta">
    <span class="sens {texte.principal.sens}">
      {texte.principal.sens === 'etend' ? '▲' : '▼'}
      <span>{court(texte.principal.code)}</span></span
    >
    <span class="discret"
      >voté le {date(texte.date)}, {legislature(texte.legislature)} législature</span
    >
  </span>
  <span class="visuellement-cache"
    >Le texte {phrase(texte.principal.code, texte.principal.sens)}.</span
  >
</a>

<style>
  .texte {
    display: block;
    padding: 0.7rem 0;
    border-bottom: 1px solid var(--filet);
    text-decoration: none;
  }
  .titre {
    display: block;
    font-weight: 650;
    font-size: 1.1rem;
    line-height: 1.3;
  }
  .texte:hover .titre {
    text-decoration: underline;
  }
  .meta {
    display: flex;
    flex-wrap: wrap;
    gap: 0.2rem 0.9rem;
    font-size: 0.92rem;
    margin-top: 0.2rem;
  }
  .sens {
    font-weight: 650;
  }
  .sens.etend {
    color: var(--favorable);
  }
  .sens.restreint {
    color: var(--defavorable);
  }
  .sens span {
    color: var(--encre);
  }
</style>
