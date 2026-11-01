<script lang="ts" module>
  import type { Source } from '$lib/types';

  /** Ligne du tableau des sources : `avant` garde l'ancienne clé, pour renommer les citations. */
  export type LigneSource = Source & { cle: string; avant: string };

  export const versLignes = (s: Record<string, Source>): LigneSource[] =>
    Object.entries(s ?? {}).map(([cle, v]) => ({ cle, avant: cle, ...v }));

  export const versSources = (lignes: LigneSource[]): Record<string, Source> =>
    Object.fromEntries(
      lignes
        .filter((s) => s.cle.trim())
        .map(({ cle, auteur, titre, date, url }) => [cle.trim(), { auteur, titre, date, url }])
    );
</script>

<script lang="ts">
  // Droits touchés, étiquettes, sources et vigilance : les mêmes formulaires pour la qualification
  // d'un texte et pour une version propre au Sénat (règle 24). Avec `suivi`, ni rôle ni sens (règle 22).
  import type { DroitQualifie, Grille, Vigilance } from '$lib/types';

  let {
    droits = $bindable(),
    etiquettes = $bindable(),
    vigilance = $bindable(),
    sources = $bindable(),
    grille,
    bibliotheque,
    suivi = false
  }: {
    droits: DroitQualifie[];
    etiquettes: string[];
    vigilance: Vigilance[];
    sources: LigneSource[];
    grille: Grille;
    bibliotheque: { cle: string; texte: string; source: Source }[];
    suivi?: boolean;
  } = $props();

  function ajouterDroit() {
    droits.push({
      code: '',
      role: droits.some((d) => d.role === 'principal') ? 'secondaire' : 'principal',
      sens: 'restreint',
      sources: [],
      justification: ''
    });
  }

  function basculer(liste: string[], cle: string) {
    const i = liste.indexOf(cle);
    if (i >= 0) liste.splice(i, 1);
    else liste.push(cle);
  }

  function ajouterSource(s?: { cle: string; source: Source }) {
    let cle = s?.cle ?? '';
    while (cle && sources.some((x) => x.cle === cle)) cle += '-bis';
    const v = s?.source ?? { auteur: '', titre: '', date: '', url: '' };
    sources.push({ cle, avant: cle, ...v });
  }

  /** Renommer une source met à jour les droits et la vigilance qui la citent. */
  function renommer(l: LigneSource) {
    const nouveau = l.cle.trim();
    if (l.avant && nouveau && nouveau !== l.avant)
      for (const liste of [...droits.map((d) => d.sources), ...vigilance.map((v) => v.sources)]) {
        const i = liste.indexOf(l.avant);
        if (i >= 0) liste[i] = nouveau;
      }
    l.cle = nouveau;
    l.avant = nouveau;
  }

  function retirerSource(i: number) {
    const cle = sources[i].cle;
    for (const liste of [...droits.map((d) => d.sources), ...vigilance.map((v) => v.sources)]) {
      const j = liste.indexOf(cle);
      if (j >= 0) liste.splice(j, 1);
    }
    sources.splice(i, 1);
  }

  let choixBibliotheque = $state('');
</script>

<h3>Droits touchés</h3>
<p class="discret">
  {#if !suivi}Un droit principal ; le sens se lit du point de vue des droits des personnes (règle
    1).{/if} Une justification courte et au moins une source par droit.
</p>
{#each droits as d, i (i)}
  <div class="droit">
    <div class="ligne">
      <select bind:value={d.code} aria-label="Droit">
        <option value="" disabled>droit…</option>
        {#each grille.droits as g (g.code)}
          <option value={g.code} title={g.libelle}>{g.code}</option>
        {/each}
      </select>
      {#if !suivi}
        <select bind:value={d.role} aria-label="Rôle">
          <option value="principal">principal</option>
          <option value="secondaire">secondaire</option>
        </select>
        <select bind:value={d.sens} aria-label="Sens" class={d.sens}>
          <option value="restreint">restreint</option>
          <option value="etend">étend</option>
        </select>
      {/if}
      <span class="discret">sources :</span>
      {#each sources.filter((s) => s.cle) as s (s.cle)}
        <label class="ligne petite">
          <input
            type="checkbox"
            checked={d.sources.includes(s.cle)}
            onchange={() => basculer(d.sources, s.cle)}
          />
          {s.cle}
        </label>
      {:else}
        <span class="discret">(définir les sources plus bas)</span>
      {/each}
      <button type="button" class="lien" onclick={() => droits.splice(i, 1)}>retirer</button>
    </div>
    <textarea bind:value={d.justification} rows="2" placeholder="Justification, avec la source"
    ></textarea>
  </div>
{/each}
<button type="button" onclick={ajouterDroit}>+ droit</button>

{#if !suivi}
  <h3>Étiquettes</h3>
  <div class="ligne">
    {#each grille.etiquettes as e (e.code)}
      <label class="ligne petite" title={e.libelle}>
        <input
          type="checkbox"
          checked={etiquettes.includes(e.code)}
          onchange={() => basculer(etiquettes, e.code)}
        />
        {e.code}
      </label>
    {/each}
  </div>
{/if}

<h3>Sources</h3>
<p class="discret">
  Avis de la CNCDH, du Défenseur des droits, de la CNIL, décision du Conseil constitutionnel,
  analyse d'ONG… (règle 7). La clé sert à les citer.
</p>
<table class="sources">
  <thead>
    <tr><th>Clé</th><th>Auteur</th><th>Titre</th><th>Date</th><th>URL</th><th></th></tr>
  </thead>
  <tbody>
    {#each sources as s, i (i)}
      <tr>
        <td
          ><input
            type="text"
            bind:value={s.cle}
            onchange={() => renommer(s)}
            class="mono"
            size="14"
          /></td
        >
        <td><input type="text" bind:value={s.auteur} size="16" /></td>
        <td><input type="text" bind:value={s.titre} /></td>
        <td>
          <input
            type="text"
            bind:value={s.date}
            placeholder="AAAA-MM-JJ"
            pattern={'\\d{4}(-\\d{2}(-\\d{2})?)?'}
            title="AAAA-MM-JJ, ou AAAA-MM si le document n'est daté qu'au mois"
            size="10"
          />
        </td>
        <td><input type="url" bind:value={s.url} /></td>
        <td><button type="button" class="lien" onclick={() => retirerSource(i)}>retirer</button></td
        >
      </tr>
    {/each}
  </tbody>
</table>
<div class="ligne">
  <button type="button" onclick={() => ajouterSource()}>+ source</button>
  {#if bibliotheque.length}
    <select bind:value={choixBibliotheque} aria-label="Reprendre une source d'un autre texte">
      <option value="">reprendre une source d'un autre texte…</option>
      {#each bibliotheque as b, i (i)}
        <option value={String(i)}
          >{b.cle} ({b.texte}) : {b.source.auteur}, {b.source.titre.slice(0, 60)}</option
        >
      {/each}
    </select>
    <button
      type="button"
      disabled={!choixBibliotheque}
      onclick={() => {
        ajouterSource(bibliotheque[Number(choixBibliotheque)]);
        choixBibliotheque = '';
      }}>reprendre</button
    >
  {/if}
</div>

{#if !suivi}
  <h3>Points de vigilance</h3>
  <p class="discret">
    Critiques sourcées affichées à côté du jugement, sans le modifier (règle 5).
  </p>
  {#each vigilance as v, i (i)}
    <div class="droit">
      <textarea bind:value={v.texte} rows="2"></textarea>
      <div class="ligne">
        <span class="discret">sources :</span>
        {#each sources.filter((s) => s.cle) as s (s.cle)}
          <label class="ligne petite">
            <input
              type="checkbox"
              checked={v.sources.includes(s.cle)}
              onchange={() => basculer(v.sources, s.cle)}
            />
            {s.cle}
          </label>
        {/each}
        <button type="button" class="lien" onclick={() => vigilance.splice(i, 1)}>retirer</button>
      </div>
    </div>
  {/each}
  <button type="button" onclick={() => vigilance.push({ texte: '', sources: [] })}>
    + point de vigilance
  </button>
{/if}

<style>
  .droit {
    border-left: 3px solid var(--bord);
    padding: 0.3rem 0 0.3rem 0.6rem;
    margin: 0.5rem 0;
  }
  .droit textarea {
    margin-top: 0.3rem;
  }
  .petite {
    gap: 0.2rem;
    font-size: 0.88rem;
  }
  select.etend {
    color: var(--etend);
  }
  select.restreint {
    color: var(--restreint);
  }
  .sources input {
    width: 100%;
  }
</style>
