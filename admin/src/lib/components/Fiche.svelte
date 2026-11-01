<script lang="ts">
  // Fiche texte : qualification, scrutins retenus, aperçu du score, contrôles, historique.
  // Tout se modifie en local, puis s'enregistre d'un bloc (une révision par enregistrement).
  import { untrack } from 'svelte';
  import { enhance } from '$app/forms';
  import EditeurDroits, { type LigneSource, versLignes, versSources } from './EditeurDroits.svelte';
  import Positions from './Positions.svelte';
  import {
    date,
    dateHeure,
    legislature,
    LIBELLES_ETAPE,
    LIBELLES_POUR,
    LIBELLES_ROLE,
    LIBELLES_ROLE_SENAT,
    LIBELLES_STATUT,
    LIBELLES_VERSION_SENAT
  } from '$lib/format';
  import {
    normaliser,
    POUR,
    ROLES_SCRUTIN,
    ROLES_SENAT,
    STATUTS,
    valider,
    validerSuivi,
    VERSIONS_SENAT
  } from '$lib/qualification';
  import { favorable, qualifSenat, scoresGroupes, scrutinsComptes } from '$lib/scores';
  import type {
    BlocSenat,
    Groupe,
    Pour,
    Qualification,
    RoleScrutin,
    ScrutinCatalogue,
    ScrutinRetenu,
    ScrutinSenat,
    Statut
  } from '$lib/types';
  import type { PageData, ActionData } from '../../routes/textes/[id]/$types';

  let { data, form }: { data: PageData; form: ActionData } = $props();

  // État initial : la qualification enregistrée (ou vide). Le composant est recréé à chaque texte
  // (+page.svelte), d'où la lecture unique de `data`.
  const depart = untrack(() => structuredClone(data.qualif));
  let doc: Qualification = $state(depart.doc);
  let sources: LigneSource[] = $state(versLignes(depart.doc.sources));
  let statut: Statut = $state(depart.statut);
  let motif = $state(depart.motif_ecart ?? '');
  let commentaire = $state('');
  let attendu = $state(depart.modifie_le);
  let modifie = $state(false);
  let enCours = $state(false);

  const t = $derived(data.texte);
  const groupes = $derived(new Map<string, Groupe>(data.groupes.map((g) => [g.id, g])));
  const sigleLignee = (l: string) => groupes.get(l)?.sigle ?? l;
  const parId = $derived(new Map(data.scrutins.map((s) => [s.id, s])));
  const infos = $derived(
    new Map(
      data.scrutins.map((s) => [
        s.id,
        {
          dossier_id: s.texte_id,
          etape: s.etape,
          division: s.amendement_division,
          objet: s.objet,
          pour: s.pour,
          contre: s.contre
        }
      ])
    )
  );

  const infosSenat = $derived(
    new Map(
      data.senat.map((s) => [
        s.id,
        { dossier_id: s.texte_id, objet: s.objet, pour: s.pour, contre: s.contre }
      ])
    )
  );

  // Sénat (règles 23 à 28).
  const vide = (): BlocSenat => ({
    version: 'seul',
    scrutins: [],
    droits: [],
    etiquettes: [],
    vigilance: [],
    sources: {},
    note: ''
  });
  let blocSenat: BlocSenat = $state(depart.doc.senat ?? vide());
  let sourcesSenat: LigneSource[] = $state(versLignes(depart.doc.senat?.sources ?? {}));
  // Droits, étiquettes, vigilance et sources propres n'existent que pour une autre version : le
  // formulaire les garde si l'on change de version, mais ils ne s'enregistrent pas.
  const senat = $derived<BlocSenat>(
    blocSenat.version === 'autre'
      ? { ...blocSenat, sources: versSources(sourcesSenat) }
      : { ...blocSenat, droits: [], etiquettes: [], vigilance: [], sources: {} }
  );

  // Fiche de suivi : ni sens, ni rôle, ni scrutin dans ce qui s'enregistre (le formulaire les garde,
  // au cas où le statut change avant l'enregistrement).
  const aSuivre = $derived(statut === 'a-suivre');
  const complet = $derived(
    normaliser({
      ...doc,
      droits: aSuivre
        ? (doc.droits.map(({ code, sources, justification }) => ({
            code,
            sources,
            justification
          })) as Qualification['droits'])
        : doc.droits,
      scrutins: aSuivre ? [] : doc.scrutins,
      senat: aSuivre ? undefined : senat,
      sources: versSources(sources)
    })
  );
  const controle = $derived.by(() => {
    if (statut === 'ecarte')
      return {
        erreurs: motif.trim() ? [] : ['un texte écarté doit avoir un motif'],
        avertissements: []
      };
    const v = aSuivre
      ? validerSuivi(complet, data.grille)
      : valider(complet, data.grille, infos, infosSenat);
    if (data.autresIds.includes(complet.id))
      v.erreurs.push(`identifiant ${complet.id} déjà pris par un autre texte`);
    return v;
  });

  // Toute modification marque la fiche comme non enregistrée.
  let premier = true;
  $effect(() => {
    JSON.stringify(complet);
    void statut;
    void motif;
    if (premier) premier = false;
    else modifie = true;
  });

  // --- Scrutins -------------------------------------------------------------------------------

  const retenus = $derived(new Map(doc.scrutins.map((s) => [s.id, s])));
  const ORDRE = Object.fromEntries(ROLES_SCRUTIN.map((r, i) => [r, i]));

  function objetPropose(s: ScrutinCatalogue): string {
    const etape = LIBELLES_ETAPE[s.etape ?? ''] ?? s.etape ?? '';
    const quoi =
      s.objet === 'amendement' && s.amendement_division
        ? `amendement n° ${s.amendement_numero} sur « ${s.amendement_division} »`
        : (s.titre ?? '').replace(/^l'/, '').slice(0, 90);
    return `${quoi}, ${etape} (${s.pour}-${s.contre})`;
  }

  function retenir(s: ScrutinCatalogue, role: RoleScrutin | '') {
    const i = doc.scrutins.findIndex((x) => x.id === s.id);
    if (!role) {
      if (i >= 0) doc.scrutins.splice(i, 1);
      return;
    }
    if (i >= 0) {
      doc.scrutins[i].role = role;
      return;
    }
    // Sens par défaut : le texte lui-même va « dans le sens du texte », une motion contre lui ;
    // le sens d'un amendement clé est toujours fixé à la main (règle 11).
    const pour: Pour =
      role === 'motion' || role === 'censure'
        ? 'contre-texte'
        : role === 'amendement'
          ? 'a-trancher'
          : 'texte';
    doc.scrutins.push({ id: s.id, role, pour, objet: objetPropose(s) });
    doc.scrutins.sort(
      (a, b) =>
        ORDRE[a.role] - ORDRE[b.role] ||
        (parId.get(b.id)?.numero ?? 0) - (parId.get(a.id)?.numero ?? 0)
    );
  }

  let vue = $state<'principaux' | 'amendements' | 'tous'>('principaux');
  let rechercheScrutin = $state('');
  const principal = (s: ScrutinCatalogue) =>
    retenus.has(s.id) ||
    s.id === t.decisif_propose ||
    !['amendement', 'article', 'suppression_article_unique'].includes(s.objet ?? '');
  const visibles = $derived(
    data.scrutins.filter((s) => {
      if (vue === 'principaux' && !principal(s)) return false;
      if (
        vue === 'amendements' &&
        !['amendement', 'article', 'suppression_article_unique'].includes(s.objet ?? '')
      )
        return false;
      const r = rechercheScrutin.trim().toLowerCase();
      if (r && !`${s.titre} ${s.amendement_division ?? ''} ${s.numero}`.toLowerCase().includes(r))
        return false;
      return true;
    })
  );

  // --- Sénat (règles 23 à 28) -----------------------------------------------------------------

  const retenusSenat = $derived(new Map(blocSenat.scrutins.map((s) => [s.id, s])));
  const parIdSenat = $derived(new Map(data.senat.map((s) => [s.id, s])));
  const groupesSenatPos = $derived(
    new Map<string, Groupe>(
      data.groupesSenat.map((g) => [
        g.id,
        { ...g, lignee: g.id, legislature: 0, couleur: null, date_debut: null, date_fin: null }
      ])
    )
  );
  let tousSenat = $state(false);
  const principalSenat = (s: ScrutinSenat) =>
    retenusSenat.has(s.id) ||
    s.objet === 'ensemble' ||
    s.objet === 'article_unique' ||
    (s.objet ?? '').startsWith('motion') ||
    s.objet === 'question_prealable';
  const visiblesSenat = $derived(data.senat.filter((s) => tousSenat || principalSenat(s)));

  function retenirSenat(s: ScrutinSenat, role: ScrutinRetenu['role'] | '') {
    const i = blocSenat.scrutins.findIndex((x) => x.id === s.id);
    if (!role) {
      if (i >= 0) blocSenat.scrutins.splice(i, 1);
      return;
    }
    if (i >= 0) {
      blocSenat.scrutins[i].role = role;
      return;
    }
    const quoi = (s.objet === 'ensemble' ? 'ensemble' : (s.titre ?? '').slice(0, 80)).trim();
    blocSenat.scrutins.push({
      id: s.id,
      role,
      pour: role === 'motion' ? 'contre-texte' : 'texte',
      objet: `${quoi}, ${(s.lecture ?? '').toLowerCase()} (${s.pour}-${s.contre})`
    });
  }

  const comptesSenat = $derived(
    scrutinsComptes(statut === 'ecarte' || aSuivre ? [] : qualifSenat([complet]))
  );
  const apercuSenat = $derived.by(() => {
    const pos = new Map(data.senat.map((s) => [s.id, s.positions]));
    return scoresGroupes(comptesSenat, pos, (g) => g)
      .filter((s) => s.droit === 'global')
      .sort((a, b) => (b.score ?? -1) - (a.score ?? -1));
  });

  // --- Aperçu du score ------------------------------------------------------------------------

  const comptes = $derived(scrutinsComptes(statut === 'ecarte' || aSuivre ? [] : [complet]));
  const apercu = $derived.by(() => {
    const pos = new Map(data.scrutins.map((s) => [s.id, s.positions]));
    const scores = scoresGroupes(comptes, pos, (g) => groupes.get(g)?.lignee ?? g);
    const droits = ['global', ...complet.droits.map((d) => d.code)];
    const globaux = new Map(
      scores.filter((s) => s.droit === 'global').map((s) => [s.lignee, s.score ?? -1])
    );
    const lignees = [...new Set(scores.map((s) => s.lignee))].sort(
      (a, b) => (globaux.get(b) ?? -1) - (globaux.get(a) ?? -1)
    );
    const cle = new Map(scores.map((s) => [`${s.lignee}|${s.droit}`, s]));
    return { droits, lignees, cle };
  });
  const principalSens = $derived(complet.droits.find((d) => d.role === 'principal')?.sens);

  // --- Historique -----------------------------------------------------------------------------

  function recharger(r: (typeof data.revisions)[number]) {
    const d = JSON.parse(r.doc) as Qualification;
    doc = d;
    sources = versLignes(d.sources);
    blocSenat = d.senat ?? vide();
    sourcesSenat = versLignes(blocSenat.sources);
    statut = r.statut;
    motif = r.motif_ecart ?? '';
    commentaire = `retour à la version du ${dateHeure(r.date)}`;
  }

  const blocCC = $derived([t.cc_decision, t.cc_sens?.toLowerCase()].filter(Boolean).join(', '));
</script>

<svelte:window
  onbeforeunload={(e) => {
    if (modifie) e.preventDefault();
  }}
/>

<p class="discret"><a href="/">← Textes</a></p>
<h1>{t.titre}</h1>
<div class="ligne discret">
  <span>{legislature(t.legislature)} législature</span>
  <span>{t.procedure}</span>
  <span class="mono">{t.id}</span>
  {#if t.url_an}<a href={t.url_an} rel="external noopener" target="_blank">dossier AN</a>{/if}
  {#if t.loi}
    <span>loi {t.loi} du {date(t.date_loi)}</span>
    {#if t.url_loi}<a href={t.url_loi} rel="external noopener" target="_blank">Légifrance</a>{/if}
  {/if}
  {#if t.cc_decision}
    <span>Conseil constitutionnel : {blocCC}</span>
    {#if t.cc_url}<a href={t.cc_url} rel="external noopener" target="_blank">décision</a>{/if}
  {/if}
  {#if t.motifs}<span>mots-clés : « {t.motifs.replaceAll(';', ', ')} »</span>{/if}
</div>

<form
  method="POST"
  action="?/enregistrer"
  use:enhance={() => {
    enCours = true;
    return async ({ result, update }) => {
      enCours = false;
      if (result.type === 'success' && result.data?.modifie_le) {
        attendu = String(result.data.modifie_le);
        modifie = false;
        commentaire = '';
      }
      await update({ reset: false });
    };
  }}
>
  <input type="hidden" name="doc" value={JSON.stringify(complet)} />
  <input type="hidden" name="attendu" value={attendu} />

  {#if statut !== 'ecarte'}
    <section class="carte">
      <h2>{aSuivre ? 'Fiche de suivi' : 'Qualification'}</h2>
      {#if aSuivre}
        <p class="discret">
          Avant le vote : les droits touchés et leurs sources publiques, sans sens ni score, et
          aucun scrutin retenu. Le texte passe à « validé » après son vote.
        </p>
      {/if}
      <div class="ligne">
        <label class="champ"
          >Identifiant public
          <input type="text" bind:value={doc.id} class="mono" size="36" />
        </label>
        <label class="champ grand"
          >Titre affiché
          <input type="text" bind:value={doc.titre} />
        </label>
      </div>
      <label class="champ"
        >Résumé (une ou deux phrases, ton factuel)
        <textarea bind:value={doc.resume} rows="2"></textarea>
      </label>

      <EditeurDroits
        bind:droits={doc.droits}
        bind:etiquettes={doc.etiquettes}
        bind:vigilance={doc.vigilance}
        bind:sources
        grille={data.grille}
        bibliotheque={data.bibliotheque}
        suivi={aSuivre}
      />

      {#if !aSuivre}
        <h3>Conseil constitutionnel et note</h3>
        <label class="champ"
          >Décision résumée {#if t.cc_decision}({t.cc_decision}, {t.cc_sens?.toLowerCase()}){/if}
          <textarea bind:value={doc.conseil_constitutionnel} rows="2"></textarea>
        </label>
      {/if}
      <label class="champ"
        >Note de méthode (publique{aSuivre ? '' : ' : choix des scrutins, amendements écartés…'})
        <textarea bind:value={doc.note} rows="2"></textarea>
      </label>
    </section>
  {/if}

  {#if statut !== 'ecarte' && !aSuivre}
    <section class="carte">
      <h2>Scrutins</h2>
      <p class="discret">
        Comptés : le décisif (dernier vote de l'AN sur l'ensemble, règle 9) et les amendements clés
        au sens fixé (règle 11), un seul par article et par lecture. Motions et autres lectures :
        affichées, pas comptées. En vert, les groupes dont la position est favorable aux droits sur
        ce scrutin.
      </p>
      {#if !doc.scrutins.some((s) => s.role === 'decisif') && t.decisif_propose && parId.has(t.decisif_propose)}
        <p>
          <button type="button" onclick={() => retenir(parId.get(t.decisif_propose!)!, 'decisif')}>
            Retenir le décisif proposé ({t.decisif_propose})
          </button>
        </p>
      {/if}

      {#if doc.scrutins.length}
        <h3>Retenus ({doc.scrutins.length})</h3>
        <table>
          <tbody>
            {#each doc.scrutins as r, i (r.id)}
              {@const s = parId.get(r.id)}
              <tr>
                <td class="mono">{r.id.replace(/^VTANR5L\d+/, '')}</td>
                <td>
                  <select bind:value={r.role} aria-label="Rôle">
                    {#each ROLES_SCRUTIN as role (role)}<option value={role}
                        >{LIBELLES_ROLE[role]}</option
                      >{/each}
                  </select>
                </td>
                <td>
                  <select
                    bind:value={r.pour}
                    aria-label="Sens"
                    class:a-trancher={r.pour === 'a-trancher'}
                  >
                    {#each POUR as p (p)}<option value={p}>{LIBELLES_POUR[p]}</option>{/each}
                  </select>
                </td>
                <td class="large"><input type="text" bind:value={r.objet} /></td>
                <td>{s ? date(s.date) : 'absent du catalogue'}</td>
                <td
                  ><button type="button" class="lien" onclick={() => doc.scrutins.splice(i, 1)}
                    >retirer</button
                  ></td
                >
              </tr>
            {/each}
          </tbody>
        </table>
      {/if}

      <div class="ligne entete-scrutins">
        <h3>Scrutins du dossier ({data.scrutins.length})</h3>
        <select bind:value={vue} aria-label="Scrutins affichés">
          <option value="principaux">ensemble, motions, retenus</option>
          <option value="amendements">amendements et articles</option>
          <option value="tous">tous</option>
        </select>
        <input type="search" bind:value={rechercheScrutin} placeholder="article, mot, numéro…" />
        <span class="discret">{visibles.length} affichés</span>
      </div>
      <table class="scrutins">
        <thead>
          <tr
            ><th>Scrutin</th><th>Objet et positions de groupe</th><th class="nombre">Pour-contre</th
            ><th>Retenu</th></tr
          >
        </thead>
        <tbody>
          {#each visibles as s (s.id)}
            {@const r = retenus.get(s.id) as ScrutinRetenu | undefined}
            {@const fav = r && principalSens ? favorable(principalSens, r.pour) : null}
            <tr class:retenu={r}>
              <td>
                <span class="mono">n° {s.numero}</span>
                <div class="discret">{date(s.date)}</div>
                <div class="discret">{LIBELLES_ETAPE[s.etape ?? ''] ?? s.etape ?? ''}</div>
                {#if s.id === t.decisif_propose}<span class="pastille valide">décisif proposé</span
                  >{/if}
              </td>
              <td>
                <span class="discret">{s.objet}{s.type_vote === 'SPS' ? ', solennel' : ''} :</span>
                {s.titre}
                {#if s.amendement_division}
                  <div class="discret">
                    amendement n° {s.amendement_numero} · {s.amendement_division}
                    {#if s.amendement_auteur}· auteur {groupes.get(s.amendement_auteur)?.sigle ??
                        s.amendement_auteur}{/if}
                    {#if s.amendement_sort}· {s.amendement_sort.toLowerCase()}{/if}
                  </div>
                {/if}
                <Positions positions={s.positions} {groupes} favorable={fav} />
              </td>
              <td class="nombre">
                {s.pour}-{s.contre}
                <div class="discret">{s.abstention} abst.</div>
                <div class="discret">{s.sort}</div>
              </td>
              <td>
                <select
                  value={r?.role ?? ''}
                  onchange={(e) => retenir(s, e.currentTarget.value as RoleScrutin | '')}
                  aria-label="Retenir le scrutin {s.numero}"
                >
                  <option value="">—</option>
                  {#each ROLES_SCRUTIN as role (role)}<option value={role}
                      >{LIBELLES_ROLE[role]}</option
                    >{/each}
                </select>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </section>

    <section class="carte">
      <h2>Vote du Sénat</h2>
      <p class="discret">
        Compté : le décisif seul, dernier vote public sur l'ensemble, lu sur le texte voté (règles
        23, 24 et 26). Sans source admise sur la version votée ou sans voix d'un côté : vote affiché
        (« ensemble »), sans droits ni sens. Motions affichées, question préalable comprise. Le bloc
        n'est enregistré qu'avec au moins un scrutin ou une note.
      </p>
      <label class="champ"
        >Le vote porte sur
        <select bind:value={blocSenat.version}>
          {#each VERSIONS_SENAT as v (v)}<option value={v}>{LIBELLES_VERSION_SENAT[v]}</option
            >{/each}
        </select>
      </label>
      {#if blocSenat.scrutins.length}
        <h3>Retenus ({blocSenat.scrutins.length})</h3>
        <table>
          <tbody>
            {#each blocSenat.scrutins as r, i (r.id)}
              {@const s = parIdSenat.get(r.id)}
              <tr>
                <td class="mono">{r.id}</td>
                <td>
                  <select bind:value={r.role} aria-label="Rôle au Sénat">
                    {#each ROLES_SENAT as role (role)}<option value={role}
                        >{LIBELLES_ROLE_SENAT[role]}</option
                      >{/each}
                  </select>
                </td>
                <td>
                  <select bind:value={r.pour} aria-label="Sens au Sénat">
                    {#each POUR as p (p)}<option value={p}>{LIBELLES_POUR[p]}</option>{/each}
                  </select>
                </td>
                <td class="large"><input type="text" bind:value={r.objet} /></td>
                <td>{s ? date(s.date) : 'absent du catalogue'}</td>
                <td
                  ><button
                    type="button"
                    class="lien"
                    onclick={() => blocSenat.scrutins.splice(i, 1)}>retirer</button
                  ></td
                >
              </tr>
            {/each}
          </tbody>
        </table>
      {/if}
      {#if blocSenat.version === 'autre'}
        <h3>Qualification de cette version</h3>
        <p class="discret">
          Lue sur le texte voté au Sénat, avec ses propres sources (règle 24). Droits et sens
          seulement si un décisif est retenu : sans décisif, le vote est affiché, sans droits ni
          sens.
        </p>
        <EditeurDroits
          bind:droits={blocSenat.droits}
          bind:etiquettes={blocSenat.etiquettes}
          bind:vigilance={blocSenat.vigilance}
          bind:sources={sourcesSenat}
          grille={data.grille}
          bibliotheque={data.bibliotheque}
        />
      {/if}
      <label class="champ"
        >Note (publique : sur quoi porte le vote, pourquoi il est compté ou affiché)
        <textarea bind:value={blocSenat.note} rows="2"></textarea>
      </label>

      <div class="ligne entete-scrutins">
        <h3>Scrutins du Sénat sur ce dossier ({data.senat.length})</h3>
        <label class="ligne petite">
          <input type="checkbox" bind:checked={tousSenat} /> articles et parties aussi
        </label>
      </div>
      {#if visiblesSenat.length}
        <table class="scrutins">
          <thead>
            <tr
              ><th>Scrutin</th><th>Objet et positions de groupe</th><th class="nombre"
                >Pour-contre</th
              ><th>Retenu</th></tr
            >
          </thead>
          <tbody>
            {#each visiblesSenat as s (s.id)}
              {@const r = retenusSenat.get(s.id)}
              <tr class:retenu={r}>
                <td>
                  {#if s.url}<a class="mono" href={s.url} rel="external noopener" target="_blank"
                      >{s.id}</a
                    >{:else}<span class="mono">{s.id}</span>{/if}
                  <div class="discret">{date(s.date)}</div>
                  <div class="discret">{s.lecture ?? ''}</div>
                </td>
                <td>
                  <span class="discret">{s.objet} :</span>
                  {s.titre}
                  {#if s.note}<div class="discret">{s.note}</div>{/if}
                  <Positions positions={s.positions} groupes={groupesSenatPos} favorable={null} />
                </td>
                <td class="nombre">
                  {s.pour}-{s.contre}
                  <div class="discret">{s.abstention} abst.</div>
                  <div class="discret">{s.sort}</div>
                </td>
                <td>
                  <select
                    value={r?.role ?? ''}
                    onchange={(e) =>
                      retenirSenat(s, e.currentTarget.value as ScrutinRetenu['role'] | '')}
                    aria-label="Retenir le scrutin {s.id}"
                  >
                    <option value="">—</option>
                    {#each ROLES_SENAT as role (role)}<option value={role}
                        >{LIBELLES_ROLE_SENAT[role]}</option
                      >{/each}
                  </select>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      {:else}
        <p class="discret">Pas de scrutin public du Sénat sur ce dossier.</p>
      {/if}

      {#if apercuSenat.length}
        <h3>Aperçu du score de ce texte au Sénat</h3>
        <table class="apercu">
          <tbody>
            {#each apercuSenat as a (a.lignee)}
              <tr>
                <td>{groupesSenatPos.get(a.lignee)?.sigle ?? a.lignee}</td>
                <td
                  class="nombre"
                  title={`${a.votes_favorables} favorables, ${a.votes_defavorables} défavorables, ${a.abstentions} abstentions`}
                  >{a.score ?? '–'}</td
                >
              </tr>
            {/each}
          </tbody>
        </table>
      {/if}
    </section>

    <section class="carte">
      <h2>Aperçu du score de ce texte</h2>
      <p class="discret">
        Part pondérée des votes favorables aux droits, par groupe (lignée), sur les scrutins comptés
        de ce texte seul. Abstentions et non-votants hors calcul (règles 16 et 17).
      </p>
      {#if apercu.lignees.length}
        <table class="apercu">
          <thead>
            <tr>
              <th>Groupe</th>
              {#each apercu.droits as d (d)}<th class="nombre">{d}</th>{/each}
            </tr>
          </thead>
          <tbody>
            {#each apercu.lignees as l (l)}
              <tr>
                <td>{sigleLignee(l)}</td>
                {#each apercu.droits as d (d)}
                  {@const sc = apercu.cle.get(`${l}|${d}`)}
                  <td
                    class="nombre"
                    title={sc
                      ? `${sc.votes_favorables} favorables, ${sc.votes_defavorables} défavorables, ${sc.abstentions} abstentions`
                      : ''}
                  >
                    {sc?.score ?? '–'}
                  </td>
                {/each}
              </tr>
            {/each}
          </tbody>
        </table>
      {:else}
        <p class="discret">Aucun scrutin compté pour l'instant.</p>
      {/if}
    </section>
  {/if}

  <section class="carte enregistrer">
    <ul class="messages" aria-live="polite">
      {#each controle.erreurs as e (e)}<li class="erreur">{e}</li>{/each}
      {#each controle.avertissements as a (a)}<li class="avertissement">{a}</li>{/each}
      {#if form?.erreurs}
        {#each form.erreurs as e (e)}<li class="erreur">Refusé : {e}</li>{/each}
      {:else if form?.ok && !modifie}
        <li class="ok">Enregistré.</li>
      {/if}
    </ul>
    <div class="ligne">
      <label class="champ"
        >Statut
        <select name="statut" bind:value={statut}>
          {#each STATUTS as s (s)}<option value={s}>{LIBELLES_STATUT[s]}</option>{/each}
        </select>
      </label>
      {#if statut === 'ecarte'}
        <label class="champ grand"
          >Motif (public : pourquoi ce texte n'est pas qualifié)
          <input type="text" name="motif_ecart" bind:value={motif} />
        </label>
      {/if}
      <label class="champ grand"
        >Commentaire de révision (privé)
        <input type="text" name="commentaire" bind:value={commentaire} />
      </label>
      <button
        class="principal"
        disabled={enCours || ((statut === 'valide' || aSuivre) && controle.erreurs.length > 0)}
        title={(statut === 'valide' || aSuivre) && controle.erreurs.length
          ? 'Corriger les erreurs pour valider'
          : ''}
      >
        {enCours ? 'Enregistrement…' : 'Enregistrer'}
      </button>
      {#if modifie}<span class="discret">modifications non enregistrées</span>{/if}
    </div>
    {#if data.existe}
      <p class="discret">
        Dernier enregistrement : {data.qualif.modifie_par}, {dateHeure(data.qualif.modifie_le)}.
        {#if data.qualif.publie_empreinte}Publié au moins une fois.{:else}Jamais publié.{/if}
        {#if data.qualif.publie_empreinte && (data.qualif.statut === 'brouillon' || data.qualif.statut === 'a-relire')}
          Sa version publiée reste sur le site jusqu'à sa validation ; pour le retirer, l'écarter.
        {/if}
      </p>
      {#if data.publie}
        {#if data.publie.changements.length}
          <details open>
            <summary>
              Changements depuis la version publiée ({dateHeure(data.publie.date)}) :
              {data.publie.changements.length}
            </summary>
            <ul>
              {#each data.publie.changements as c (c)}<li>{c}</li>{/each}
            </ul>
          </details>
        {:else}
          <p class="discret">Identique à la version publiée ({dateHeure(data.publie.date)}).</p>
        {/if}
      {/if}
    {/if}
  </section>
</form>

{#if data.revisions.length}
  <section class="carte">
    <h2>Historique</h2>
    <table>
      <tbody>
        {#each data.revisions as r (r.id)}
          <tr>
            <td>{dateHeure(r.date)}</td>
            <td>{r.auteur}</td>
            <td><span class="pastille {r.statut}">{LIBELLES_STATUT[r.statut]}</span></td>
            <td>{r.commentaire ?? ''}</td>
            <td>
              <button type="button" class="lien" onclick={() => recharger(r)}
                >recharger cette version</button
              >
            </td>
          </tr>
        {/each}
      </tbody>
    </table>
  </section>
{/if}

<style>
  .grand {
    flex: 1 1 22rem;
  }
  .grand input {
    width: 100%;
  }
  select.a-trancher {
    background: var(--alerte-fond);
  }
  td.large {
    width: 45%;
  }
  td.large input {
    width: 100%;
  }
  .entete-scrutins {
    position: sticky;
    top: 0;
    background: var(--surface);
    z-index: 1;
    padding: 0.3rem 0;
  }
  .entete-scrutins h3 {
    margin: 0;
  }
  .scrutins th {
    top: 3rem;
  }
  tr.retenu {
    background: var(--surface-2);
  }
  .enregistrer {
    position: sticky;
    bottom: 0;
    z-index: 2;
    box-shadow: 0 -4px 12px rgb(0 0 0 / 0.08);
  }
</style>
