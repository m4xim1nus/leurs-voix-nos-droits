// Lecture des votes d'un·e député·e sur un texte, pour sa fiche. Rien n'est calculé ici qui
// entre dans un score : on ne fait que dire, vote par vote, ce que la règle 14 en fait, et
// regrouper ces lectures pour l'affichage (bande de couleur, filtres).

import type { VoteDepute } from '$lib/server/vues';

export type Lecture = 'favorable' | 'defavorable' | 'hors' | 'non-compte';

/**
 * Lecture d'un vote (règle 14) : pour ou contre, favorable ou défavorable aux droits ; abstention,
 * absence et non-vote hors calcul (règles 16 et 17). `inverse` : texte vu sous l'angle d'un droit
 * de sens contraire à son droit principal (règle 15).
 */
export function lectureVote(v: VoteDepute, inverse: boolean): Lecture {
  if (!v.scrutin.compte) return 'non-compte';
  if (v.position === 'pour' || v.position === 'contre')
    return (v.position === v.scrutin.favorable) !== inverse ? 'favorable' : 'defavorable';
  return 'hors';
}

/**
 * Bilan d'affichage d'un texte, d'après ses votes comptés : tous favorables, tous défavorables,
 * dans les deux sens (`partage`), ou aucun vote pour ou contre (`hors`). Le score du texte, lui,
 * reste celui du pipeline.
 */
export type Bilan = 'favorable' | 'defavorable' | 'partage' | 'hors';

export function bilanTexte(votes: VoteDepute[], inverse: boolean): Bilan {
  const l = new Set(votes.map((v) => lectureVote(v, inverse)));
  if (l.has('favorable')) return l.has('defavorable') ? 'partage' : 'favorable';
  return l.has('defavorable') ? 'defavorable' : 'hors';
}

/** A voté pour quand son groupe votait contre, ou l'inverse. L'abstention n'est pas un écart. */
export function ecartGroupe(v: VoteDepute): boolean {
  const g = v.ventilation?.position;
  return (
    (v.position === 'pour' || v.position === 'contre') &&
    (g === 'pour' || g === 'contre') &&
    g !== v.position
  );
}
