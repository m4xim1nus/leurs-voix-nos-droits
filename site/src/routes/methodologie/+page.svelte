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
    content="Comment les textes sont qualifiés et comment les scores sont calculés : des règles fixes et publiques."
  />
</svelte:head>

<h1>Méthodologie</h1>
<p class="chapo">
  Le site mesure une chose : quand un·e député·e vote sur un texte qui touche aux droits et
  libertés, vote-t-il dans le sens de ces droits ? Pour y répondre sans jugement au cas par cas, il
  applique des règles fixes, numérotées ci-dessous. Elles valent pour tous les textes et tous les
  député·es.
</p>

<nav aria-label="Sommaire" class="sommaire">
  <ol>
    <li><a href="#qualification">Qualifier un texte</a></li>
    <li><a href="#preparation">Qui qualifie, et comment</a></li>
    <li><a href="#scrutins">Les scrutins retenus</a></li>
    <li><a href="#groupes">La position d’un groupe</a></li>
    <li><a href="#scores">Le calcul des scores</a></li>
    <li><a href="#en-cours">Les textes en cours</a></li>
    <li><a href="#senat">Le Sénat</a></li>
    <li><a href="#donnees">Les données</a></li>
    <li><a href="#limites">Les limites</a></li>
  </ol>
</nav>

<section id="qualification">
  <h2>Qualifier un texte</h2>
  <p>
    Chaque texte retenu reçoit un <strong>droit principal</strong> et, souvent, des droits
    secondaires, pris dans une grille de <a href="/droits">douze droits</a>. Pour chacun, un sens :
    le texte <strong>étend</strong> ce droit, ou il le <strong>restreint</strong>. Chaque jugement
    cite au moins une source publique, affichée à côté de lui.
  </p>
  <ol class="regles">
    <li value="1" id="regle-1">
      <strong>Point de vue.</strong> Le sens se lit du point de vue des droits des personnes concernées,
      jamais de celui des prérogatives de l’État. Un texte qui donne de nouveaux moyens à la police restreint
      les garanties des personnes face à elle.
    </li>
    <li value="2" id="regle-2">
      <strong>Périmètre.</strong> La grille suit les droits des personnes face à la puissance publique
      et aux plus forts. La propriété et l’ordre public sont des objectifs que la loi concilie avec ces
      droits : ils n’entrent pas dans la grille. Quand un texte les étend, c’est signalé en point de vigilance.
      L’accès aux soins entre dans le droit à la santé (installation des médecins, accès direct aux professionnels).
      La formation professionnelle entre dans les droits au travail et à la protection sociale. Le choix
      d’une source d’énergie (nucléaire, renouvelables) n’est pas un droit de la grille : le droit à un
      environnement sain se juge sur les garanties des personnes (information, participation du public,
      protection des milieux). Les droits civiques couvrent qui peut voter et être élu, et les conditions
      d’exercice du vote (inscription, procuration, vote par correspondance) ; le mode de scrutin et le
      régime des mandats (cumul, incompatibilités) relèvent de l’organisation des pouvoirs publics et
      n’entrent pas dans la grille. L’inégalité de revenu n’entre pas dans le droit à l’égalité et à la
      non-discrimination : un argument de ce type s’affiche en point de vigilance.
    </li>
    <li value="3" id="regle-3">
      <strong>Recouvrements.</strong> Justice des mineurs : droits de l’enfant en principal, police et
      justice en secondaire. Technique de surveillance : vie privée en principal, libertés publiques seulement
      si une source le relève. Mesure qui ne vise que des étrangers : droits des personnes étrangères
      en principal. Mesure qui ne vise que des personnes détenues : le droit en cause en principal (le
      droit de vote, par exemple), police et justice en secondaire.
    </li>
    <li value="4" id="regle-4">
      <strong>Sens droit par droit.</strong> Il n’y a pas de sens « mixte ». Chaque droit touché a le
      sien ; celui du texte est celui de son droit principal. Exemple : la loi immigration de 2024 restreint
      les droits des personnes étrangères et étend ceux de l’enfant. Le sens se lit par rapport au droit
      applicable au jour du vote, jurisprudence comprise : une loi qui plafonne ce que les tribunaux accordaient
      déjà restreint le droit, tout comme une loi qui rétablit une règle que le Conseil constitutionnel
      avait abrogée, même assortie de la garantie qu’il exigeait. Le droit applicable comprend son échéance
      légale : prolonger un dispositif protecteur avant son extinction étend le droit. Dans un texte dont
      les mesures vont en sens opposés pour un même droit, ce droit prend le sens des mesures que les
      sources citent le plus souvent, et la mesure de sens opposé s’affiche en point de vigilance. Une
      mesure sur le corps électoral se lit, pour les droits civiques, sur le droit de vote des personnes
      qu’elle ajoute à la liste ou en retire ; quand une source y voit une atteinte aux droits d’un peuple
      autochtone, le texte reçoit aussi le droit à l’égalité et à la non-discrimination, au sens « restreint ».
      Les deux lectures sont alors comptées.
    </li>
    <li value="5" id="regle-5">
      <strong>Points de vigilance.</strong> Les critiques sourcées sur la mise en œuvre ou sur l’insuffisance
      des garanties s’affichent à côté du jugement, sans le modifier.
    </li>
    <li value="6" id="regle-6">
      <strong>Objet qualifié.</strong> On qualifie le texte soumis au vote décisif, puisque c’est ce vote
      qui est mesuré. La décision du Conseil constitutionnel s’affiche à côté.
    </li>
    <li value="7" id="regle-7">
      <strong>Sources.</strong> Commission nationale consultative des droits de l’homme (CNCDH), Défenseur
      des droits, Conseil constitutionnel, CNIL, Contrôleur général des lieux de privation de liberté
      et autres instances consultatives indépendantes qui rendent des avis publics (dont le Haut Conseil
      de la famille, de l’enfance et de l’âge), ANSES pour la santé et l’environnement, rapporteurs et
      comités de l’ONU, ONG ; pour la santé, ordres professionnels et sociétés savantes ; organisations
      professionnelles et syndicales du droit, de la santé et de l’enseignement (Conseil national des
      barreaux, syndicats d’avocats et de magistrats…) ; organisations syndicales représentatives de salariés,
      leurs fédérations professionnelles, leurs syndicats nationaux de branche et leurs unions confédérales
      de retraités ; avis du Conseil d’État sur un projet ou une proposition de loi. L’UNAF est admise,
      avec la mention de son statut institutionnel. Une association qui porte elle-même un dispositif
      est admise pour en décrire un risque, avec la mention qu’elle est partie prenante. Les rapports
      parlementaires et les positions du Gouvernement ou des groupes ne sont pas des sources : ils sont
      parties au débat. La Cour des comptes non plus : elle évalue la dépense publique, pas les droits.
      Une source peut porter sur la mesure plutôt que sur le texte, même si elle lui est antérieure. Quand
      un texte étend un droit contesté, au moins une source critique figure en vigilance. Si aucune source
      admise ne le conteste, la qualification le dit.
    </li>
    <li value="8" id="regle-8">
      <strong>Textes purement organisationnels.</strong> Ils ne sont pas qualifiés, pas plus que les
      résolutions, qui expriment un avis de l’Assemblée sans changer aucune règle, ni les lois qui
      autorisent la ratification d’une convention internationale, ni un texte qui, au vote décisif,
      ne contient plus aucune mesure (ses articles ont été supprimés). Les motions de censure
      spontanées (article 49, alinéa 2) ne sont pas qualifiées non plus : elles ne portent sur aucun
      texte. Les lois de finances de fin de gestion, qui ne font qu’ouvrir et annuler les crédits de
      l’année, ne le sont pas non plus ; les lois de finances initiales et rectificatives se
      qualifient comme les autres textes. Une réforme de structure n’est pas purement
      organisationnelle si une source admise la met en cause au nom d’un droit de la grille. Les
      textes examinés puis écartés sont
      <a href="/textes">publiés avec leur motif</a>.
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
    > Les choix de méthode, eux, ne sont jamais délégués : la grille, les règles de calcul et le sens
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
    <li value="9" id="regle-9">
      <strong>Vote décisif.</strong> Le dernier vote de l’Assemblée sur l’ensemble du texte : lecture
      définitive, texte de la commission mixte paritaire, ou dernière lecture à l’Assemblée quand le texte
      est adopté définitivement au Sénat. Les votes des autres lectures sont affichés, pas comptés. Un
      texte dont le vote décisif n’a recueilli aucune voix d’un des deux côtés n’est pas qualifié : ce
      vote ne départage personne, et le compter rapprocherait tous les scores de 100 %. Un texte à article
      unique sans vote sur l’ensemble (article rejeté, puis texte tombé ou retiré) : le vote sur l’article
      tient lieu de vote décisif. De même quand l’amendement qui supprime l’article unique est adopté
      et que le texte n’est plus voté : voter pour, c’est alors voter contre le texte. Un texte adopté
      par le 49.3, sans vote final : il est qualifié, mais ne compte dans aucun score, car le scrutin
      sur une motion de censure n’enregistre que les voix pour la censure. Ses motions de censure s’affichent,
      groupe par groupe. Quand le dernier vote sur l’ensemble n’est pas un scrutin public, le dernier
      scrutin public reste le vote décisif, avec la date du texte sur lequel il a porté : c’est le seul
      vote nominatif disponible. Quand une loi de finances est rejetée par le rejet d’une de ses parties,
      sans vote sur l’ensemble, ce vote est affiché mais n’est pas décisif, car il ne porte pas sur les
      mesures de la partie non discutée ; à défaut d’un vote ultérieur sur l’ensemble, le texte n’est
      pas qualifié.
    </li>
    <li value="10" id="regle-10">
      <strong>Motions de rejet : affichées, pas comptées.</strong> Une motion peut être votée pour des
      raisons tactiques. Sur la loi immigration, la motion de rejet a été adoptée avec les voix de groupes
      qui ont ensuite voté le texte. La compter comme une opposition au texte les créditerait d’un vote
      favorable aux droits. Une motion déposée et adoptée par les soutiens du texte, pour l’envoyer directement
      en commission mixte paritaire, s’affiche dans ce sens : la voter, c’est soutenir le texte.
    </li>
    <li value="11" id="regle-11">
      <strong>Amendements clés.</strong> Seuls comptent les amendements qui suppriment ou rétablissent
      un article portant une mesure mise en cause par une source. Leur sens se fixe d’après le contenu
      de l’article, pas d’après la nature de l’amendement : supprimer un article qui ajoute une garantie
      va contre les droits. Un article dont le sens n’est pas univoque n’est pas retenu, y compris quand
      les sources ne s’accordent pas sur ce sens. Un seul scrutin par article (celui qui en a fixé le
      sort), et une seule lecture : la dernière où des suppressions ont été mises aux voix. Ne comptent
      pas : la suppression de l’article unique d’un texte (elle double le vote décisif), ou de l’article
      qui est le seul du texte au vote décisif, et un scrutin sans aucune voix d’un côté (il ne départage
      personne).
    </li>
  </ol>
</section>

<section id="groupes">
  <h2>La position d’un groupe</h2>
  <ol class="regles">
    <li value="12" id="regle-12">
      <strong>Majorité des exprimés, toujours avec sa cohésion.</strong> La position d’un groupe est celle
      de la majorité de ses membres qui ont voté pour ou contre. Si les abstentions dépassent à la fois
      les pour et les contre, le groupe est « majoritairement abstentionniste ». À égalité, il est « partagé
       ». La cohésion est la part des votants du groupe (pour, contre et abstention) qui ont voté comme
      lui. Exemple : 10 pour, 2 contre et 8 abstentions donnent « pour », avec une cohésion de 50 %.
    </li>
    <li value="13" id="regle-13">
      <strong>Mises au point.</strong> Un·e député·e qui déclare après coup avoir voulu voter autrement
      ne change pas le résultat officiel : sa déclaration n’est pas comptée.
    </li>
  </ol>
</section>

<section id="scores">
  <h2>Le calcul des scores</h2>
  <ol class="regles">
    <li value="14" id="regle-14">
      <strong>Vote favorable aux droits.</strong> Sur chaque scrutin compté, voter pour est favorable
      ou défavorable selon deux sens : celui du texte (il étend ou restreint le droit) et celui du scrutin
      (voter pour soutient le texte, ou s’y oppose). Sur un texte qui restreint un droit, voter contre
      le texte est favorable, et voter la suppression d’un de ses articles restrictifs aussi. Le score
      mesure le vote, pas son motif : un groupe qui vote contre un texte étendant un droit parce qu’il
      le juge insuffisant est compté défavorable, comme celui qui s’y oppose sur le fond.
    </li>
    <li value="15" id="regle-15">
      <strong>Score.</strong> La part des votes favorables parmi les votes comptés, de 0 à 100 %,
      pondérée pour que <a href="#regle-18">chaque texte pèse autant</a>, quel que soit son nombre
      de scrutins comptés. Le score d’ensemble prend le sens du droit principal de chaque texte. Le
      score d’un droit compte les textes où il est principal et ceux où il est secondaire, chacun
      avec son propre sens.
    </li>
    <li value="16" id="regle-16">
      <strong>Abstention : hors calcul.</strong> Elle n’entre pas dans le score et s’affiche à côté. Elle
      n’est donc jamais comptée comme un vote contre.
    </li>
    <li value="17" id="regle-17">
      <strong>Absences : hors calcul.</strong> Un·e député·e absent·e, ou présent·e sans voter (c’est
      souvent la présidence de séance), n’a pas de vote sur ce scrutin. Sa participation s’affiche à côté
      du score : la part des scrutins comptés, tenus pendant son mandat, où il a voté pour, contre ou
      s’est abstenu.
    </li>
    <li value="18" id="regle-18">
      <strong>Chaque texte pèse autant.</strong> Le vote décisif vaut la moitié du texte, les amendements
      clés se partagent l’autre moitié à parts égales. Un texte sans amendement clé ne compte que son
      vote décisif. Un texte à neuf amendements clés n’écrase donc pas les autres.
    </li>
    <li value="19" id="regle-19">
      <strong>Changement de groupe.</strong> Chaque vote compte pour le groupe où siégeait l’élu·e ce
      jour-là, d’après le décompte officiel de l’Assemblée. La fiche d’un·e député·e réunit tous ses votes.
      Un groupe qui change de nom reste un seul groupe, sous son nom le plus récent. Le score d’un groupe
      réunit les votes de ses membres, pas ses positions.
    </li>
  </ol>
  <p class="petit discret">
    Les scores s’affichent arrondis à l’unité ; les données téléchargeables les donnent au dixième.
  </p>
</section>

<section id="en-cours">
  <h2>Les textes en cours</h2>
  <ol class="regles">
    <li value="20" id="regle-20">
      <strong>État d’un texte.</strong> L’état d’un texte est un fait lu dans l’open data, jamais une
      appréciation : loi promulguée, en navette (avec la chambre où il est attendu), à l’arrêt, rejeté,
      retiré. Il vient du dossier de l’Assemblée et des décisions de séance publiées par le Sénat, et
      il est daté du jour des données. Un texte est dit « à l’arrêt » quand aucun acte n’a été enregistré
      depuis 12 mois. Un texte « inscrit » figure à l’ordre du jour d’une séance : il n’est pas forcément
      examiné à cette date, ni voté. L’état n’entre dans aucun score.
    </li>
    <li value="21" id="regle-21">
      <strong>Texte qualifié encore en navette.</strong> Son dernier vote sur l’ensemble à l’Assemblée
      reste décisif et compte dans les scores, avec la mention « vote de 1re lecture, texte encore en
      navette » (la lecture est celle du scrutin). Son sens se lit « sur le texte voté le… » : le texte
      peut encore changer. Après un nouveau vote sur l’ensemble, le sens est relu sur le texte voté. Jusqu’à
      cette relecture, l’ancien vote décisif reste compté et le nouveau vote s’affiche avec la mention
      « pas encore qualifié ». Un texte à l’arrêt affiche son état, sans cette mention.
    </li>
    <li value="22" id="regle-22">
      <strong>Fiche de suivi.</strong> Un texte sans vote qualifié peut être suivi avant le vote. Il
      est retenu à la main : les mots-clés ne font que présélectionner. Sa fiche donne les droits
      qu’il touche et des sources publiques admises, au moins une par droit,
      <strong>sans sens ni score</strong>. Aucun scrutin n’y est retenu. Faute de source admise, il
      n’y a pas de fiche. Après le vote, le texte est qualifié ou écarté selon les règles communes,
      et sa fiche disparaît. La page des
      <a href="/en-cours">textes en cours</a> n’affiche que ces textes suivis et les textes qualifiés
      encore en navette.
    </li>
  </ol>
</section>

<section id="senat">
  <h2>Le Sénat</h2>
  <p>
    Les règles 1 à 8 s’appliquent au Sénat, de même que les règles 12 à 14 et 20. Les règles
    ci-dessous remplacent, pour le Sénat, les règles 9 à 11 et 15 à 19.
  </p>
  <ol>
    <li value="23" id="regle-23">
      <strong>Scrutin décisif du Sénat</strong> : le dernier scrutin public du Sénat sur l’ensemble
      du texte, ou sur son article unique. Il est compté s’il a au moins une voix de chaque côté et
      si son sens est établi (règle 24). Sinon, il est affiché et non compté. Les autres lectures et
      les parties d’une loi de finances sont affichées, pas comptées. Les motions aussi, question
      préalable comprise, même quand elle met fin à l’examen du texte. Les crédits d’une mission et
      les amendements ne sont pas retenus. Quand le dernier vote sur l’ensemble n’est pas public, le
      dernier scrutin public reste décisif, avec la mention « dernier vote public, sur le texte du
      JJ/MM/AAAA ».
    </li>
    <li value="24" id="regle-24">
      <strong>Chaque vote se lit sur le texte voté.</strong> Si le Sénat a voté le même texte que le scrutin
      décisif de l’Assemblée (conclusions de la commission mixte paritaire, adoption sans modification
      par l’une des chambres), le sens est repris. S’il a voté une autre version, le sens est relu sur
      cette version et sourcé (règle 7). La source peut porter sur la mesure, à condition que la lecture
      du texte voté montre qu’il s’agit bien de la même. Sans source admise, le vote est affiché et non
      compté, et aucun sens n’est donné. Sur un texte rejeté par le Sénat, le sens se lit sur la version
      mise aux voix, pas sur celle de l’Assemblée.
    </li>
    <li value="25" id="regle-25">
      <strong>Texte voté au seul Sénat.</strong> Il est trié, puis qualifié s’il entre dans la grille
      (règles 2 et 8). Il ne compte que dans les scores du Sénat, avec la mention « pas de vote sur l’ensemble
      à l’Assemblée », qui vaut aussi pour un texte que l’Assemblée a rejeté par une motion ou à main
      levée. Un texte attendu à l’Assemblée est qualifié dès le vote du Sénat, sans attendre son inscription,
      avec la mention « texte encore en navette, attendu à l’Assemblée ». Un texte à l’arrêt affiche son
      état (règle 20), sans cette mention. Il ne compte dans les scores de l’Assemblée qu’après un vote
      de l’Assemblée. Chaque chambre garde alors son décisif, chacun lu sur son texte. Comme à la règle
      21, un nouveau vote du Sénat sur l’ensemble est relu sur le texte voté. Jusque-là, l’ancien décisif
      reste compté et le nouveau vote porte la mention « pas encore qualifié ». Un décisif du Sénat sur
      un texte encore en navette porte la mention « vote de 1re lecture au Sénat, texte encore en navette »
      (la lecture est celle du scrutin).
    </li>
    <li value="26" id="regle-26">
      <strong>Scores du Sénat.</strong> Chaque texte pèse 1 et ne compte que son décisif : pas d’amendements
      clés. Un texte adopté par le 49.3 à l’Assemblée compte au Sénat s’il y a eu un vote sur l’ensemble
      (règles 23 et 24). Abstentions et non-votants sont hors calcul. Le calcul du score par droit, le
      groupe du jour du vote et l’agrégation des votes dans le score d’un groupe sont ceux des règles
      15 et 19. Il n’y a qu’une période : depuis le 28/06/2022, sans découpage, puisque le Sénat n’a pas
      de législature et se renouvelle par moitié. Le nombre de votes comptés s’affiche à côté du score :
      un·e élu·e récent·e en a peu.
    </li>
    <li value="27" id="regle-27">
      <strong>Vote de groupe.</strong> Sur presque chaque scrutin public du Sénat, un vote est enregistré
      pour presque tous les sièges, et il suit presque toujours la majorité du groupe. Le règlement du
      Sénat permet de voter par délégation et par procédé électronique. Public Sénat décrit la pratique
      en avril 2025 : « un seul sénateur peut voter pour l’ensemble de son groupe ». Ces votes sont les
      résultats officiels, et on les compte tels quels. Ils ne disent pas qui était présent, et ils peuvent
      ne pas refléter un choix individuel. La fiche d’un·e sénateur·ice affiche donc un score « d’après
      les votes enregistrés à son nom » et met en avant ses écarts au groupe. Elle n’affiche aucun taux
      de participation. La page du Sénat présente d’abord les groupes.
    </li>
    <li value="28" id="regle-28">
      <strong>Deux chambres séparées.</strong> Aucun score ne mélange les deux chambres. Aucun score d’un·e
      député·e n’est comparé à celui d’un·e sénateur·ice, puisque les textes comptés diffèrent. Aucune
      correspondance n’est établie entre les groupes des deux chambres : ils sont côte à côte, chacun
      sous son sigle. Un texte écarté (règles 8 et 9) l’est pour les deux chambres : son vote au Sénat
      n’entre dans aucun score.
    </li>
  </ol>
</section>

<section id="donnees">
  <h2>Les données</h2>
  <p>
    Les votes viennent uniquement de l’open data officiel de l’Assemblée nationale et du Sénat :
    scrutins, votes nominatifs, dossiers législatifs, élu·es et groupes. D’autres sites (datan.fr,
    leurs-votes.fr) servent à vérifier les décomptes, jamais de source. Le périmètre couvre les XVIe
    et XVIIe législatures, depuis juin 2022.
  </p>
  <p>
    <strong>Code postal.</strong> Il n’existe pas de table officielle qui relie un code postal à une circonscription.
    Le site joint la base officielle des codes postaux (La Poste), qui donne les communes de chaque code,
    aux résultats des législatives de 2024 par bureau de vote (ministère de l’Intérieur), qui donnent
    la circonscription de chaque commune. Les communes sont ramenées au code officiel géographique en
    vigueur (Insee). Le découpage légal, lui, est fixé par le code électoral : ces résultats n’en sont
    qu’un reflet fidèle. Quand une commune est partagée entre plusieurs circonscriptions, le site affiche
    tous les député·es possibles.
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
      Un score ne dit que ce qu’il mesure : des votes en séance, sur les textes qualifiés. Il ne dit
      rien du travail en commission, des amendements déposés ni des prises de parole.
    </li>
    <li>
      Avec peu de textes, un score sur un droit repose sur peu de votes : le nombre de textes est
      toujours affiché à côté.
    </li>
    <li>
      Les amendements se votent souvent en séance ordinaire, où peu de député·es sont présent·es. La
      participation aux scrutins comptés est donc souvent basse, sans que cela dise tout de
      l’assiduité d’un·e député·e.
    </li>
    <li>
      La législature 2017-2022 n’est pas encore couverte. Elle le sera dans une étape suivante.
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
    padding-left: 0.3rem;
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
