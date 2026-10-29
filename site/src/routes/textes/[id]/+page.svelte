<script lang="ts">
  import Regle from '$lib/components/Regle.svelte';
  import Sources from '$lib/components/Sources.svelte';
  import Ventilations from '$lib/components/Ventilations.svelte';
  import { court, ETIQUETTES, phrase } from '$lib/droits';
  import { date, entier, legislature, POSITION, ROLE, sensDuPour } from '$lib/format';
  import { NOM } from '$lib/site';
  import type { ScrutinRetenu } from '$lib/types';

  let { data } = $props();
  const t = $derived(data.texte);
  const comptes = $derived(t.scrutins.filter((s) => s.compte));
  const affiches = $derived(t.scrutins.filter((s) => !s.compte));
  const src = (ids: string[]) => ids.map((i) => t.sources[i]).filter(Boolean);

  const pourquoi = (s: ScrutinRetenu) =>
    s.role === 'motion'
      ? 'Motion : affichée, pas comptée (règle 10).'
      : s.role === 'ensemble'
        ? 'Autre lecture : affichée, pas comptée (règle 9).'
        : s.pour === 'a-trancher'
          ? 'Sens à trancher : pas compté.'
          : 'Affiché, pas compté.';
</script>

<svelte:head>
  <title>{t.titre}, {NOM}</title>
  <meta
    name="description"
    content="Le texte {phrase(
      t.principal.code,
      t.principal.sens
    )}. Sources, scrutins et votes des groupes."
  />
</svelte:head>

{#snippet scrutin(s: ScrutinRetenu, ouvert: boolean)}
  <article class="scrutin">
    <p class="role">
      {ROLE[s.role]}{#if s.compte && t.scrutins.some((x) => x.role === 'amendement' && x.compte)},
        poids {entier(s.poids * 100)} % du texte{/if}
    </p>
    <h3>{s.objet}</h3>
    <p class="petit">
      {date(s.date)}. {s.sort === 'adopte' ? 'Adopté' : 'Rejeté'} par {s.decompte.pour} voix pour,
      {s.decompte.contre} contre et {s.decompte.abstention} abstentions.
      <a href={s.url} rel="external">Scrutin n° {s.numero} sur le site de l’AN</a>.
    </p>
    {#if s.amendement}
      <p class="petit discret">
        {`Amendement n° ${s.amendement.numero}${s.amendement.auteur ? ` de ${s.amendement.auteur}` : ''}${s.amendement.groupe ? ` (${s.amendement.groupe})` : ''}, ${s.amendement.division.toLowerCase()}.`}
      </p>
    {/if}
    <p class="petit">
      {#if s.compte}
        Ici, {sensDuPour(s.pour)} : le vote favorable aux droits est
        <strong class="favorable">{POSITION[s.favorable!].toLowerCase()}</strong>.
      {:else}
        <span class="discret">{pourquoi(s)}</span>
      {/if}
    </p>
    <details open={ouvert}>
      <summary>Position des groupes</summary>
      <Ventilations ventilations={s.ventilations} favorable={s.compte ? s.favorable : null} />
    </details>
  </article>
{/snippet}

<p class="discret"><a href="/textes">Textes</a></p>
<h1 class="titre">{t.titre}</h1>
<p class="discret">
  {legislature(t.legislature)} législature. Vote décisif le {date(t.date)}.
  {#if t.loi}{`Loi n° ${t.loi}${t.date_loi ? ` du ${date(t.date_loi)}` : ''}.`}{/if}
  {#if t.url_an}<a href={t.url_an} rel="external">Dossier à l’Assemblée</a>.{/if}
  {#if t.url_loi}<a href={t.url_loi} rel="external">Texte sur Légifrance</a>.{/if}
</p>
{#if t.resume}<p class="chapo">{t.resume}</p>{/if}

<section>
  <h2>Ce que fait le texte</h2>
  {#each t.droits as d (d.code)}
    <div class="droit">
      <p class="petit discret">
        <a href="/droits/{d.code}">{court(d.code)}</a>, droit {d.role === 'principal'
          ? 'principal'
          : 'secondaire'}
      </p>
      <p>
        <strong class={d.sens === 'etend' ? 'favorable' : 'defavorable'}
          >Le texte {phrase(d.code, d.sens)}.</strong
        >
        {d.justification}
      </p>
      <Sources sources={src(d.sources)} />
    </div>
  {/each}
  {#if t.etiquettes.length}
    <p class="petit">Étiquettes : {t.etiquettes.map((e) => ETIQUETTES[e] ?? e).join(', ')}.</p>
  {/if}

  {#if t.vigilance.length}
    <h3>Points de vigilance</h3>
    <p class="petit discret">
      Critiques sourcées affichées à côté du jugement, sans le modifier (règle 5).
    </p>
    {#each t.vigilance as v, i (i)}
      <div class="droit">
        <p>{v.texte}</p>
        <Sources sources={src(v.sources)} />
      </div>
    {/each}
  {/if}

  {#if t.conseil_constitutionnel || t.cc_decision}
    <h3>Conseil constitutionnel</h3>
    <p>
      {t.conseil_constitutionnel}
      {#if t.cc_decision}
        {#if t.cc_url}<a href={t.cc_url} rel="external">Décision n° {t.cc_decision}</a
          >{:else}Décision n° {t.cc_decision}{/if}.
      {/if}
    </p>
  {/if}
  {#if t.note}<p class="petit discret">{t.note}</p>{/if}
</section>

<section>
  <h2>Comment votent les groupes sur ce texte</h2>
  <p>
    Part des votes favorables aux droits (au sens du droit principal : le texte {phrase(
      t.principal.code,
      t.principal.sens
    )}) sur {comptes.length === 1 ? 'le vote décisif' : `les ${comptes.length} scrutins comptés`}.
  </p>
  <Regle
    lignes={data.groupes.map((g) => ({
      cle: g.groupe.id,
      libelle: g.groupe.sigle,
      couleur: g.groupe.couleur,
      href: `/groupes/${g.groupe.slug}`,
      score: g.score.score
    }))}
  />
</section>

<section>
  <h2>Les scrutins comptés</h2>
  <p>
    Le vote décisif {comptes.length > 1
      ? 'pèse la moitié du texte, les amendements clés se partagent l’autre moitié'
      : 'pèse tout le texte'} (règle 18).
  </p>
  {#each comptes as s (s.id)}{@render scrutin(s, s.role === 'decisif')}{/each}

  {#if affiches.length}
    <h2>Les autres scrutins, affichés</h2>
    {#each affiches as s (s.id)}{@render scrutin(s, false)}{/each}
  {/if}
</section>

<style>
  .titre {
    font-size: clamp(2rem, 5.5vw, 3.4rem);
    max-width: 24ch;
    margin-bottom: 0.75rem;
  }
  .droit {
    border-left: 3px solid var(--filet);
    padding-left: 0.9rem;
    margin: 1rem 0 1.25rem;
  }
  .droit p {
    margin-bottom: 0.3rem;
  }
  .scrutin {
    border-top: 1px solid var(--filet);
    padding: 0.9rem 0 0.5rem;
  }
  .scrutin h3 {
    margin-top: 0.15rem;
    font-size: 1.2rem;
  }
  .role {
    margin: 0;
    font-size: 0.9rem;
    font-weight: 650;
    color: var(--ardoise);
  }
  summary {
    cursor: pointer;
    font-weight: 600;
    font-size: 0.95rem;
  }
</style>
