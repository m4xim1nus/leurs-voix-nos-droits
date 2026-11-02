<script lang="ts">
  import { enhance } from '$app/forms';
  import { dateHeure } from '$lib/format';
  import { LIBELLES_ETAT } from '$lib/llm';

  let { data, form } = $props();

  const r = $derived(data.reglages);
  const c = $derived(data.conso);
  const part = $derived(r.plafond_usd > 0 ? Math.min(1, c.mois_usd / r.plafond_usd) : 1);
  const usd = (x: number) =>
    `${x.toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} $`;
  const jetons = (x: number) => x.toLocaleString('fr-FR').replace(/ /g, ' ');
  const mois = (m: string) => `${m.slice(5, 7)}/${m.slice(0, 4)}`;
</script>

<svelte:head><title>LLM · admin</title></svelte:head>

<h1>LLM</h1>
<p class="discret">
  Après chaque passe de données, une Action GitHub peut demander à un LLM une proposition pour
  chaque nouvelle alerte. Le LLM propose, il ne valide ni ne publie jamais. Cette page règle cet
  usage : interrupteur, clé, plafond, et ce qui a été dépensé. Coupé, l’admin fonctionne exactement
  comme sans LLM.
</p>

{#if form?.erreur}
  <ul class="messages"><li class="erreur">{form.erreur}</li></ul>
{:else if form?.ok}
  <ul class="messages"><li class="ok">{form.ok}</li></ul>
{/if}

<section class="carte">
  <h2>État</h2>
  <p>
    <span class="pastille {data.etat === 'en-service' ? 'valide' : 'brouillon'}"
      >{data.etat === 'en-service' ? 'en service' : 'aucun appel'}</span
    >
    {LIBELLES_ETAT[data.etat]}
  </p>
  <form method="POST" action="?/basculer" use:enhance>
    <input type="hidden" name="actif" value={r.actif ? 'non' : 'oui'} />
    <button class:principal={!r.actif}>{r.actif ? 'Couper' : 'Allumer'}</button>
    {#if r.bascule}<span class="discret"
        >{r.actif ? 'allumé' : 'coupé'} le {dateHeure(r.bascule.modifie_le)} par {r.bascule
          .modifie_par}</span
      >{/if}
  </form>
</section>

<section class="carte">
  <h2>Dépense du mois ({mois(c.mois)})</h2>
  <p>
    <strong>{usd(c.mois_usd)}</strong> sur un plafond de {usd(r.plafond_usd)}, en {c.mois_appels}
    appel{c.mois_appels > 1 ? 's' : ''}.
  </p>
  <div
    class="jauge"
    role="meter"
    aria-label="Part du plafond dépensée"
    aria-valuemin="0"
    aria-valuemax={r.plafond_usd}
    aria-valuenow={c.mois_usd}
  >
    <div class:plein={part >= 1} style:width="{Math.round(part * 100)}%"></div>
  </div>
  <p class="discret">
    Coût estimé par le pipeline d’après les jetons et les recherches web de chaque appel ; la
    facture d’Anthropic fait foi. Le plafond est vérifié avant chaque appel : atteint, l’Action
    s’arrête sans faire échouer la passe de données. Le vrai butoir est la limite de dépense du
    workspace, dans la console Anthropic : la régler au même montant.
  </p>
  <form method="POST" action="?/plafond" use:enhance class="ligne-form">
    <label for="plafond">Plafond mensuel, en dollars</label>
    <input
      id="plafond"
      name="plafond"
      type="text"
      inputmode="decimal"
      value={String(r.plafond_usd).replace('.', ',')}
      size="6"
    />
    <button>Enregistrer</button>
  </form>
  {#if c.par_tache.length}
    <table>
      <thead
        ><tr><th>Tâche</th><th class="nombre">Appels</th><th class="nombre">Coût</th></tr></thead
      >
      <tbody>
        {#each c.par_tache as t (t.tache)}
          <tr
            ><td>{t.tache}</td><td class="nombre">{t.appels}</td><td class="nombre"
              >{usd(t.cout_usd)}</td
            ></tr
          >
        {/each}
      </tbody>
    </table>
  {/if}
</section>

<section class="carte">
  <h2>Clé d’API</h2>
  {#if r.cle}
    <p>
      Clé enregistrée, finissant par <span class="mono">…{r.cle.fin}</span>, saisie le
      {dateHeure(r.cle.modifie_le)} par {r.cle.modifie_par}. Elle n’est jamais réaffichée.
    </p>
    <form method="POST" action="?/retirer" use:enhance>
      <button>Retirer la clé</button>
    </form>
  {:else}
    <p>Aucune clé enregistrée.</p>
  {/if}
  {#if data.secret}
    <form method="POST" action="?/cle" use:enhance class="ligne-form">
      <label for="cle">{r.cle ? 'Remplacer par une nouvelle clé' : 'Saisir une clé'}</label>
      <input
        id="cle"
        name="cle"
        type="password"
        autocomplete="off"
        spellcheck="false"
        placeholder="sk-ant-…"
        size="40"
      />
      <button>Tester et enregistrer</button>
    </form>
    <p class="discret">
      La clé est d’abord testée (liste des modèles, sans coût), puis chiffrée dans la base de
      l’admin ; seule l’Action sait la déchiffrer. Une clé d’un workspace dédié au projet, avec sa
      limite de dépense, est préférable.
    </p>
  {:else}
    <p class="discret">
      Saisie impossible : le secret <span class="mono">LLM_CHIFFREMENT</span> manque au Worker (<span
        class="mono">npx wrangler secret put LLM_CHIFFREMENT</span
      >, même valeur dans les secrets du dépôt GitHub).
    </p>
  {/if}
</section>

<section class="carte">
  <h2>Modèle</h2>
  <form method="POST" action="?/modele" use:enhance class="ligne-form">
    <label for="modele" class="visuellement-cache">Modèle</label>
    <select id="modele" name="modele" value={r.modele}>
      {#each data.modeles as m (m.id)}
        <option value={m.id}>{m.libelle}</option>
      {/each}
    </select>
    <button>Enregistrer</button>
  </form>
</section>

<section class="carte">
  <h2>Derniers appels</h2>
  {#if c.derniers.length}
    <table>
      <thead>
        <tr>
          <th>Date</th>
          <th>Tâche</th>
          <th>Texte</th>
          <th>Résultat</th>
          <th class="nombre">Jetons (entrée / sortie)</th>
          <th class="nombre">Recherches</th>
          <th class="nombre">Coût</th>
        </tr>
      </thead>
      <tbody>
        {#each c.derniers as a (a.id)}
          <tr>
            <td>{dateHeure(a.date)}</td>
            <td
              >{a.tache}
              <div class="discret">{a.modele}</div></td
            >
            <td
              >{#if a.dossier_an}<a href="/textes/{a.dossier_an}">{a.dossier_an}</a>{/if}</td
            >
            <td
              >{a.resultat}{#if a.detail}<div class="discret">{a.detail}</div>{/if}</td
            >
            <td class="nombre"
              >{jetons(a.jetons_entree + a.jetons_cache_lus + a.jetons_cache_ecrits)} / {jetons(
                a.jetons_sortie
              )}</td
            >
            <td class="nombre">{a.recherches_web}</td>
            <td class="nombre">{usd(a.cout_usd)}</td>
          </tr>
        {/each}
      </tbody>
    </table>
  {:else}
    <p>Aucun appel pour l’instant.</p>
  {/if}
  {#if c.par_mois.length > 1}
    <h3>Mois précédents</h3>
    <table>
      <tbody>
        {#each c.par_mois as m (m.mois)}
          <tr
            ><td>{mois(m.mois)}</td><td class="nombre">{m.appels} appels</td><td class="nombre"
              >{usd(m.cout_usd)}</td
            ></tr
          >
        {/each}
      </tbody>
    </table>
  {/if}
</section>

<style>
  .jauge {
    height: 0.6rem;
    border-radius: var(--rayon);
    background: var(--surface-2);
    overflow: hidden;
    max-width: 30rem;
  }
  .jauge div {
    height: 100%;
    background: var(--accent);
  }
  .jauge div.plein {
    background: var(--erreur);
  }
  .ligne-form {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.5rem;
    margin: 0.6rem 0;
  }
</style>
