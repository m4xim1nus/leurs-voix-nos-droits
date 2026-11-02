<script lang="ts">
  import { LIBELLES_ALERTE } from '$lib/alertes';
  import { date } from '$lib/format';

  let { data } = $props();
  const notes = $derived(new Map(data.notes.map((n) => [n.dossier_an, n.texte])));
</script>

<svelte:head><title>À traiter · admin</title></svelte:head>

<h1>À traiter</h1>
<p class="discret">
  {data.alertes.length} alertes, les plus récentes d’abord. Ce sont des avertissements : elles ne bloquent
  ni la mise à jour des données ni la publication. Une alerte disparaît quand la qualification du texte
  en tient compte, même avant publication. « Inscrit » ne veut pas dire voté.
</p>

{#if data.alertes.length}
  <table>
    <thead>
      <tr>
        <th>Date</th>
        <th>Alerte</th>
        <th>Texte</th>
      </tr>
    </thead>
    <tbody>
      {#each data.alertes as a (a.id)}
        <tr>
          <td>{date(a.date)}</td>
          <td>{LIBELLES_ALERTE[a.type]}</td>
          <td>
            <a href="/textes/{a.dossier_id}">{a.titre ?? a.dossier_id}</a>
            <div class="discret">{a.detail}</div>
            {#if notes.has(a.dossier_id)}<div class="note">
                Note interne : {notes.get(a.dossier_id)}
              </div>{/if}
          </td>
        </tr>
      {/each}
    </tbody>
  </table>
{:else}
  <p>Rien à traiter.</p>
{/if}

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
  .note {
    font-size: 0.9rem;
    margin-top: 0.2rem;
  }
  .note-texte {
    white-space: pre-line;
  }
</style>
