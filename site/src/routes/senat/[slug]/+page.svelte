<script lang="ts">
  import Regle from '$lib/components/Regle.svelte';
  import { court, phrase } from '$lib/droits';
  import { date, pluriel, POSITION, POSITION_GROUPE, pourcent } from '$lib/format';
  import { NOM, URL_SITE } from '$lib/site';
  import type { VoteSenateur } from '$lib/server/vues-senat';

  let { data } = $props();
  const s = $derived(data.senateur);
  const elle = $derived(s.civ === 'Mme');
  const nom = $derived(`${s.prenom} ${s.nom}`);
  const fonction = $derived(
    s.actuel ? (elle ? 'Sénatrice' : 'Sénateur') : elle ? 'Ancienne sénatrice' : 'Ancien sénateur'
  );
  const nComptes = $derived(data.global ? data.global.favorables + data.global.defavorables : 0);
  const mailto = $derived(
    s.courriel
      ? `mailto:${s.courriel}?subject=${encodeURIComponent('Vos votes sur les droits et libertés')}&body=${encodeURIComponent(
          `Bonjour ${elle ? 'Madame la Sénatrice' : 'Monsieur le Sénateur'},\n\nJ’ai consulté les votes enregistrés à votre nom sur les textes qui touchent aux droits et libertés :\n${URL_SITE}/senat/${s.slug}\n\n`
        )}`
      : null
  );
  const classe = (v: VoteSenateur) =>
    v.scrutin.favorable && (v.position === 'pour' || v.position === 'contre')
      ? v.position === v.scrutin.favorable
        ? 'favorable'
        : 'defavorable'
      : '';
  const periode = (g: { debut: string | null; fin: string | null }) =>
    g.fin
      ? `du ${date(g.debut)} au ${date(g.fin)}`
      : g.debut
        ? `depuis le ${date(g.debut)}`
        : 'en cours';
</script>

<svelte:head>
  <title>{nom}, {NOM}</title>
  <meta
    name="description"
    content="Votes enregistrés au nom de {nom} au Sénat sur les textes qui touchent aux droits et libertés."
  />
  {#if data.global?.score != null}
    <meta property="og:image" content="{URL_SITE}/cartes/senateurs/{s.slug}.png" />
  {/if}
</svelte:head>

{#snippet vote(v: VoteSenateur)}
  <div class="vote" class:ecart={v.ecart}>
    <p class="titre-texte"><a href="/textes/{v.texte.id}">{v.texte.titre}</a></p>
    <p class="petit">
      <span class={v.texte.principal.sens === 'etend' ? 'favorable' : 'defavorable'}
        >{v.texte.principal.sens === 'etend' ? '▲' : '▼'} {court(v.texte.principal.code)}</span
      >
      <span class="visuellement-cache"
        >Le texte voté {phrase(v.texte.principal.code, v.texte.principal.sens)}.</span
      >
    </p>
    <p class="petit">
      {date(v.scrutin.date)}, {v.scrutin.objet}. Vote enregistré :
      <strong class={classe(v)}>{POSITION[v.position].toLowerCase()}</strong
      >{#if v.groupe && v.position_groupe}, groupe {v.groupe.sigle} :
        {POSITION_GROUPE[v.position_groupe]}{/if}.
      {#if v.delegue_a}Par délégation à <a href="/senat/{v.delegue_a.slug}">{v.delegue_a.nom}</a
        >.{/if}
      {#if v.statut}{v.statut}.{/if}
      <a href={v.scrutin.url} rel="external">Scrutin du Sénat</a>.
    </p>
  </div>
{/snippet}

<p class="discret"><a href="/senat">Sénat</a></p>
<h1>{nom}</h1>
<p>
  {fonction}, {s.circonscription}.
  {#if data.groupeActuel}Groupe {data.groupeActuel.sigle}{data.groupeActuel.nom !==
    data.groupeActuel.sigle
      ? ` (${data.groupeActuel.nom})`
      : ''}.{/if}
</p>

<section>
  <h2>Score d’après les votes enregistrés à son nom</h2>
  {#if data.global?.score != null}
    <p class="score">
      <strong>{pourcent(data.global.score)}</strong> de votes favorables aux droits
    </p>
    <p>
      Sur {pluriel(nComptes, 'vote compté', 'votes comptés')}{data.global.abstentions
        ? `, et ${pluriel(data.global.abstentions, 'abstention')} hors calcul`
        : ''}.
    </p>
    {#if data.periodes.length}
      <ul class="periodes">
        {#each data.periodes as p (p.id)}
          <li>
            {p.libelle} :
            <strong>{pourcent(p.score.score)}</strong
            >{#if p.groupe && p.scoreGroupe?.score != null}, son groupe {p.groupe.sigle} sur cette période
              : {pourcent(p.scoreGroupe.score)}{/if}.
          </li>
        {/each}
      </ul>
    {/if}
    <p class="petit discret">
      Un vote enregistré ne dit pas qui était présent, et il peut ne pas refléter un choix
      individuel : voir le <a href="/methodologie#regle-27">vote de groupe</a>. Ce score ne se
      compare pas à celui d’un·e député·e : les textes comptés diffèrent.
    </p>
    {#if data.droits.length}
      <Regle
        lignes={data.droits.map((d) => ({
          cle: d.droit.code,
          libelle: d.droit.court,
          score: d.score.score,
          n_textes: d.score.n_textes
        }))}
      />
    {/if}
  {:else}
    <p>Aucun vote compté à son nom sur les textes qualifiés à ce jour.</p>
  {/if}
</section>

<p class="actions">
  {#if mailto}<a class="bouton" href={mailto}>Lui écrire</a>{/if}
  {#if s.courriel}<span class="discret petit">{s.courriel}</span>{/if}
  {#if data.global?.score != null}
    <a class="bouton secondaire" href="/cartes/senateurs/{s.slug}.png" download="{s.slug}.png"
      >Télécharger l’image</a
    >
    <a class="petit" href="/cartes/portrait/senateurs/{s.slug}.png" download="{s.slug}-portrait.png"
      >format portrait, pour les réseaux</a
    >
    {#if data.groupeActuel && data.periodes[0]?.scoreGroupe}
      <a
        class="petit"
        href="/senat/comparer?a=s:{s.slug}&b=g:{data.groupeActuel.id}:{data.periodes[0].id}"
        >Comparer avec son groupe</a
      >
    {/if}
  {/if}
</p>

<section>
  <h2>Ses écarts au groupe</h2>
  {#if data.ecarts.length}
    <p>
      {pluriel(data.ecarts.length, 'vote compté', 'votes comptés')} à l’opposé de la majorité de son groupe
      ce jour-là.
    </p>
    {#each data.ecarts as v (v.scrutin.id)}{@render vote(v)}{/each}
  {:else if data.votes.length}
    <p>Aucun vote compté à l’opposé de la majorité de son groupe.</p>
  {:else}
    <p>Aucun vote compté pour l’instant.</p>
  {/if}
</section>

{#if data.votes.length}
  <section>
    <h2>Tous ses votes comptés</h2>
    {#each data.votes as v (v.scrutin.id)}{@render vote(v)}{/each}
  </section>
{/if}

<section>
  <h2>Ses groupes</h2>
  <ul>
    {#each s.groupes as g, i (i)}
      <li>
        {g.groupe.sigle}{g.groupe.nom !== g.groupe.sigle ? ` (${g.groupe.nom})` : ''}, {periode(g)}
      </li>
    {:else}
      <li>Aucun groupe enregistré depuis juin 2017.</li>
    {/each}
  </ul>
</section>

<style>
  .periodes {
    margin: 0.5rem 0;
  }
  .score {
    font-size: 1.3rem;
    margin-bottom: 0.25rem;
  }
  .titre-texte {
    font-weight: 650;
    margin-bottom: 0.15rem;
  }
  .vote {
    border-top: 1px solid var(--filet);
    padding-top: 0.5rem;
    margin-bottom: 0.5rem;
  }
  .vote.ecart {
    border-left: 4px solid var(--encre);
    padding-left: 0.75rem;
  }
  .actions {
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem;
    align-items: center;
  }
</style>
