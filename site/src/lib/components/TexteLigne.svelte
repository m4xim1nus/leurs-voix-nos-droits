<!--
  Un texte qualifié dans une liste : titre, date du vote décisif, droit principal et son sens, ou
  ceux du droit `droit` quand la liste est filtrée sur un droit.
-->
<script lang="ts">
  import { court, phrase, sousAngle } from '$lib/droits';
  import { date, legislature } from '$lib/format';
  import type { TexteCourt } from '$lib/server/vues';

  let { texte, droit = null }: { texte: TexteCourt; droit?: string | null } = $props();
  const vu = $derived(sousAngle(texte, droit));
</script>

<a class="texte" href="/textes/{texte.id}">
  <span class="titre">{texte.titre}</span>
  <span class="meta">
    <span class="sens {vu.sens}">
      {vu.sens === 'etend' ? '▲' : '▼'}
      <span>{court(vu.code)}</span></span
    >
    <span class="discret"
      >{texte.sans_vote
        ? 'adopté par le 49.3 sans vote final, non compté'
        : `voté le ${date(texte.date)}`}, {legislature(texte.legislature)} législature</span
    >
  </span>
  <span class="visuellement-cache">Le texte {phrase(vu.code, vu.sens)}.</span>
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
