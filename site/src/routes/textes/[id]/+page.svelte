<script lang="ts">
  import Regle from '$lib/components/Regle.svelte';
  import Sources from '$lib/components/Sources.svelte';
  import Ventilations from '$lib/components/Ventilations.svelte';
  import { court, ETIQUETTES, phrase } from '$lib/droits';
  import {
    date,
    entier,
    etatTexte,
    legislature,
    majuscule,
    mentionNavette,
    minuscule,
    POSITION,
    ROLE,
    sensDuPour
  } from '$lib/format';
  import { CONTESTATION, NOM, URL_SITE } from '$lib/site';
  import type { ScrutinRetenu } from '$lib/types';

  let { data } = $props();
  const t = $derived(data.texte);
  const comptes = $derived(t.scrutins.filter((s) => s.compte));
  const affiches = $derived(t.scrutins.filter((s) => !s.compte));
  const src = (ids: string[]) => ids.map((i) => t.sources[i]).filter(Boolean);
  const enNavette = $derived(t.etat?.etat === 'en_navette');
  const mentionDecisif = $derived(
    mentionNavette(t.etat, t.scrutins.find((s) => s.role === 'decisif')?.etape ?? null)
  );

  /** La note de méthode, échappée, avec un lien vers chaque règle citée (« règle 11 », « règles 9 et 11 »). */
  const noteHtml = (note: string) =>
    note
      .replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]!)
      .replace(/règles? (\d{1,2})((?:(?:,| et) \d{1,2})*)/g, (tout: string) =>
        tout.replace(/\d{1,2}/g, (n) => `<a href="/methodologie#regle-${n}">${n}</a>`)
      );

  const pourquoi = (s: ScrutinRetenu) =>
    s.role === 'censure'
      ? `Motion de censure : affichée, pas comptée. Ce scrutin n’enregistre que les voix pour la censure ; il ne dit rien de ceux qui ne l’ont pas votée.`
      : s.role === 'motion'
        ? 'Motion : affichée, pas comptée. Une motion peut se voter pour des raisons tactiques.'
        : s.role === 'ensemble'
          ? 'Autre lecture : affichée, pas comptée. Seul le dernier vote de l’Assemblée sur l’ensemble compte.'
          : s.pour === 'a-trancher'
            ? 'Sens à trancher : pas compté.'
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
      {#if s.role === 'censure'}
        {date(s.date)}. {s.sort === 'adopte' ? 'Adoptée' : 'Rejetée'} : {s.decompte.pour} voix pour la
        censure{s.decompte.requis ? `, sur ${s.decompte.requis} requises` : ''}.
      {:else}
        {date(s.date)}. {s.sort === 'adopte' ? 'Adopté' : 'Rejeté'} par {s.decompte.pour} voix pour,
        {s.decompte.contre} contre et {s.decompte.abstention} abstentions.
      {/if}
      <a href={s.url} rel="external">Scrutin n° {s.numero} sur le site de l’AN</a>.
    </p>
    {#if s.compte && mentionNavette(t.etat, s.etape)}
      <p class="petit mention">{majuscule(mentionNavette(t.etat, s.etape)!)}.</p>
    {/if}
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
      <Ventilations
        ventilations={s.ventilations}
        favorable={s.compte ? s.favorable : null}
        censure={s.role === 'censure'}
      />
    </details>
  </article>
{/snippet}

<p class="discret"><a href="/textes">Textes</a></p>
<h1 class="titre">{t.titre}</h1>
<p class="discret">
  {legislature(t.legislature)} législature. {t.sans_vote
    ? 'Adopté par le 49.3, sans vote final de l’Assemblée.'
    : `Vote décisif le ${date(t.date)}${mentionDecisif ? ` (${mentionDecisif})` : ''}.`}
  {#if t.loi}{`Loi n° ${t.loi}${t.date_loi ? ` du ${date(t.date_loi)}` : ''}.`}{/if}
  {#if t.url_an}<a href={t.url_an} rel="external">Dossier à l’Assemblée</a>.{/if}
  {#if t.url_loi}<a href={t.url_loi} rel="external">Texte sur Légifrance</a>.{/if}
</p>
{#if t.etat && etatTexte(t.etat) && !t.loi}
  <p class="etat">
    État au {date(data.dateEtat)} : <strong>{minuscule(etatTexte(t.etat))}</strong>.
    {#if t.etat.seance_inscrite}Inscrit en séance le {date(t.etat.seance_inscrite)}.{/if}
    {#if t.etat.date_derniere_lecture && t.etat.date_derniere_lecture > t.date}Dernière lecture
      conclue le {date(t.etat.date_derniere_lecture)}.{/if}
  </p>
{/if}
{#if t.resume}<p class="chapo">{t.resume}</p>{/if}

<section>
  <h2>Ce que fait le texte</h2>
  {#if enNavette && !t.sans_vote}
    <p class="petit">Sur le texte voté le {date(t.date)}.</p>
  {/if}
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
    <p class="petit">Étiquettes : {t.etiquettes.map((e) => ETIQUETTES[e] ?? e).join(', ')}.</p>
  {/if}

  {#if t.vigilance.length}
    <h3>Points de vigilance</h3>
    <p class="petit discret">Critiques sourcées, affichées à côté du jugement sans le modifier.</p>
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
  {#if CONTESTATION}
    <p class="petit">
      <a
        href="mailto:{CONTESTATION}?subject={encodeURIComponent(
          `Contestation : ${t.titre}`
        )}&body={encodeURIComponent(
          `Qualification contestée : ${URL_SITE}/textes/${t.id}\n\nCe que je conteste, et pourquoi (une source publique aide à trancher) :\n\n`
        )}">Contester cette qualification</a
      >. Chaque contestation est lue, et la qualification corrigée si elle est fondée.
    </p>
  {/if}
  {#if t.note}
    <details class="note">
      <summary>Comment ce texte a été qualifié</summary>
      <p class="petit">{@html noteHtml(t.note)}</p>
      <p class="petit discret">
        Les numéros renvoient aux règles de la <a href="/methodologie">méthodologie</a>.
      </p>
    </details>
  {/if}
</section>

{#if t.sans_vote}
  <section>
    <h2>Un texte adopté sans vote</h2>
    <p>
      Le Gouvernement a engagé sa responsabilité sur ce texte (article 49, alinéa 3, de la
      Constitution) : il a été adopté sans vote final de l’Assemblée, faute de motion de censure
      adoptée. Il est qualifié comme les autres, mais il ne compte dans aucun score : le scrutin sur
      une motion de censure n’enregistre que les voix pour la censure, et ne dit donc rien des
      député·es qui ne l’ont pas votée. Les motions de censure s’affichent ci-dessous, groupe par
      groupe.
    </p>
  </section>
{:else}
  <section>
    <h2>Comment votent les groupes sur ce texte</h2>
    <p>
      Part des votes favorables aux droits (au sens du droit principal : le texte {phrase(
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
{/if}

<section>
  {#if comptes.length}
    <h2>Les scrutins comptés</h2>
    <p>
      Le vote décisif {comptes.length > 1
        ? 'pèse la moitié du texte, les amendements clés se partagent l’autre moitié'
        : 'pèse tout le texte'}. Chaque texte pèse autant dans le score.
    </p>
    {#each comptes as s (s.id)}{@render scrutin(s, s.role === 'decisif')}{/each}
  {/if}

  {#if affiches.length}
    <h2 id="autres-scrutins">
      {comptes.length ? 'Les autres scrutins, affichés' : 'Les scrutins, affichés'}
    </h2>
    {#each affiches as s (s.id)}{@render scrutin(s, s.role === 'censure')}{/each}
  {/if}
</section>

<style>
  .titre {
    font-size: clamp(2rem, 5.5vw, 3.4rem);
    max-width: 24ch;
    margin-bottom: 0.75rem;
  }
  .etat {
    max-width: 60ch;
  }
  .mention {
    font-weight: 600;
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
