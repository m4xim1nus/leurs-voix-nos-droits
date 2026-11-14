<!--
  Les droits de la grille en tuiles, chacune liée à la page du droit : combien de textes le
  restreignent (▼) et l'étendent (▲), en barre et en chiffres, comme les tuiles de la page des textes.
  Avec `libelles`, la définition du droit s'affiche sous son nom.
-->
<script lang="ts">
  import { pluriel } from '$lib/format';

  interface Tuile {
    code: string;
    court: string;
    libelle?: string;
    restreint: number;
    etend: number;
  }
  let { droits, libelles = false }: { droits: Tuile[]; libelles?: boolean } = $props();
</script>

<ul class="tuiles" class:libelles>
  {#each droits as d (d.code)}
    {@const total = d.restreint + d.etend}
    <li>
      <a class="tuile" href="/droits/{d.code}">
        <span class="nom">{d.court}</span>
        {#if libelles && d.libelle}<span class="libelle">{d.libelle}.</span>{/if}
        <span class="bas">
          <span class="barre" aria-hidden="true"
            >{#if total}<span class="r" style:width="{(100 * d.restreint) / total}%"></span><span
                class="e"
                style:width="{(100 * d.etend) / total}%"
              ></span>{/if}</span
          >
          <span class="compte" aria-hidden="true"
            ><span class="defavorable">▼ {d.restreint}</span><span class="favorable"
              >▲ {d.etend}</span
            ></span
          ><span class="visuellement-cache"
            >{pluriel(
              d.restreint,
              'texte restreint',
              'textes restreignent',
              'aucun texte ne restreint'
            )} ce droit, {pluriel(
              d.etend,
              'texte l’étend',
              'textes l’étendent',
              'aucun ne l’étend'
            )}.</span
          >
        </span>
      </a>
    </li>
  {/each}
</ul>

<style>
  .tuiles {
    list-style: none;
    padding: 0;
    margin: 1rem 0 0;
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(min(100% / 2 - 0.3rem, 13rem), 1fr));
    gap: 0.6rem;
  }
  .tuiles.libelles {
    grid-template-columns: repeat(auto-fill, minmax(min(100%, 20rem), 1fr));
  }
  .tuiles li {
    display: flex;
    max-width: none;
  }
  .tuile {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    padding: 0.8rem 0.9rem;
    border: 1px solid var(--filet);
    border-radius: 10px;
    background: var(--papier);
    color: var(--encre);
    text-decoration: none;
  }
  .tuile:hover {
    border-color: var(--encre);
  }
  .tuile:hover .nom {
    text-decoration: underline;
  }
  .nom {
    font-weight: 700;
    line-height: 1.2;
  }
  .libelles .nom {
    font-family: var(--titre);
    font-stretch: 78%;
    font-weight: 750;
    font-size: 1.3rem;
  }
  .libelle {
    font-size: 0.92rem;
    line-height: 1.4;
    color: var(--ardoise);
  }
  .bas {
    margin-top: auto;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  .barre {
    display: flex;
    height: 6px;
    border-radius: 3px;
    overflow: hidden;
    background: var(--filet);
  }
  .barre .r {
    background: var(--defavorable);
  }
  .barre .e {
    background: var(--favorable);
  }
  .compte {
    display: flex;
    gap: 1rem;
    font-size: 0.95rem;
    font-weight: 700;
  }
</style>
