<!--
  Un texte qualifié dans une liste : titre, date du vote décisif, droit principal et son sens, ou
  ceux du droit `droit` quand la liste est filtrée sur un droit, et où en est le texte.
-->
<script lang="ts">
  import { court, phrase, sousAngle } from '$lib/droits';
  import { date, etatEnListe, legislature } from '$lib/format';
  import type { TexteListe } from '$lib/server/vues';

  let { texte, droit = null }: { texte: TexteListe; droit?: string | null } = $props();
  const vu = $derived(
    texte.principal ? sousAngle({ ...texte, principal: texte.principal }, droit) : null
  );
  const etat = $derived(etatEnListe(texte.etat, texte.etape));
</script>

<a class="texte" href="/textes/{texte.id}">
  <span class="titre">{texte.titre}</span>
  <span class="meta">
    {#if vu}
      <span class="sens {vu.sens}">
        {vu.sens === 'etend' ? '▲' : '▼'}
        <span>{court(vu.code)}</span></span
      >
    {/if}
    <span class="discret"
      >{#if texte.seul}{vu ? 'voté' : 'vote affiché, non compté,'} au seul Sénat, le {date(
          texte.date
        )}{:else}{texte.sans_vote
          ? 'adopté par le 49.3 sans vote final, non compté'
          : `voté le ${date(texte.date)}`}, {legislature(texte.legislature)} législature{/if}</span
    >
    {#if etat}<span class="etat">{etat}</span>{/if}
  </span>
  {#if vu}<span class="visuellement-cache">Le texte {phrase(vu.code, vu.sens)}.</span>{/if}
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
  .etat {
    font-weight: 600;
  }
</style>
