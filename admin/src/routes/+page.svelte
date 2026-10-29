<script lang="ts">
  import { page } from '$app/state';
  import { replaceState } from '$app/navigation';
  import { date, legislature, LIBELLES_STATUT } from '$lib/format';
  import { STATUTS } from '$lib/qualification';

  let { data } = $props();

  // Filtres, repris de l'adresse (pour les retrouver au retour d'une fiche).
  const q = page.url.searchParams;
  let recherche = $state(q.get('q') ?? '');
  let leg = $state(q.get('leg') ?? '');
  let nature = $state(q.get('nature') ?? 'ordinaire');
  let candidats = $state(q.get('candidats') ?? 'oui');
  let droit = $state(q.get('droit') ?? '');
  let statut = $state(q.get('statut') ?? '');
  let adoptes = $state(q.get('adoptes') === 'oui');

  const natures = $derived([...new Set(data.textes.map((t) => t.nature ?? ''))].sort());
  const libelleDroit = $derived(new Map(data.grille.droits.map((d) => [d.code, d.libelle])));

  const norm = (s: string) => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();

  const filtres = $derived.by(() => {
    const r = norm(recherche.trim());
    return data.textes.filter((t) => {
      const cands = [t.droits_candidats, t.etiquettes_candidates].filter(Boolean).join(';');
      if (r && !norm(`${t.titre} ${t.id} ${t.qualif_id ?? ''} ${t.loi ?? ''}`).includes(r))
        return false;
      if (leg && String(t.legislature) !== leg) return false;
      if (nature && t.nature !== nature) return false;
      if (candidats === 'oui' && !cands && !t.statut) return false;
      if (candidats === 'non' && cands) return false;
      if (droit && !(t.droits_candidats ?? '').split(';').includes(droit)) return false;
      if (statut === 'aucun' ? t.statut : statut && t.statut !== statut) return false;
      if (adoptes && !t.loi) return false;
      return true;
    });
  });

  $effect(() => {
    const p = new URLSearchParams();
    const defauts: Record<string, string> = { nature: 'ordinaire', candidats: 'oui' };
    const valeurs: Record<string, string> = {
      q: recherche,
      leg,
      nature,
      candidats,
      droit,
      statut,
      adoptes: adoptes ? 'oui' : ''
    };
    for (const [k, v] of Object.entries(valeurs)) if (v !== (defauts[k] ?? '')) p.set(k, v);
    const s = p.toString();
    if (s !== page.url.searchParams.toString()) replaceState(s ? `?${s}` : '/', {});
  });

  const comptes = $derived(
    STATUTS.map((s) => [s, data.textes.filter((t) => t.statut === s).length] as const)
  );
</script>

<svelte:head><title>Textes · admin</title></svelte:head>

<h1>Textes</h1>
<p class="discret">
  {data.textes.length} textes ayant au moins un scrutin public à l'AN.
  {#each comptes as [s, n] (s)}
    <span class="pastille {s}">{LIBELLES_STATUT[s]} : {n}</span>
  {/each}
  Les droits candidats viennent des mots-clés : une aide au tri, jamais une qualification.
</p>

<form class="ligne filtres carte" onsubmit={(e) => e.preventDefault()}>
  <label class="champ"
    >Recherche
    <input type="search" bind:value={recherche} placeholder="titre, dossier, loi…" />
  </label>
  <label class="champ"
    >Législature
    <select bind:value={leg}>
      <option value="">toutes</option>
      <option value="17">XVIIe</option>
      <option value="16">XVIe</option>
      <option value="15">XVe (dossier)</option>
    </select>
  </label>
  <label class="champ"
    >Nature
    <select bind:value={nature}>
      <option value="">toutes</option>
      {#each natures as n (n)}<option value={n}>{n}</option>{/each}
    </select>
  </label>
  <label class="champ"
    >Mots-clés
    <select bind:value={candidats}>
      <option value="oui">candidats (ou déjà qualifiés)</option>
      <option value="">tous</option>
      <option value="non">non candidats</option>
    </select>
  </label>
  <label class="champ"
    >Droit candidat
    <select bind:value={droit}>
      <option value="">tous</option>
      {#each data.grille.droits as d (d.code)}<option value={d.code}>{d.code}</option>{/each}
    </select>
  </label>
  <label class="champ"
    >Qualification
    <select bind:value={statut}>
      <option value="">toutes</option>
      <option value="aucun">aucune</option>
      {#each STATUTS as s (s)}<option value={s}>{LIBELLES_STATUT[s]}</option>{/each}
    </select>
  </label>
  <label class="ligne"><input type="checkbox" bind:checked={adoptes} /> promulgués seulement</label>
  <span class="discret">{filtres.length} textes</span>
</form>

<table>
  <thead>
    <tr>
      <th>Texte</th>
      <th>Lég.</th>
      <th>Loi</th>
      <th class="nombre">Scrutins</th>
      <th>Droits candidats</th>
      <th>Qualification</th>
    </tr>
  </thead>
  <tbody>
    {#each filtres as t (t.id)}
      <tr>
        <td>
          <a href="/textes/{t.id}">{t.titre}</a>
          <div class="discret">
            {t.nature} · {t.initiative} · dernier scrutin le {date(t.dernier_scrutin)}
            {#if t.motifs}· <span title="motifs trouvés">« {t.motifs.replaceAll(';', ', ')} »</span
              >{/if}
          </div>
        </td>
        <td>{legislature(t.legislature)}</td>
        <td>
          {#if t.loi}{t.loi}
            <div class="discret">{date(t.date_loi)}</div>{/if}
        </td>
        <td class="nombre">
          {t.n_scrutins}
          {#if t.n_amendements}<div class="discret">{t.n_amendements} amdt</div>{/if}
        </td>
        <td>
          {#each (t.droits_candidats ?? '').split(';').filter(Boolean) as c (c)}
            <span class="pastille" title={libelleDroit.get(c)}>{c}</span>
          {/each}
          {#each (t.etiquettes_candidates ?? '').split(';').filter(Boolean) as c (c)}
            <span class="pastille discret">{c}</span>
          {/each}
        </td>
        <td>
          {#if t.statut}
            <span class="pastille {t.statut}">{LIBELLES_STATUT[t.statut]}</span>
            <div class="discret mono">{t.qualif_id}</div>
          {/if}
        </td>
      </tr>
    {/each}
  </tbody>
</table>

<style>
  .filtres {
    position: sticky;
    top: 0;
    z-index: 1;
  }
  td .pastille {
    margin: 0 0.15rem 0.15rem 0;
  }
</style>
