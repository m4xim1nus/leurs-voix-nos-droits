<script lang="ts">
  import { enhance } from '$app/forms';
  import { LIBELLES_ALERTE } from '$lib/alertes';
  import { date, dateHeure } from '$lib/format';
  import { LIBELLES_ETAT } from '$lib/llm';
  import type { Groupe, PropositionAffichee } from './+page.server';

  let { data, form } = $props();

  const SECTIONS = {
    pret: {
      titre: 'Prêt à relire',
      aide: 'Un vote a eu lieu, ou une source a publié sur le texte (veille), et la proposition du LLM passe les contrôles. « Mise à jour mineure » : rien ne change du statut, du droit principal, du sens ni du décisif.'
    },
    methode: {
      titre: 'Question de méthode',
      aide: 'La proposition signale un cas que les règles ne prévoient pas : à trancher (docs/A_VALIDER.md) avant de valider. Une fois la règle fixée, « Question tranchée » renvoie la carte dans sa section.'
    },
    main: {
      titre: 'À faire à la main',
      aide: 'Un vote a eu lieu, sans proposition utilisable : LLM coupé, proposition écartée par les contrôles, ou alerte que le LLM ne traite pas d’office (Sénat). Une proposition peut se demander.'
    },
    'a-venir': {
      titre: 'À venir',
      aide: 'Textes inscrits en séance : rien à qualifier avant le vote (« inscrit » ne veut pas dire voté). Une fiche de suivi peut se demander au LLM pour un texte qu’on veut suivre.'
    }
  } as const;

  const LIBELLES_MODE: Record<string, string> = {
    complet: 'qualification',
    ecart: 'relecture de l’écart',
    requalification: 'requalification',
    suivi: 'fiche de suivi',
    senat: 'vote du Sénat',
    veille: 'veille des sources'
  };
  const usd = (x: number) =>
    `${x.toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} $`;
  const enService = $derived(data.llm.etat === 'en-service');
  const compte = (n: number, mot: string) => `${n} ${mot}${n > 1 ? 's' : ''}`;
</script>

<svelte:head><title>À traiter · admin</title></svelte:head>

<h1>À traiter</h1>
<p class="resume">
  {#each data.sections as s (s.cle)}
    <a href="#{s.cle}" class="compteur" class:vide={!s.groupes.length}
      ><strong>{s.groupes.length}</strong> {SECTIONS[s.cle].titre.toLowerCase()}</a
    >
  {/each}
  {#if data.nMineures}<span class="discret"
      >dont {compte(data.nMineures, 'mise')} à jour mineure{data.nMineures > 1 ? 's' : ''}</span
    >{/if}
</p>
<p class="discret">
  {compte(data.nAlertes, 'alerte')}. Une alerte est un avertissement : elle ne bloque ni les données
  ni la publication, et disparaît quand la qualification en tient compte, même avant publication.
  LLM : {LIBELLES_ETAT[data.llm.etat]} (<a href="/llm">réglages</a>). Le LLM propose, il ne valide
  ni ne publie : une proposition chargée passe « à relire » sur la fiche, où elle se corrige et se
  valide comme toute qualification.
</p>

{#if form?.erreur}
  <ul class="messages"><li class="erreur">{form.erreur}</li></ul>
{:else if form?.ok}
  <ul class="messages"><li class="ok">{form.ok}</li></ul>
{/if}

{#snippet proposition(p: PropositionAffichee)}
  <div class="proposition" class:echec={p.statut === 'echec'}>
    <h4>
      Proposition du LLM : {LIBELLES_MODE[p.mode] ?? p.mode}
      {#if p.mineure}<span class="pastille valide">mise à jour mineure</span>{/if}
      {#if p.methode}<span class="pastille a-relire">question de méthode</span>{/if}
      <span class="discret"> · {dateHeure(p.date)} · {p.modele} · {usd(p.cout_usd)}</span>
    </h4>
    {#if p.relecture.publication}
      {@const pub = p.relecture.publication}
      <p class="discret">
        Publication du {date(pub.date)} : {pub.auteur},
        <a href={pub.lien} rel="external noopener" target="_blank">{pub.titre}</a>{#if pub.raison}. {pub.raison}{/if}
      </p>
    {/if}
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
      {#if p.relecture.action}<p class="action">{p.relecture.action}</p>{/if}
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
        <details>
          <summary>Sources et extraits ({Object.keys(p.doc.sources).length})</summary>
          <ul>
            {#each Object.entries(p.doc.sources) as [cle, s] (cle)}
              <li>
                <a href={s.url} rel="external noopener" target="_blank">{s.auteur}, {s.titre}</a>
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
        <details open={p.methode}>
          <summary>Points d’attention</summary>
          <ul>
            {#each p.relecture.controles?.points ?? [] as x, i (i)}<li class="fort">{x}</li>{/each}
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
    {#if p.relecture.methode_tranchee}
      <p class="discret">
        Question de méthode tranchée le {dateHeure(p.relecture.methode_tranchee.le)} par {p
          .relecture.methode_tranchee.par} : relire la proposition à la lumière de la règle.
      </p>
    {/if}
    <div class="gestes">
      {#if p.methode}
        <form method="POST" action="?/trancher" use:enhance>
          <input type="hidden" name="id" value={p.id} />
          <button
            title="La règle est fixée dans la méthode : la carte quitte « Question de méthode »"
            >Question tranchée</button
          >
        </form>
      {/if}
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
    {#if form?.erreur && 'id' in form && form.id === p.id}<p class="erreur-texte">
        {form.erreur}
      </p>{/if}
  </div>
{/snippet}

{#snippet carte(g: Groupe)}
  <section class="carte groupe">
    <h3>
      <a href="/textes/{g.dossier}">{g.titre}</a>
      {#if g.echeance}<span class="pastille a-suivre">en séance le {date(g.echeance)}</span>{/if}
    </h3>
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
      {@render proposition(p)}
    {/each}
    {#if !g.propositions.length && g.alertes.length}
      {#if g.demande}
        <p class="discret">
          Proposition demandée le {dateHeure(g.demande.demande_le)} par {g.demande.demande_par} : elle
          arrivera après la prochaine passe de données.
        </p>
      {:else if enService}
        <form method="POST" action="?/demander" use:enhance>
          <input type="hidden" name="alerte" value={g.alertes[0].id} />
          <input type="hidden" name="dossier" value={g.dossier} />
          <button
            >{g.section === 'a-venir'
              ? 'Demander une fiche de suivi au LLM'
              : 'Demander une proposition au LLM'}</button
          >
        </form>
      {/if}
    {/if}
  </section>
{/snippet}

{#each data.sections as s (s.cle)}
  <h2 id={s.cle}>{SECTIONS[s.cle].titre} ({s.groupes.length})</h2>
  <p class="discret">{SECTIONS[s.cle].aide}</p>
  {#each s.groupes as g (g.dossier)}
    {@render carte(g)}
  {:else}
    <p class="discret">Rien.</p>
  {/each}
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
  .resume {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem 1rem;
    align-items: baseline;
  }
  .compteur {
    text-decoration: none;
    padding: 0.2rem 0.6rem;
    border: 1px solid var(--bord);
    border-radius: var(--rayon);
    background: var(--surface);
    color: var(--texte);
  }
  .compteur.vide {
    color: var(--texte-2);
  }
  .groupe h3 {
    font-size: 1.05rem;
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
  .proposition h4 {
    font-size: 0.95rem;
    margin: 0 0 0.3rem;
  }
  .action {
    background: var(--surface-2);
    border-radius: var(--rayon);
    padding: 0.4rem 0.6rem;
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
