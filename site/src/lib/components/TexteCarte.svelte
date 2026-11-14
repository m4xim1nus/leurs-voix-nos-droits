<!--
  Un texte qualifié en carte, pour la page des textes : le droit et son sens d'abord, en bande de
  couleur ; puis le titre officiel, la phrase en mots simples dessous, la date du vote et où en est
  le texte. Sous l'angle du droit `droit` quand la liste est filtrée sur un droit, comme TexteLigne.
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
  const quand = $derived(
    texte.seul
      ? `Voté au seul Sénat, le ${date(texte.date)}`
      : texte.sans_vote
        ? 'Adopté par le 49.3 sans vote final'
        : `Voté le ${date(texte.date)}, ${legislature(texte.legislature)} législature`
  );
  const aussi = $derived(texte.droits.filter((d) => d.code !== vu?.code).map((d) => court(d.code)));
</script>

<a class="carte {vu?.sens ?? 'affiche'}" href="/textes/{texte.id}">
  <span class="bande">
    {#if vu}
      <span class="sens" aria-hidden="true">{vu.sens === 'etend' ? '▲ Étend' : '▼ Restreint'}</span>
      <span class="droit">{court(vu.code)}</span>
      <span class="visuellement-cache">Le texte {phrase(vu.code, vu.sens)}.</span>
    {:else}
      <span class="sens">Vote affiché</span>
      <span class="droit">non compté</span>
    {/if}
  </span>
  <span class="corps">
    <span class="titre">{texte.titre}</span>
    {#if texte.simple}<span class="simple">{texte.simple}</span>{/if}
    <span class="meta"
      >{quand}{#if etat}&nbsp;· <span class="etat">{etat}</span>{/if}</span
    >
    {#if aussi.length}<span class="aussi">Touche aussi : {aussi.join(', ')}</span>{/if}
  </span>
</a>

<style>
  .carte {
    display: flex;
    border: 1px solid var(--filet);
    border-radius: 10px;
    overflow: hidden;
    text-decoration: none;
    background: var(--papier);
    color: var(--encre);
  }
  .carte.etend {
    border-color: var(--favorable-pale);
  }
  .carte.restreint {
    border-color: var(--defavorable-pale);
  }
  .bande {
    flex: 0 0 7.5rem;
    display: flex;
    flex-direction: column;
    justify-content: center;
    gap: 0.3rem;
    padding: 0.9rem 0.75rem;
    background: var(--ardoise);
    color: var(--papier);
  }
  .etend .bande {
    background: var(--favorable);
  }
  .restreint .bande {
    background: var(--defavorable);
  }
  .sens {
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.05em;
    text-transform: uppercase;
  }
  .droit {
    font-family: var(--titre);
    font-size: 1.05rem;
    font-weight: 800;
    font-stretch: 75%;
    line-height: 1.1;
  }
  .corps {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
    padding: 0.85rem 1rem;
  }
  .titre {
    font-weight: 700;
    font-size: 1.1rem;
    line-height: 1.3;
  }
  .carte:hover .titre {
    text-decoration: underline;
  }
  .simple {
    line-height: 1.4;
  }
  .meta,
  .aussi {
    font-size: 0.85rem;
    line-height: 1.4;
    color: var(--ardoise);
  }
  .etat {
    font-weight: 600;
    color: var(--encre);
  }
  @media (max-width: 30rem) {
    .carte {
      flex-direction: column;
    }
    .bande {
      flex: none;
      flex-direction: row;
      flex-wrap: wrap;
      align-items: baseline;
      gap: 0.5rem;
      padding: 0.5rem 0.9rem;
    }
  }
</style>
