<!--
  Méthodologie publique. Elle reprend les règles de docs/METHODO.md, avec la même numérotation :
  toute règle modifiée là doit l'être ici.
-->
<script lang="ts">
  import { NOM } from '$lib/site';

  let { data } = $props();
</script>

<svelte:head>
  <title>Méthodologie, {NOM}</title>
  <meta
    name="description"
    content="Comment les textes sont qualifiés et comment les scores sont calculés : des règles fixes et publiques."
  />
</svelte:head>

<h1>Méthodologie</h1>
<p class="chapo">
  Le site mesure une chose : quand un député vote sur un texte qui touche aux droits et libertés,
  vote-t-il dans le sens de ces droits ? Pour y répondre sans jugement au cas par cas, il applique
  des règles fixes, numérotées ci-dessous. Elles valent pour tous les textes et tous les députés.
</p>

<nav aria-label="Sommaire" class="sommaire">
  <ol>
    <li><a href="#qualification">Qualifier un texte</a></li>
    <li><a href="#preparation">Qui qualifie, et comment</a></li>
    <li><a href="#scrutins">Les scrutins retenus</a></li>
    <li><a href="#groupes">La position d’un groupe</a></li>
    <li><a href="#scores">Le calcul des scores</a></li>
    <li><a href="#donnees">Les données</a></li>
    <li><a href="#limites">Les limites</a></li>
  </ol>
</nav>

<section id="qualification">
  <h2>Qualifier un texte</h2>
  <p>
    Chaque texte retenu reçoit un <strong>droit principal</strong> et, souvent, des droits
    secondaires, pris dans une grille de <a href="/droits">onze droits</a>. Pour chacun, un sens :
    le texte <strong>étend</strong> ce droit, ou il le <strong>restreint</strong>. Chaque jugement
    cite au moins une source publique, affichée à côté de lui.
  </p>
  <ol class="regles">
    <li value="1">
      <strong>Point de vue.</strong> Le sens se lit du point de vue des droits des personnes concernées,
      jamais de celui des prérogatives de l’État. Un texte qui donne de nouveaux moyens à la police restreint
      les garanties des personnes face à elle.
    </li>
    <li value="2">
      <strong>Périmètre.</strong> La grille suit les droits des personnes face à la puissance publique
      et aux plus forts. La propriété et l’ordre public sont des objectifs que la loi concilie avec ces
      droits : ils n’entrent pas dans la grille. Quand un texte les étend, c’est signalé en point de vigilance.
    </li>
    <li value="3">
      <strong>Recouvrements.</strong> Justice des mineurs : droits de l’enfant en principal, police et
      justice en secondaire. Technique de surveillance : vie privée en principal, libertés publiques seulement
      si une source le relève. Mesure qui ne vise que des étrangers : droits des personnes étrangères
      en principal.
    </li>
    <li value="4">
      <strong>Sens droit par droit.</strong> Il n’y a pas de sens « mixte ». Chaque droit touché a le
      sien ; celui du texte est celui de son droit principal. Exemple : la loi immigration de 2024 restreint
      les droits des personnes étrangères et étend ceux de l’enfant.
    </li>
    <li value="5">
      <strong>Points de vigilance.</strong> Les critiques sourcées sur la mise en œuvre ou sur l’insuffisance
      des garanties s’affichent à côté du jugement, sans le modifier.
    </li>
    <li value="6">
      <strong>Objet qualifié.</strong> On qualifie le texte soumis au vote décisif, puisque c’est ce vote
      qui est mesuré. La décision du Conseil constitutionnel s’affiche à côté.
    </li>
    <li value="7">
      <strong>Sources.</strong> Commission nationale consultative des droits de l’homme (CNCDH), Défenseur
      des droits, Conseil constitutionnel, CNIL, Contrôleur général des lieux de privation de liberté,
      rapporteurs et comités de l’ONU, ONG ; pour la santé, ordres professionnels et sociétés savantes.
      Quand un texte étend un droit contesté, au moins une source critique figure en vigilance.
    </li>
    <li value="8">
      <strong>Textes purement organisationnels.</strong> Ils ne sont pas qualifiés. Les textes
      examinés puis écartés sont <a href="/textes">publiés avec leur motif</a>.
    </li>
  </ol>
</section>

<section id="preparation">
  <h2>Qui qualifie, et comment</h2>
  <p>
    Chaque qualification est <strong>préparée avec un assistant d’intelligence artificielle</strong>
    (Claude, d’Anthropic). L’assistant rassemble les avis publiés sur le texte, lit les scrutins de l’Assemblée
    et propose les droits touchés, leur sens, les sources et les scrutins à retenir, en appliquant les
    règles de cette page.
  </p>
  <p>
    Une personne relit ensuite chaque proposition, la corrige au besoin et la valide. <strong
      >Aucune qualification n’est publiée sans cette validation humaine.</strong
    > Les choix de méthode, eux, ne sont jamais délégués : la grille, les règles de calcul et le sens
    de chaque scrutin compté sont arrêtés par une personne et publiés ici.
  </p>
  <p>
    Chaque publication est enregistrée dans l’historique public du <a
      href="https://github.com/m4xim1nus/leurs-voix-nos-droits/commits/main/data/editorial.json"
      >dépôt de code</a
    >, qui garde la trace de chaque modification.
  </p>
</section>

<section id="scrutins">
  <h2>Les scrutins retenus</h2>
  <ol class="regles">
    <li value="9">
      <strong>Vote décisif.</strong> Le dernier vote de l’Assemblée sur l’ensemble du texte : lecture
      définitive, texte de la commission mixte paritaire, ou dernière lecture à l’Assemblée quand le texte
      est adopté définitivement au Sénat. Les votes des autres lectures sont affichés, pas comptés.
    </li>
    <li value="10">
      <strong>Motions de rejet : affichées, pas comptées.</strong> Une motion peut être votée pour des
      raisons tactiques. Sur la loi immigration, la motion de rejet a été adoptée avec les voix de groupes
      qui ont ensuite voté le texte. La compter comme une opposition au texte les créditerait d’un vote
      favorable aux droits.
    </li>
    <li value="11">
      <strong>Amendements clés.</strong> Seuls comptent les amendements qui suppriment ou rétablissent
      un article portant une mesure mise en cause par une source. Leur sens se fixe d’après le contenu
      de l’article, pas d’après la nature de l’amendement : supprimer un article qui ajoute une garantie
      va contre les droits. Un seul scrutin par article (celui qui en a fixé le sort), et une seule lecture
      : la dernière où des suppressions ont été mises aux voix. Ne comptent pas : la suppression de l’article
      unique d’un texte (elle double le vote décisif) et un scrutin sans aucune voix d’un côté (il ne
      départage personne).
    </li>
  </ol>
</section>

<section id="groupes">
  <h2>La position d’un groupe</h2>
  <ol class="regles">
    <li value="12">
      <strong>Majorité des exprimés, toujours avec sa cohésion.</strong> La position d’un groupe est celle
      de la majorité de ses membres qui ont voté pour ou contre. Si les abstentions dépassent à la fois
      les pour et les contre, le groupe est « majoritairement abstentionniste ». À égalité, il est « partagé
      ». La cohésion est la part des votants du groupe (pour, contre et abstention) qui ont voté comme
      lui. Exemple : 10 pour, 2 contre et 8 abstentions donnent « pour », avec une cohésion de 50 %.
    </li>
    <li value="13">
      <strong>Mises au point.</strong> Un député qui déclare après coup qu’il voulait voter autrement
      ne change pas le résultat officiel : sa déclaration n’est pas comptée.
    </li>
  </ol>
</section>

<section id="scores">
  <h2>Le calcul des scores</h2>
  <ol class="regles">
    <li value="14">
      <strong>Vote favorable aux droits.</strong> Sur chaque scrutin compté, voter pour est favorable
      ou défavorable selon deux sens : celui du texte (il étend ou restreint le droit) et celui du scrutin
      (voter pour soutient le texte, ou s’y oppose). Sur un texte qui restreint un droit, voter contre
      le texte est favorable, et voter la suppression d’un de ses articles restrictifs aussi.
    </li>
    <li value="15">
      <strong>Score.</strong> La part des votes favorables parmi les votes comptés, de 0 à 100 %, pondérée
      selon la règle 18. Le score d’ensemble prend le sens du droit principal de chaque texte. Le score
      d’un droit compte les textes où il est principal et ceux où il est secondaire, chacun avec son propre
      sens.
    </li>
    <li value="16">
      <strong>Abstention : hors calcul.</strong> Elle n’entre pas dans le score et s’affiche à côté. Elle
      n’est donc jamais comptée comme un vote contre.
    </li>
    <li value="17">
      <strong>Absences : hors calcul.</strong> Un député absent, ou présent sans voter (c’est souvent
      la présidence de séance), n’a pas de vote sur ce scrutin. Sa participation s’affiche à côté du score
      : la part des scrutins comptés, tenus pendant son mandat, où il a voté pour, contre ou s’est abstenu.
    </li>
    <li value="18">
      <strong>Chaque texte pèse autant.</strong> Le vote décisif vaut la moitié du texte, les amendements
      clés se partagent l’autre moitié à parts égales. Un texte sans amendement clé ne compte que son
      vote décisif. Un texte à neuf amendements clés n’écrase donc pas les autres.
    </li>
    <li value="19">
      <strong>Changement de groupe.</strong> Chaque vote compte pour le groupe où siégeait le député ce
      jour-là, d’après le décompte officiel de l’Assemblée. La fiche d’un député réunit tous ses votes.
      Un groupe qui change de nom reste un seul groupe, sous son nom le plus récent. Le score d’un groupe
      réunit les votes de ses membres, pas ses positions.
    </li>
  </ol>
  <p class="petit discret">
    Les scores s’affichent arrondis à l’unité ; les données téléchargeables les donnent au dixième.
  </p>
</section>

<section id="donnees">
  <h2>Les données</h2>
  <p>
    Les votes viennent uniquement de l’open data officiel de l’Assemblée nationale : scrutins, votes
    nominatifs, dossiers législatifs, députés et groupes. D’autres sites (datan.fr, leurs-votes.fr)
    servent à vérifier les décomptes, jamais de source. Le périmètre couvre les XVIe et XVIIe
    législatures, depuis juin 2022.
  </p>
  <p>
    <strong>Code postal.</strong> Il n’existe pas de table officielle qui relie un code postal à une circonscription.
    Le site joint la base officielle des codes postaux (La Poste), qui donne les communes de chaque code,
    aux résultats des législatives de 2024 par bureau de vote (ministère de l’Intérieur), qui donnent
    la circonscription de chaque commune. Les communes sont ramenées au code officiel géographique en
    vigueur (Insee). Le découpage légal, lui, est fixé par le code électoral : ces résultats n’en sont
    qu’un reflet fidèle. Quand une commune est partagée entre plusieurs circonscriptions, le site affiche
    tous les députés possibles.
  </p>
  <p>
    Tout est <a href="/donnees">téléchargeable</a> : qualifications, scores, votes nominatifs.
    Données à jour du {data.genereLe.slice(0, 10).split('-').reverse().join('/')}.
  </p>
</section>

<section id="limites">
  <h2>Les limites</h2>
  <ul>
    <li>
      Un score ne dit que ce qu’il mesure : des votes en séance, sur les textes qualifiés. Il ne dit
      rien du travail en commission, des amendements déposés ni des prises de parole.
    </li>
    <li>
      Avec peu de textes, un score sur un droit repose sur peu de votes : le nombre de textes est
      toujours affiché à côté.
    </li>
    <li>
      Les amendements se votent souvent en séance ordinaire, où peu de députés sont présents. La
      participation aux scrutins comptés est donc souvent basse, sans que cela dise tout de
      l’assiduité d’un député.
    </li>
    <li>
      Le Sénat et la législature 2017-2022 ne sont pas encore couverts. Ils le seront dans des
      étapes suivantes.
    </li>
  </ul>
</section>

<style>
  .sommaire ol {
    columns: 2 14rem;
    padding-left: 1.2rem;
  }
  .regles {
    padding-left: 1.6rem;
  }
  .regles li {
    margin-bottom: 0.8rem;
  }
  .regles li::marker {
    font-family: var(--titre);
    font-stretch: 75%;
    font-weight: 800;
  }
  section {
    scroll-margin-top: 1rem;
  }
</style>
