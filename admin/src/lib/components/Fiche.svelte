<script lang="ts">
  // Fiche texte : qualification, scrutins retenus, aperçu du score, contrôles, historique.
  // Tout se modifie en local, puis s'enregistre d'un bloc (une révision par enregistrement).
  import { untrack } from 'svelte';
  import { enhance } from '$app/forms';
  import Positions from './Positions.svelte';
  import {
    date,
    dateHeure,
    legislature,
    LIBELLES_ETAPE,
    LIBELLES_POUR,
    LIBELLES_ROLE,
    LIBELLES_STATUT
  } from '$lib/format';
  import { normaliser, POUR, ROLES_SCRUTIN, STATUTS, valider } from '$lib/qualification';
  import { favorable, scoresGroupes, scrutinsComptes } from '$lib/scores';
  import type {
    Groupe,
    Pour,
    Qualification,
    RoleScrutin,
    ScrutinCatalogue,
    ScrutinRetenu,
    Source,
    Statut
  } from '$lib/types';
  import type { PageData, ActionData } from '../../routes/textes/[id]/$types';

  let { data, form }: { data: PageData; form: ActionData } = $props();

  type LigneSource = Source & { cle: string; avant: string };
  const versLignes = (s: Record<string, Source>): LigneSource[] =>
    Object.entries(s ?? {}).map(([cle, v]) => ({ cle, avant: cle, ...v }));

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

  const complet = $derived(
    normaliser({
      ...doc,
      sources: Object.fromEntries(
        sources
          .filter((s) => s.cle.trim())
          .map(({ cle, auteur, titre, date, url }) => [cle.trim(), { auteur, titre, date, url }])
      )
    })
  );
  const controle = $derived.by(() => {
    if (statut === 'ecarte')
      return {
        erreurs: motif.trim() ? [] : ['un texte écarté doit avoir un motif'],
        avertissements: []
      };
    const v = valider(complet, data.grille, infos);
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

  // --- Droits, étiquettes, sources, vigilance -------------------------------------------------

  function ajouterDroit() {
    doc.droits.push({
      code: '',
      role: doc.droits.some((d) => d.role === 'principal') ? 'secondaire' : 'principal',
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
      for (const liste of [
        ...doc.droits.map((d) => d.sources),
        ...doc.vigilance.map((v) => v.sources)
      ]) {
        const i = liste.indexOf(l.avant);
        if (i >= 0) liste[i] = nouveau;
      }
    l.cle = nouveau;
    l.avant = nouveau;
  }

  function retirerSource(i: number) {
    const cle = sources[i].cle;
    for (const liste of [
      ...doc.droits.map((d) => d.sources),
      ...doc.vigilance.map((v) => v.sources)
    ]) {
      const j = liste.indexOf(cle);
      if (j >= 0) liste.splice(j, 1);
    }
    sources.splice(i, 1);
  }

  let choixBibliotheque = $state('');

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

  // --- Aperçu du score ------------------------------------------------------------------------

  const comptes = $derived(scrutinsComptes(statut === 'ecarte' ? [] : [complet]));
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
      <h2>Qualification</h2>
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

      <h3>Droits touchés</h3>
      <p class="discret">
        Un droit principal ; le sens se lit du point de vue des droits des personnes (règle 1). Une
        justification courte et au moins une source par droit.
      </p>
      {#each doc.droits as d, i (i)}
        <div class="droit">
          <div class="ligne">
            <select bind:value={d.code} aria-label="Droit">
              <option value="" disabled>droit…</option>
              {#each data.grille.droits as g (g.code)}
                <option value={g.code} title={g.libelle}>{g.code}</option>
              {/each}
            </select>
            <select bind:value={d.role} aria-label="Rôle">
              <option value="principal">principal</option>
              <option value="secondaire">secondaire</option>
            </select>
            <select bind:value={d.sens} aria-label="Sens" class={d.sens}>
              <option value="restreint">restreint</option>
              <option value="etend">étend</option>
            </select>
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
            <button type="button" class="lien" onclick={() => doc.droits.splice(i, 1)}
              >retirer</button
            >
          </div>
          <textarea
            bind:value={d.justification}
            rows="2"
            placeholder="Justification, avec la source"></textarea>
        </div>
      {/each}
      <button type="button" onclick={ajouterDroit}>+ droit</button>

      <h3>Étiquettes</h3>
      <div class="ligne">
        {#each data.grille.etiquettes as e (e.code)}
          <label class="ligne petite" title={e.libelle}>
            <input
              type="checkbox"
              checked={doc.etiquettes.includes(e.code)}
              onchange={() => basculer(doc.etiquettes, e.code)}
            />
            {e.code}
          </label>
        {/each}
      </div>

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
              <td
                ><button type="button" class="lien" onclick={() => retirerSource(i)}>retirer</button
                ></td
              >
            </tr>
          {/each}
        </tbody>
      </table>
      <div class="ligne">
        <button type="button" onclick={() => ajouterSource()}>+ source</button>
        {#if data.bibliotheque.length}
          <select bind:value={choixBibliotheque} aria-label="Reprendre une source d'un autre texte">
            <option value="">reprendre une source d'un autre texte…</option>
            {#each data.bibliotheque as b, i (i)}
              <option value={String(i)}
                >{b.cle} ({b.texte}) : {b.source.auteur}, {b.source.titre.slice(0, 60)}</option
              >
            {/each}
          </select>
          <button
            type="button"
            disabled={!choixBibliotheque}
            onclick={() => {
              ajouterSource(data.bibliotheque[Number(choixBibliotheque)]);
              choixBibliotheque = '';
            }}>reprendre</button
          >
        {/if}
      </div>

      <h3>Points de vigilance</h3>
      <p class="discret">
        Critiques sourcées affichées à côté du jugement, sans le modifier (règle 5).
      </p>
      {#each doc.vigilance as v, i (i)}
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
            <button type="button" class="lien" onclick={() => doc.vigilance.splice(i, 1)}
              >retirer</button
            >
          </div>
        </div>
      {/each}
      <button type="button" onclick={() => doc.vigilance.push({ texte: '', sources: [] })}>
        + point de vigilance
      </button>

      <h3>Conseil constitutionnel et note</h3>
      <label class="champ"
        >Décision résumée {#if t.cc_decision}({t.cc_decision}, {t.cc_sens?.toLowerCase()}){/if}
        <textarea bind:value={doc.conseil_constitutionnel} rows="2"></textarea>
      </label>
      <label class="champ"
        >Note de méthode (publique : choix des scrutins, amendements écartés…)
        <textarea bind:value={doc.note} rows="2"></textarea>
      </label>
    </section>

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
        disabled={enCours || (statut === 'valide' && controle.erreurs.length > 0)}
        title={statut === 'valide' && controle.erreurs.length
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
  select.a-trancher {
    background: var(--alerte-fond);
  }
  .sources input {
    width: 100%;
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
