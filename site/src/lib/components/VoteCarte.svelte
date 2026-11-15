<!--
  Un texte et le vote d'un·e député·e, en carte, pour sa fiche. Même langage que TexteCarte : une
  bande de couleur à gauche (en haut sur téléphone), qui dit ici ce que son vote a signifié pour le
  droit ; puis le titre officiel, son vote, la position de son groupe et le détail des scrutins
  comptés. Sous l'angle du droit choisi quand la liste est filtrée sur un droit (règle 15).
-->
<script lang="ts" module>
  import type { TexteCourt, VoteDepute } from '$lib/server/vues';
  import type { Sens } from '$lib/types';
  import type { Bilan } from '$lib/votes-depute';

  export interface TexteVote {
    texte: TexteCourt;
    votes: VoteDepute[];
    /** Scrutins du texte pendant son mandat, affichés sans être comptés (fiche texte). */
    autres: number;
    vu: { code: string; sens: Sens; inverse: boolean };
    /** Son score sur ce texte, sous l'angle du droit vu. */
    score: number | null;
    bilan: Bilan;
  }
</script>

<script lang="ts">
  import { court, phrase } from '$lib/droits';
  import {
    date,
    etatEnListe,
    legislature,
    mentionNavette,
    minuscule,
    pluriel,
    POSITION,
    POSITION_GROUPE,
    pourcent,
    ROLE
  } from '$lib/format';
  import { ecartGroupe, lectureVote } from '$lib/votes-depute';

  let {
    t,
    elle,
    surDroit = false
  }: {
    t: TexteVote;
    elle: boolean;
    /** Liste filtrée sur un droit. */ surDroit?: boolean;
  } = $props();

  const e = $derived(elle ? 'e' : '');
  const Il = $derived(elle ? 'Elle' : 'Il');
  const aux = $derived(surDroit ? 'à ce droit' : 'aux droits');
  const plusieurs = $derived(t.votes.length > 1);

  const LECTURE = {
    favorable: 'favorable aux droits',
    defavorable: 'défavorable aux droits',
    hors: 'hors calcul',
    'non-compte': 'non compté'
  };

  const bande = $derived.by(() => {
    if (t.bilan === 'favorable') return '▲\u00a0Favorable';
    if (t.bilan === 'defavorable') return '▼\u00a0Défavorable';
    if (t.bilan === 'partage') return '▲▼\u00a0Partagé';
    const p = new Set(t.votes.map((v) => v.position));
    if (p.has('abstention')) return 'Abstention';
    if (p.has('non_votant')) return `Non-votant${e}`;
    return `Absent${e}`;
  });
  const pourLecteur = $derived(
    `Pour ce droit (${court(t.vu.code)}), ${
      t.bilan === 'favorable'
        ? 'son vote est favorable'
        : t.bilan === 'defavorable'
          ? 'son vote est défavorable'
          : t.bilan === 'partage'
            ? 'ses votes vont dans les deux sens'
            : 'aucun vote pour ou contre de sa part, hors calcul'
    }.`
  );

  const meta = $derived(
    [
      `Voté le ${date(t.texte.date)}, ${legislature(t.texte.legislature)} législature`,
      etatEnListe(t.texte.etat, t.texte.etape)
    ]
      .filter(Boolean)
      .join(' · ')
  );

  function seul(p: VoteDepute['position']): string {
    if (p === 'pour' || p === 'contre') return `${Il} a voté ${p}.`;
    if (p === 'abstention') return `${Il} s’est abstenu${e}.`;
    if (p === 'non_votant') return `${Il} était non-votant${e}.`;
    return `${Il} était absent${e}.`;
  }
  const sonVote = $derived.by(() => {
    if (!plusieurs) return seul(t.votes[0].position);
    const memes = new Set(t.votes.map((v) => v.position));
    if (memes.size === 1)
      return `${seul(t.votes[0].position).slice(0, -1)} aux ${t.votes.length} scrutins comptés.`;
    const n = (p: VoteDepute['position']) => t.votes.filter((v) => v.position === p).length;
    const parts = [
      n('pour') && `${n('pour')} pour`,
      n('contre') && `${n('contre')} contre`,
      n('abstention') && pluriel(n('abstention'), 'abstention'),
      n('non_votant') && `${n('non_votant')} fois non-votant${e}`,
      n('absent') && pluriel(n('absent'), 'absence')
    ].filter(Boolean);
    return `Sur les ${t.votes.length} scrutins comptés : ${parts.join(', ')}.`;
  });

  const scoreTexte = $derived(
    plusieurs && t.score !== null
      ? ` Sur ce texte, ${pourcent(t.score)} de votes favorables ${aux}.`
      : ''
  );

  // Son groupe, au vote décisif s'il y en a plusieurs.
  const repere = $derived(t.votes.find((v) => v.scrutin.role === 'decisif') ?? t.votes[0]);
  const groupe = $derived.by(() => {
    const v = repere.ventilation;
    if (!repere.groupe || !v) return null;
    const ou = plusieurs ? `, ${minuscule(ROLE[repere.scrutin.role])}` : '';
    const cohesion = v.cohesion === null ? '' : `, cohésion ${pourcent(v.cohesion * 100)}`;
    return { ...repere.groupe, texte: `${ou} : ${POSITION_GROUPE[v.position]}${cohesion}.` };
  });
  const ecarts = $derived(t.votes.filter(ecartGroupe).length);
</script>

<article class="carte {t.bilan}">
  <div class="bande">
    <span class="sens" aria-hidden="true">{bande}</span>
    <span class="droit" aria-hidden="true">{court(t.vu.code)}</span>
    <span class="visuellement-cache">{pourLecteur}</span>
  </div>
  <div class="corps">
    <h4 class="titre"><a href="/textes/{t.texte.id}">{t.texte.titre}</a></h4>
    <p class="meta">{meta}</p>
    <p>Le texte {phrase(t.vu.code, t.vu.sens)}. <strong>{sonVote}</strong>{scoreTexte}</p>
    {#if groupe || ecarts}
      <p class="groupe">
        {#if groupe}
          <span
            >Son groupe <span class="sigle" style:--c={groupe.couleur}>{groupe.sigle}</span
            >{groupe.texte}</span
          >
        {/if}
        {#if ecarts}<span class="ecart"
            >Écart avec son groupe{plusieurs ? ` sur ${pluriel(ecarts, 'scrutin')}` : ''}</span
          >{/if}
      </p>
    {/if}
    <details>
      <summary>{plusieurs ? `Les ${t.votes.length} scrutins comptés` : 'Le scrutin compté'}</summary
      >
      <ul class="votes">
        {#each t.votes as v (v.scrutin.id)}
          {@const l = lectureVote(v, t.vu.inverse)}
          {@const mention = mentionNavette(t.texte.etat, v.scrutin.etape)}
          <li>
            <span
              ><a href={v.scrutin.url} rel="external">{v.scrutin.objet}</a>,
              <span class="discret">{date(v.scrutin.date)}{mention ? `, ${mention}` : ''}</span
              ></span
            >
            <span class="ligne">
              <strong>{v.position === 'absent' ? `Absent${e}` : POSITION[v.position]}</strong>
              <span class="lecture {l}">{LECTURE[l]}</span>
              {#if v.groupe}
                <span
                  ><span class="sigle" style:--c={v.groupe.couleur}>{v.groupe.sigle}</span
                  >{v.ventilation ? ` : ${POSITION_GROUPE[v.ventilation.position]}` : ''}</span
                >
              {/if}
              {#if ecartGroupe(v)}<span class="ecart">écart</span>{/if}
            </span>
          </li>
        {/each}
      </ul>
      {#if t.autres}
        <p class="discret">
          <a href="/textes/{t.texte.id}#autres-scrutins"
            >{pluriel(t.autres, 'autre scrutin', 'autres scrutins')} sur ce texte</a
          >, affichés sans être comptés.
        </p>
      {/if}
    </details>
  </div>
</article>

<style>
  .carte {
    display: flex;
    border: 1px solid var(--filet);
    border-radius: 10px;
    overflow: hidden;
    background: var(--papier);
    color: var(--encre);
  }
  .carte.favorable {
    border-color: var(--favorable-pale);
  }
  .carte.defavorable {
    border-color: var(--defavorable-pale);
  }
  .bande {
    flex: 0 0 8.5rem;
    display: flex;
    flex-direction: column;
    justify-content: center;
    gap: 0.3rem;
    padding: 0.9rem 0.75rem;
    background: var(--ardoise);
    color: var(--papier);
  }
  .favorable .bande {
    background: var(--favorable);
  }
  .defavorable .bande {
    background: var(--defavorable);
  }
  .partage .bande {
    background: var(--encre);
  }
  .sens {
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.03em;
    text-transform: uppercase;
  }
  .droit {
    font-family: var(--titre);
    font-size: 1.05rem;
    font-weight: 800;
    font-stretch: 75%;
    line-height: 1.1;
  }
  .corps {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
    padding: 0.85rem 1rem;
  }
  .corps p {
    margin: 0;
    max-width: none;
  }
  .titre {
    margin: 0;
    font-family: var(--texte);
    font-stretch: normal;
    font-size: 1.05rem;
    font-weight: 700;
    line-height: 1.3;
  }
  .titre a {
    text-decoration: none;
  }
  .titre a:hover {
    text-decoration: underline;
  }
  .meta {
    font-size: 0.85rem;
    color: var(--ardoise);
  }
  strong {
    font-weight: 650;
  }
  .groupe {
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    gap: 0.3rem 0.75rem;
    font-size: 0.9rem;
  }
  .ecart {
    display: inline-block;
    font-size: 0.8rem;
    font-weight: 700;
    line-height: 1.3;
    padding: 0 0.4rem;
    border: 1.5px solid var(--encre);
    border-radius: 3px;
  }
  details {
    font-size: 0.85rem;
  }
  summary {
    cursor: pointer;
    font-weight: 650;
    color: var(--ardoise);
  }
  .votes {
    list-style: none;
    padding: 0;
    margin: 0.3rem 0;
  }
  .votes li {
    max-width: none;
    padding: 0.4rem 0;
    border-bottom: 1px solid var(--filet);
  }
  .ligne {
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    gap: 0.1rem 0.9rem;
  }
  .lecture.favorable {
    color: var(--favorable);
    font-weight: 650;
  }
  .lecture.defavorable {
    color: var(--defavorable);
    font-weight: 650;
  }
  @media (max-width: 30rem) {
    .carte {
      flex-direction: column;
    }
    .bande {
      flex: none;
      flex-direction: row;
      flex-wrap: wrap;
      justify-content: flex-start;
      align-items: baseline;
      gap: 0.5rem;
      padding: 0.5rem 0.9rem;
    }
  }
</style>
