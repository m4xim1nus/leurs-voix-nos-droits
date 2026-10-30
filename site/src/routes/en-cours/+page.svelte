<!--
  Textes retenus encore en navette, rangés par échéance. Des faits : l'ordre du jour, le dernier vote
  public de l'Assemblée et, pour un texte qualifié, le sens lu sur le texte alors voté.
-->
<script lang="ts">
  import Sources from '$lib/components/Sources.svelte';
  import Ventilations from '$lib/components/Ventilations.svelte';
  import { court, phrase } from '$lib/droits';
  import {
    date,
    inscription,
    listeDates,
    pluriel,
    POSITION_GROUPE,
    voteDeLecture
  } from '$lib/format';
  import { FIN_SESSION, NOM } from '$lib/site';
  import type { Echeance, PointAgenda, TexteEnCours } from '$lib/types';

  let { data } = $props();

  const SECTIONS: { echeance: Echeance; titre: string }[] = [
    { echeance: 'inscrit', titre: 'Inscrits à l’ordre du jour' },
    { echeance: 'AN', titre: 'Attendus à l’Assemblée' },
    { echeance: 'SN', titre: 'Attendus au Sénat' },
    { echeance: 'CMP', titre: 'En commission mixte paritaire' },
    { echeance: 'inconnue', titre: 'Suite pas encore connue' }
  ];
  const parEcheance = (e: Echeance) => data.textes.filter((t) => t.echeance === e);
  const inscrits = $derived(parEcheance('inscrit').length);
  const finDeSession = $derived(data.dateEtat > FIN_SESSION);
  const eventuel = (p: PointAgenda[]) =>
    p.some((x) => x.etat === 'eventuel') ? ' (réunion éventuelle)' : '';
  const dates = (t: TexteEnCours) =>
    t.seances.length ? t.seances.map((s) => s.date) : [t.etat.seance_inscrite!];
  const chambre = (t: TexteEnCours) => (t.seances.length ? 'AN' : t.chambre);
</script>

<svelte:head>
  <title>Textes en cours, {NOM}</title>
  <meta
    name="description"
    content="Les textes qui touchent aux droits et libertés encore en navette : ce qui est inscrit à l’ordre du jour et le dernier vote de chaque groupe."
  />
  <link
    rel="alternate"
    type="application/rss+xml"
    title="Textes en cours, {NOM}"
    href="/en-cours/flux.xml"
  />
</svelte:head>

<h1>Textes en cours</h1>
<p class="chapo">
  Les textes retenus sur ce site qui poursuivent leur parcours au Parlement : où ils en sont, et
  comment chaque groupe a voté la dernière fois à l’Assemblée. État au {date(data.dateEtat)}.
</p>
<p>
  Un texte inscrit à l’ordre du jour n’est pas forcément examiné à cette date, ni voté. Les règles
  sont dans la <a href="/methodologie#en-cours">méthodologie</a>.
</p>
<p class="petit">
  Suivre ces textes : <a href="/en-cours/flux.xml">flux RSS</a>,
  <a href="/en-cours/agenda.ics">agenda à ajouter à votre calendrier</a>.
</p>

{#if finDeSession && !inscrits}
  <p>
    La session a pris fin le {date(FIN_SESSION)}, avant l’élection présidentielle : aucun texte
    retenu n’est inscrit à l’ordre du jour pour l’instant.
  </p>
{/if}

{#if !data.textes.length}
  <p>Aucun texte retenu n’est en cours pour l’instant.</p>
{/if}

{#snippet fiche(t: TexteEnCours)}
  {@const v = t.dernier_vote}
  <article class="texte" id={t.id}>
    <h3><a href={t.href}>{t.titre}</a></h3>
    {#if t.echeance === 'inscrit'}
      <p class="date">{inscription(chambre(t), dates(t))}{eventuel(t.seances)}.</p>
    {/if}
    {#if t.commissions.length}
      <p class="petit">
        En commission le {listeDates(t.commissions.map((c) => c.date))}{eventuel(t.commissions)}.
      </p>
    {/if}
    {#if t.qualification}
      <p>
        <strong class={t.qualification.sens === 'etend' ? 'favorable' : 'defavorable'}
          >Le texte {phrase(t.qualification.code, t.qualification.sens)}</strong
        >{#if t.qualification.date}, sur le texte voté le {date(t.qualification.date)}{/if}.
      </p>
    {/if}
    {#if t.suivi}
      <p class="petit"><strong>Pas encore qualifié</strong> : ni sens ni score avant le vote.</p>
      {#if t.suivi.resume}<p>{t.suivi.resume}</p>{/if}
      <h4>Droits touchés</h4>
      {#each t.suivi.droits as d (d.code)}
        <div class="droit">
          <p>
            <a href="/droits/{d.code}">{court(d.code)}</a>{#if d.justification}.
              {d.justification}{/if}
          </p>
          <Sources sources={d.sources} />
        </div>
      {/each}
      {#if t.suivi.note}<p class="petit discret">{t.suivi.note}</p>{/if}
    {/if}
    {#if v}
      <p>
        Dernier vote public de l’Assemblée, le {date(v.date)}{voteDeLecture(v.etape)
          ? ` (${voteDeLecture(v.etape)})`
          : ''} : {v.sort === 'adopte' ? 'adopté' : 'rejeté'} par {v.decompte.pour} voix pour,
        {v.decompte.contre} contre et {v.decompte.abstention} abstentions.
        <a href={v.url} rel="external">Scrutin n° {v.numero}</a>.
        {#if !t.vote_qualifie}<strong>Ce vote n’est pas encore qualifié.</strong>{/if}
      </p>
      <ul class="positions">
        {#each v.ventilations.filter((x) => x.pour + x.contre + x.abstention > 0) as x (x.groupe.id)}
          <li>
            <span class="sigle" style:--c={x.groupe.couleur} title={x.groupe.nom}
              >{x.groupe.sigle}</span
            >&nbsp;: {POSITION_GROUPE[x.position]}
          </li>
        {/each}
      </ul>
      <details>
        <summary>Détail par groupe</summary>
        <Ventilations ventilations={v.ventilations} favorable={null} />
      </details>
    {:else}
      <p>Aucun vote public de l’Assemblée sur ce texte pour l’instant.</p>
    {/if}
  </article>
{/snippet}

{#each SECTIONS as s (s.echeance)}
  {#if parEcheance(s.echeance).length}
    <section>
      <h2>{s.titre}</h2>
      <p class="petit discret">{pluriel(parEcheance(s.echeance).length, 'texte')}</p>
      {#each parEcheance(s.echeance) as t (t.dossier_an)}{@render fiche(t)}{/each}
    </section>
  {/if}
{/each}

<style>
  .texte {
    border-top: 1px solid var(--filet);
    padding: 0.75rem 0 1rem;
  }
  .texte h3 {
    margin-top: 0;
  }
  .texte h3 a {
    text-decoration: none;
  }
  .texte h3 a:hover {
    text-decoration: underline;
  }
  .date {
    font-weight: 650;
  }
  .texte h4 {
    margin: 0.75rem 0 0.25rem;
    font-size: 1rem;
  }
  .droit {
    border-left: 3px solid var(--filet);
    padding-left: 0.9rem;
    margin: 0.5rem 0 0.75rem;
  }
  .droit p {
    margin-bottom: 0.3rem;
  }
  .positions {
    list-style: none;
    padding: 0;
    margin: 0.25rem 0 0.5rem;
    display: flex;
    flex-wrap: wrap;
    gap: 0.15rem 1rem;
    font-size: 0.93rem;
    max-width: none;
  }
  .positions li {
    margin: 0;
  }
  summary {
    cursor: pointer;
    font-weight: 600;
    font-size: 0.95rem;
  }
</style>
