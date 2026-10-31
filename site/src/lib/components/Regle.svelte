<!--
  Règle graduée (docs/CONCEPTION.md, direction visuelle) : une ligne par groupe ou député, de 0 à
  100 % de votes favorables aux droits, graduée tous les 10 points. Le curseur porte la couleur
  officielle du groupe ; le chiffre est toujours écrit à côté. Avec `onchoisir`,
  chaque ligne devient un bouton qui sert de filtre (fiches groupe et député : un droit, ses textes).
-->
<script lang="ts">
  import { pluriel, pourcent } from '$lib/format';

  interface Ligne {
    cle: string;
    libelle: string;
    couleur?: string;
    href?: string;
    score: number | null;
    n_textes?: number;
    /** Ligne mise en avant (le député sur sa fiche). */
    avant?: boolean;
  }

  let {
    lignes,
    legende = true,
    choisie = null,
    onchoisir
  }: {
    lignes: Ligne[];
    legende?: boolean;
    /** Ligne retenue comme filtre ; les autres s'estompent. */
    choisie?: string | null;
    onchoisir?: (cle: string) => void;
  } = $props();

  const GRADUATIONS = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100];
</script>

<div class="regle">
  {#if legende}
    <div class="ligne echelle" aria-hidden="true">
      <span></span>
      <div class="piste">
        <span class="bout defavorable">0 %</span>
        <span class="milieu">50 %</span>
        <span class="bout favorable">100 %</span>
      </div>
      <span></span>
    </div>
  {/if}
  {#snippet contenu(l: Ligne, lien: boolean)}
    <span class="nom">
      {#if l.href && lien}
        <a href={l.href} class:sigle={l.couleur} style:--c={l.couleur}>{l.libelle}</a>
      {:else}
        <span class:sigle={l.couleur} style:--c={l.couleur}>{l.libelle}</span>
      {/if}
    </span>
    <span class="piste" aria-hidden="true">
      {#each GRADUATIONS as g (g)}
        <span class="grad" class:majeure={g % 50 === 0} style:left="{g}%"></span>
      {/each}
      {#if l.score !== null}
        <span class="curseur" style:left="{l.score}%" style:--c={l.couleur ?? 'var(--encre)'}
        ></span>
      {/if}
    </span>
    <span class="valeur">
      <span class="chiffre">{pourcent(l.score)}</span>
      {#if l.n_textes !== undefined}
        <span class="visuellement-cache">
          de votes favorables aux droits, sur {pluriel(l.n_textes, 'texte')}</span
        >
      {/if}
    </span>
  {/snippet}
  <ul class:estompe={choisie !== null}>
    {#each lignes as l (l.cle)}
      <li class:avant={l.avant} class:choisie={l.cle === choisie}>
        {#if onchoisir}
          <button
            type="button"
            class="ligne"
            aria-pressed={l.cle === choisie}
            onclick={() => onchoisir(l.cle)}>{@render contenu(l, false)}</button
          >
        {:else}
          <div class="ligne">{@render contenu(l, true)}</div>
        {/if}
      </li>
    {/each}
  </ul>
  {#if legende}
    <p class="petit discret note">
      Part des votes favorables aux droits, pondérée texte par texte. Abstentions et absences hors
      calcul.
    </p>
  {/if}
</div>

<style>
  .regle {
    /* Largeur fixe : chaque ligne est sa propre grille, les colonnes doivent s'aligner. */
    --nom: clamp(6rem, 32%, 14rem);
    margin: 1rem 0 1.5rem;
  }
  ul {
    list-style: none;
    margin: 0;
    padding: 0;
  }
  li {
    max-width: none;
  }
  .ligne {
    display: grid;
    grid-template-columns: var(--nom) 1fr 3.4rem;
    align-items: center;
    gap: 0.75rem;
    max-width: none;
    min-height: 2.1rem;
  }
  .avant .ligne {
    background: var(--plan);
    margin: 0 -0.5rem;
    padding: 0 0.5rem;
    border-radius: 3px;
  }
  .nom {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .nom a {
    text-decoration: none;
  }
  /* Sur téléphone, le libellé passe à la ligne plutôt que d'être tronqué. */
  @media (max-width: 40rem) {
    .nom,
    .nom :global(.sigle) {
      white-space: normal;
      overflow-wrap: anywhere;
      hyphens: auto;
    }
  }
  .nom a:hover {
    text-decoration: underline;
  }
  .piste {
    display: block;
    position: relative;
    height: 1.4rem;
    border-bottom: 1.5px solid var(--encre);
  }
  .grad {
    position: absolute;
    bottom: 0;
    width: 1px;
    height: 0.35rem;
    background: var(--ardoise);
    transform: translateX(-0.5px);
  }
  .grad.majeure {
    height: 0.7rem;
    background: var(--encre);
  }
  .curseur {
    position: absolute;
    bottom: -0.45rem;
    width: 0.5rem;
    height: 1.55rem;
    transform: translateX(-50%);
    background: var(--c);
    border: 1.5px solid var(--encre);
    border-radius: 1px;
  }
  button.ligne {
    width: 100%;
    font: inherit;
    color: inherit;
    text-align: left;
    background: none;
    border: 0;
    padding: 0 0.5rem;
    margin: 0 -0.5rem;
    box-sizing: content-box;
    border-radius: 3px;
    cursor: pointer;
  }
  button.ligne:hover,
  .choisie button.ligne {
    background: var(--plan);
  }
  button.ligne:hover .nom,
  .choisie .nom {
    text-decoration: underline;
    text-underline-offset: 0.2em;
  }
  .choisie .nom {
    font-weight: 700;
  }
  .estompe li:not(.choisie) {
    opacity: 0.45;
  }
  .estompe li:not(.choisie):hover {
    opacity: 1;
  }
  .valeur {
    text-align: right;
    font-size: 1.25rem;
  }
  .echelle .piste {
    border: 0;
    height: 1.2rem;
    font-size: 0.8rem;
    font-weight: 650;
  }
  .echelle .piste span {
    position: absolute;
    bottom: 0;
  }
  .bout.defavorable {
    left: 0;
  }
  .milieu {
    left: 50%;
    transform: translateX(-50%);
    color: var(--ardoise);
  }
  .bout.favorable {
    right: 0;
  }
  .note {
    margin-top: 0.75rem;
  }
</style>
