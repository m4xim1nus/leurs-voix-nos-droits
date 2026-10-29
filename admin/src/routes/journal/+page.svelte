<script lang="ts">
  import { dateHeure, LIBELLES_STATUT } from '$lib/format';

  let { data } = $props();
</script>

<svelte:head><title>Journal · admin</title></svelte:head>

<h1>Journal</h1>
<p class="discret">Les {data.revisions.length} derniers enregistrements, tous textes confondus.</p>

<table>
  <thead>
    <tr><th>Date</th><th>Auteur</th><th>Texte</th><th>Statut</th><th>Commentaire</th></tr>
  </thead>
  <tbody>
    {#each data.revisions as r (r.id)}
      <tr>
        <td>{dateHeure(r.date)}</td>
        <td>{r.auteur}</td>
        <td>
          <a href="/textes/{r.dossier_an}">{r.qualif_id || r.dossier_an}</a>
          <div class="discret">{r.titre}</div>
        </td>
        <td><span class="pastille {r.statut}">{LIBELLES_STATUT[r.statut]}</span></td>
        <td>{r.commentaire ?? ''}</td>
      </tr>
    {/each}
  </tbody>
</table>
