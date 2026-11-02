<script lang="ts">
  import { enhance } from '$app/forms';
  import { LIBELLES_ALERTE } from '$lib/alertes';
  import { date, dateHeure } from '$lib/format';
  import { LIBELLES_ETAT } from '$lib/llm';

  let { data, form } = $props();

  const LIBELLES_MODE: Record<string, string> = {
    complet: 'qualification',
    ecart: 'relecture de l’écart',
    requalification: 'requalification',
    suivi: 'fiche de suivi',
    senat: 'vote du Sénat'
  };
  const usd = (x: number) =>
    `${x.toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} $`;
  const nProps = $derived(data.file.reduce((n, g) => n + g.propositions.length, 0));
</script>

<svelte:head><title>À traiter · admin</title></svelte:head>

<h1>À traiter</h1>
<p class="discret">
  {data.file.length} texte{data.file.length > 1 ? 's' : ''}, {data.nAlertes} alerte{data.nAlertes >
  1
    ? 's'
    : ''}{#if nProps}, {nProps} proposition{nProps > 1 ? 's' : ''} du LLM{/if}. Les textes inscrits
  en séance d’abord, par date de séance, puis les plus récentes alertes. Une alerte est un
  avertissement : elle ne bloque ni les données ni la publication, et disparaît quand la
  qualification en tient compte, même avant publication. « Inscrit » ne veut pas dire voté.
</p>
<p class="discret">
  LLM : {LIBELLES_ETAT[data.llm.etat]} (<a href="/llm">réglages</a>). Le LLM propose, il ne valide
  ni ne publie : charger une proposition la met « à relire » sur la fiche, où elle se corrige et se
  valide comme toute qualification.
</p>

{#if form?.erreur}
  <ul class="messages"><li class="erreur">{form.erreur}</li></ul>
{:else if form?.ok}
  <ul class="messages"><li class="ok">{form.ok}</li></ul>
{/if}

{#each data.file as g (g.dossier)}
  <section class="carte groupe">
    <h2>
      <a href="/textes/{g.dossier}">{g.titre}</a>
      {#if g.echeance}<span class="pastille a-relire">en séance le {date(g.echeance)}</span>{/if}
    </h2>
    <ul class="alertes">
      {#each g.alertes as a (a.id)}
        <li>
          <strong>{LIBELLES_ALERTE[a.type]}</strong>
          <span class="discret">· {date(a.date)} · {a.detail}</span>
        </li>
      {/each}
    </ul>
    {#if g.note}<p class="note">Note interne : {g.note}</p>{/if}

    {#each g.propositions as p (p.id)}
      <div class="proposition" class:echec={p.statut === 'echec'}>
        <h3>
          Proposition du LLM : {LIBELLES_MODE[p.mode] ?? p.mode}
          <span class="discret"> · {dateHeure(p.date)} · {p.modele} · {usd(p.cout_usd)}</span>
        </h3>
        {#if p.statut === 'echec'}
          <p class="erreur-texte">
            Proposition écartée par les contrôles : {p.motif ?? p.relecture.echec}
          </p>
          {#if p.relecture.controles?.erreurs?.length}
            <ul class="discret">
              {#each p.relecture.controles.erreurs as e, i (i)}<li>{e}</li>{/each}
            </ul>
          {/if}
        {:else}
          <p><strong>{p.jugement}</strong></p>
          {#if p.doc?.resume}<p>{p.doc.resume}</p>{/if}
          {#if p.ecarts?.length}
            <details>
              <summary>Écart avec la qualification actuelle ({p.ecarts.length})</summary>
              <ul>
                {#each p.ecarts as e, i (i)}<li>{e}</li>{/each}
              </ul>
            </details>
          {/if}
          {#if p.doc?.sources && Object.keys(p.doc.sources).length}
            <details open>
              <summary>Sources et extraits</summary>
              <ul>
                {#each Object.entries(p.doc.sources) as [cle, s] (cle)}
                  <li>
                    <a href={s.url} rel="external noopener" target="_blank">{s.auteur}, {s.titre}</a
                    >
                    <span class="discret">({s.date}, clé {cle})</span>
                    {#each (p.relecture.extraits ?? []).filter( (e) => e.startsWith(`${cle} :`) ) as e, i (i)}
                      <blockquote>{e.slice(cle.length + 2).trim()}</blockquote>
                    {/each}
                  </li>
                {/each}
              </ul>
            </details>
          {/if}
          {#if p.relecture.controles?.points?.length || p.relecture.points_attention?.length}
            <details open>
              <summary>Points d’attention</summary>
              <ul>
                {#each p.relecture.controles?.points ?? [] as x, i (i)}<li class="fort">
                    {x}
                  </li>{/each}
                {#each (p.relecture.points_attention ?? []).filter((x) => !x.startsWith('CAS NON PRÉVU')) as x, i (i)}<li
                  >
                    {x}
                  </li>{/each}
              </ul>
            </details>
          {/if}
          {#if p.relecture.incertitudes?.length || p.relecture.controles?.avertissements?.length}
            <details>
              <summary>Incertitudes et avertissements</summary>
              <ul>
                {#each p.relecture.incertitudes ?? [] as x, i (i)}<li>{x}</li>{/each}
                {#each p.relecture.controles?.avertissements ?? [] as x, i (i)}<li class="discret">
                    {x}
                  </li>{/each}
              </ul>
            </details>
          {/if}
        {/if}
        <div class="gestes">
          {#if p.statut === 'proposee' && p.doc?.statut !== 'sans-source'}
            <form method="POST" action="?/charger" use:enhance>
              <input type="hidden" name="id" value={p.id} />
              <button class="principal">Charger « à relire »</button>
            </form>
          {/if}
          <form method="POST" action="?/ecarter" use:enhance class="ecarter">
            <input type="hidden" name="id" value={p.id} />
            <label class="visuellement-cache" for="motif-{p.id}">Motif</label>
            <input
              id="motif-{p.id}"
              name="motif"
              type="text"
              size="30"
              placeholder={p.statut === 'echec' ? 'vu' : 'motif (facultatif)'}
            />
            <button>{p.statut === 'echec' ? 'Retirer' : 'Écarter la proposition'}</button>
          </form>
        </div>
        {#if form?.erreur && form.id === p.id}<p class="erreur-texte">{form.erreur}</p>{/if}
      </div>
    {/each}
  </section>
{:else}
  <p>Rien à traiter.</p>
{/each}

<h2>Notes internes</h2>
<p class="discret">
  Pense-bêtes saisis sur les fiches, jamais publiés. Une note se retire en la vidant sur la fiche.
</p>
{#if data.notes.length}
  <table>
    <thead>
      <tr>
        <th>Date</th>
        <th>Texte</th>
        <th>Note</th>
      </tr>
    </thead>
    <tbody>
      {#each data.notes as n (n.dossier_an)}
        <tr>
          <td>{date(n.modifie_le)}</td>
          <td><a href="/textes/{n.dossier_an}">{n.titre ?? n.dossier_an}</a></td>
          <td class="note-texte"
            >{n.texte}
            <div class="discret">{n.modifie_par}</div></td
          >
        </tr>
      {/each}
    </tbody>
  </table>
{:else}
  <p>Aucune note.</p>
{/if}

<style>
  .groupe h2 {
    font-size: 1.1rem;
    margin: 0 0 0.4rem;
  }
  .alertes {
    margin: 0.2rem 0;
    padding-left: 1.1rem;
  }
  .note {
    font-size: 0.9rem;
  }
  .note-texte {
    white-space: pre-line;
  }
  .proposition {
    border-left: 3px solid var(--accent);
    padding: 0.2rem 0 0.2rem 0.8rem;
    margin-top: 0.8rem;
  }
  .proposition.echec {
    border-left-color: var(--erreur);
  }
  .proposition h3 {
    font-size: 1rem;
    margin: 0 0 0.3rem;
  }
  blockquote {
    margin: 0.2rem 0 0.4rem 1rem;
    font-size: 0.9rem;
    color: var(--texte-2);
  }
  .fort {
    font-weight: 600;
  }
  .erreur-texte {
    color: var(--erreur);
  }
  .gestes {
    display: flex;
    flex-wrap: wrap;
    gap: 0.6rem;
    align-items: center;
    margin-top: 0.5rem;
  }
  .ecarter {
    display: flex;
    gap: 0.4rem;
  }
</style>
