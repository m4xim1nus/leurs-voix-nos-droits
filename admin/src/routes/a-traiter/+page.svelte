<script lang="ts">
  import { LIBELLES_ALERTE } from '$lib/alertes';
  import { date } from '$lib/format';

  let { data } = $props();
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
          </td>
        </tr>
      {/each}
    </tbody>
  </table>
{:else}
  <p>Rien à traiter.</p>
{/if}
