<script lang="ts">
  import { enhance } from '$app/forms';
  import { dateHeure, LIBELLES_STATUT } from '$lib/format';

  let { data, form } = $props();
  let enCours = $state(false);

  const LIBELLES = { nouveau: 'nouveau', modifie: 'modifié', retire: 'retiré' } as const;
  const changes = $derived(data.textes.filter((t) => t.changement));
  const enErreur = $derived(
    data.textes.filter((t) => (t.statut === 'valide' || t.statut === 'ecarte') && t.erreurs.length)
  );
  const autres = $derived(
    data.textes.filter(
      (t) => !t.changement && (t.statut === 'brouillon' || t.statut === 'a-relire')
    )
  );
</script>

<svelte:head><title>Publier · admin</title></svelte:head>

<h1>Publier</h1>
<p class="discret">
  « Publier » écrit les textes validés et écartés dans <span class="mono">{data.chemin}</span> du
  dépôt
  <span class="mono">{data.depot}</span> (branche {data.branche}), en un commit : le site public se
  reconstruit ensuite. Les brouillons et les textes à relire ne sont pas publiés.
</p>

{#if form?.erreur}
  <ul class="messages"><li class="erreur">Publication refusée : {form.erreur}</li></ul>
{:else if form?.ok}
  <ul class="messages">
    <li class="ok">
      {#if form.commit}
        Publié : <a href={form.commit.url} rel="external noopener" target="_blank"
          >commit {form.commit.sha.slice(0, 7)}</a
        >.
      {:else}
        Rien de nouveau : le fichier du dépôt était déjà à jour.
      {/if}
    </li>
  </ul>
{/if}

<section class="carte">
  <h2>Changements depuis la dernière publication ({changes.length})</h2>
  {#if changes.length}
    <table>
      <tbody>
        {#each changes as t (t.dossier_an)}
          <tr>
            <td><span class="pastille">{LIBELLES[t.changement!]}</span></td>
            <td
              ><a href="/textes/{t.dossier_an}">{t.id || t.dossier_an}</a>
              <span class="discret">{t.titre}</span></td
            >
            <td><span class="pastille {t.statut}">{LIBELLES_STATUT[t.statut]}</span></td>
            <td class="discret">{t.modifie_par}, {dateHeure(t.modifie_le)}</td>
          </tr>
          {#if t.erreurs.length || t.avertissements.length}
            <tr>
              <td></td>
              <td colspan="3">
                <ul class="messages">
                  {#each t.erreurs as e (e)}<li class="erreur">{e}</li>{/each}
                  {#each t.avertissements as a (a)}<li class="avertissement">{a}</li>{/each}
                </ul>
              </td>
            </tr>
          {/if}
        {/each}
      </tbody>
    </table>
    <h3>Message du commit</h3>
    <pre class="mono">{data.message}</pre>
  {:else}
    <p>Rien à publier.</p>
  {/if}

  {#if enErreur.length}
    <ul class="messages">
      <li class="erreur">
        {enErreur.length} texte(s) à publier ont des erreurs bloquantes : les corriger, ou les repasser
        en brouillon.
      </li>
    </ul>
  {/if}

  <form
    method="POST"
    action="?/publier"
    use:enhance={() => {
      enCours = true;
      return async ({ update }) => {
        await update();
        enCours = false;
      };
    }}
  >
    <button class="principal" disabled={enCours || data.bloquant || !data.configure}>
      {enCours ? 'Publication…' : 'Publier'}
    </button>
    {#if !data.configure}
      <span class="discret"
        >Secret GITHUB_TOKEN absent : publication impossible (admin/README.md).</span
      >
    {/if}
    <span class="discret">editorial.json : {(data.taille / 1024).toFixed(0)} Ko</span>
  </form>
</section>

{#if autres.length}
  <section class="carte">
    <h2>En cours, non publiés ({autres.length})</h2>
    <p>
      {#each autres as t (t.dossier_an)}
        <a href="/textes/{t.dossier_an}" class="pastille {t.statut}">{t.id || t.dossier_an}</a>{' '}
      {/each}
    </p>
  </section>
{/if}

<section class="carte">
  <h2>Publications</h2>
  {#if data.publications.length}
    <table>
      <tbody>
        {#each data.publications as p (p.id)}
          <tr>
            <td>{dateHeure(p.date)}</td>
            <td>{p.auteur}</td>
            <td>{p.n_textes} textes, {p.n_ecartes} écartés</td>
            <td>
              {#if p.commit_url}<a href={p.commit_url} rel="external noopener" target="_blank"
                  >{p.commit_sha?.slice(0, 7)}</a
                >
              {:else}<span class="discret">sans commit</span>{/if}
            </td>
            <td class="discret">{p.resume.split('\n')[0]}</td>
          </tr>
        {/each}
      </tbody>
    </table>
  {:else}
    <p class="discret">Aucune publication depuis l'admin.</p>
  {/if}
</section>

<style>
  pre {
    background: var(--surface-2);
    padding: 0.6rem;
    border-radius: var(--rayon);
    white-space: pre-wrap;
  }
</style>
