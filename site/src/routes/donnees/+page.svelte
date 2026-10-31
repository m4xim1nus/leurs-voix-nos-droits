<script lang="ts">
  import { DEPOT, NOM } from '$lib/site';

  let { data } = $props();
  const mo = (n: number) =>
    n < 1e6
      ? `${Math.max(1, Math.round(n / 1e3))} ko`
      : `${(n / 1e6).toFixed(1).replace('.', ',')} Mo`;

  const DESCRIPTION: Record<string, string> = {
    'textes.csv':
      'catalogue des textes (dossiers législatifs), qualifiés ou non : au moins un scrutin public à l’AN, en cours, inscrits à l’ordre du jour, ou votés au Sénat sur l’ensemble',
    'scrutins.csv': 'tous les scrutins publics, rattachés à leur dossier',
    'positions_groupes.csv': 'décompte et position de chaque groupe sur chaque scrutin',
    'amendements.csv':
      'amendements mis aux voix : auteur, article, sort ; leurs identiques pour la XVIIe seulement',
    'deputes.csv': 'député·es ayant siégé depuis 2022',
    'mandats.csv': 'mandats de député·e : circonscription, dates',
    'appartenances.csv': 'appartenance des député·es aux groupes, avec les dates',
    'groupes.csv': 'groupes politiques, couleur officielle et lignée',
    'mises_au_point.csv': 'mises au point de vote (affichées, pas comptées)',
    'scores_scrutins.csv': 'scrutins comptés : poids et vote favorable aux droits, droit par droit',
    'scores_deputes.csv': 'score de chaque député·e, par droit',
    'scores_groupes.csv': 'score de chaque groupe, par droit',
    'scores_deputes_textes.csv': 'score de chaque député·e, par texte',
    'scores_groupes_textes.csv': 'score de chaque groupe, par texte',
    'participation.csv': 'participation de chaque député·e aux scrutins comptés',
    'en_cours.csv':
      'textes votés au moins une fois depuis 2024, pas encore des lois, et motif d’écart',
    'en_cours_lectures.csv': 'lectures votées de ces textes : issue, scrutin de l’AN, mode de vote',
    'en_cours_evenements.csv': 'procédure accélérée, 49.3, CMP, saisine du Conseil constitutionnel',
    'en_cours_etats.csv': 'où en est chaque texte du catalogue',
    'en_cours_agenda.csv': 'ordre du jour de l’AN : points de séance et de commission à venir',
    'en_cours_alertes.csv': 'nouveaux votes et inscriptions à traiter pour la qualification',
    'senat/scrutins.csv': 'scrutins publics du Sénat depuis juin 2022, rattachés à leur dossier',
    'senat/positions_groupes.csv': 'décompte et position de chaque groupe sur chaque scrutin',
    'senat/senateurs.csv': 'sénateur·ices : département, courriel public',
    'senat/mandats.csv': 'mandats de sénateur·ice, avec les dates',
    'senat/appartenances.csv': 'appartenance aux groupes, avec les dates',
    'senat/groupes.csv': 'groupes du Sénat, sans correspondance avec ceux de l’Assemblée',
    'senat/mises_au_point.csv': 'mises au point de vote (affichées, pas comptées)',
    'senat/scores_scrutins.csv': 'décisifs comptés : vote favorable aux droits, droit par droit',
    'senat/scores_senateurs.csv': 'score de chaque sénateur·ice, par droit',
    'senat/scores_groupes.csv': 'score de chaque groupe, par droit',
    'senat/scores_senateurs_textes.csv': 'score de chaque sénateur·ice, par texte',
    'senat/scores_groupes_textes.csv': 'score de chaque groupe, par texte'
  };
</script>

<svelte:head><title>Données, {NOM}</title></svelte:head>

<h1>Données</h1>
<p class="chapo">
  Tout ce qu’affiche le site se télécharge ici, en CSV (UTF-8, séparateur virgule) ou en JSON. Les
  données sont sous <a href="https://www.etalab.gouv.fr/licence-ouverte-open-licence/"
    >Licence Ouverte 2.0</a
  >, le code sous licence MIT.
</p>

<h2>Les qualifications</h2>
<p>
  <a href="/donnees/editorial.json" download>editorial.json</a>
  <span class="discret">({mo(data.editorial)})</span>
  : pour chaque texte qualifié, les droits touchés, leur sens, la justification, les sources, les points
  de vigilance et les scrutins retenus avec leur sens. Les textes écartés y figurent avec leur motif.
  Son <a href="{DEPOT}/commits/main/data/editorial.json">historique</a> garde chaque publication.
</p>

<h2>Open data et scores</h2>
<div class="defile">
  <table>
    <tbody>
      {#each data.csv as f (f.nom)}
        <tr>
          <td><a href="/donnees/{f.nom}" download>{f.nom}</a></td>
          <td class="nombre discret">{mo(f.taille)}</td>
          <td>{DESCRIPTION[f.nom] ?? ''}</td>
        </tr>
      {/each}
    </tbody>
  </table>
</div>
<p class="petit">
  Contexte du dernier calcul (sources, dates de téléchargement, grille des droits) :
  <a href="/donnees/meta.json">meta.json</a>.
</p>

<h2>Votes nominatifs</h2>
<p>
  Tous les votes de chaque député·e, un fichier par mois : colonnes <code>scrutin</code> (numéro
  dans la législature), <code>acteur</code> (identifiant AN sans le préfixe <code>PA</code>) et
  <code>position</code> (P pour, C contre, A abstention, N non-votant).
</p>
<details>
  <summary>{data.votes.length} fichiers</summary>
  <ul class="votes">
    {#each data.votes as f (f.nom)}
      <li>
        <a href="/donnees/{f.nom}" download>{f.nom}</a> <span class="discret">{mo(f.taille)}</span>
      </li>
    {/each}
  </ul>
</details>

<h2>Sénat</h2>
<p>
  Fichiers à part : aucun score ne mélange les deux chambres. Votes nominatifs, un fichier par mois
  : colonnes <code>scrutin</code> (session-numéro), <code>senateur</code> (matricule),
  <code>position</code> (P, C, A, N), <code>statut</code>, <code>delegue_a</code> et
  <code>mise_au_point</code>. Le vote de groupe est expliqué à la
  <a href="/methodologie#regle-27">règle 27</a>.
</p>
<div class="defile">
  <table>
    <thead>
      <tr
        ><th scope="col">Fichier</th><th scope="col" class="nombre">Taille</th><th scope="col"
          >Contenu</th
        ></tr
      >
    </thead>
    <tbody>
      {#each data.senat as f (f.nom)}
        <tr>
          <td><a href="/donnees/{f.nom}" download>{f.nom}</a></td>
          <td class="nombre discret">{mo(f.taille)}</td>
          <td>{DESCRIPTION[f.nom] ?? ''}</td>
        </tr>
      {/each}
    </tbody>
  </table>
</div>
<details>
  <summary>{data.votesSenat.length} fichiers de votes</summary>
  <ul class="votes">
    {#each data.votesSenat as f (f.nom)}
      <li>
        <a href="/donnees/{f.nom}" download>{f.nom}</a> <span class="discret">{mo(f.taille)}</span>
      </li>
    {/each}
  </ul>
</details>

<h2>Annuaire</h2>
<ul>
  {#each data.annuaire as f (f.nom)}
    <li>
      <a href="/donnees/{f.nom}" download>{f.nom}</a> <span class="discret">({mo(f.taille)})</span>
    </li>
  {/each}
</ul>
<p class="petit">
  Code postal → commune → circonscription, avec la part des inscrits de la commune dans chaque
  circonscription ; courriel public de chaque député·e ; code postal → département, pour les
  sénateur·ices. Méthode : <a href="/methodologie#donnees">méthodologie</a>.
</p>

<style>
  .votes {
    columns: 3 12rem;
    font-size: 0.93rem;
  }
  summary {
    cursor: pointer;
    font-weight: 650;
  }
  td:first-child {
    white-space: nowrap;
  }
</style>
