// Fiche d'un groupe : l'open data inscrit tous les député·es NI entre l'élection et la formation des groupes.
// Dans NI, on ne liste donc que celles et ceux qui y sont aujourd'hui, ou qui y ont voté.

/** `periodes` : les appartenances de la personne à ce groupe. */
export const membreAffiche = (
  sigle: string,
  periodes: { fin: string | null; a_vote: boolean }[]
): boolean => sigle !== 'NI' || periodes.some((p) => p.fin === null || p.a_vote);

/**
 * Groupe majoritairement abstentionniste sur les scrutins comptés d'un texte : ses abstentions
 * dépassent à la fois ses votes favorables et défavorables (même règle que la position d'un groupe,
 * pipeline/lvnd/positions.py). Son score ne porte alors que sur ses rares votes exprimés.
 */
export const abstentionniste = (s: {
  favorables: number;
  defavorables: number;
  abstentions: number;
}): boolean => s.abstentions > s.favorables && s.abstentions > s.defavorables;

/**
 * Ordre de la règle d'un texte : score décroissant, sans score en dernier ; à score égal, les groupes
 * qui ont voté avant les abstentionnistes.
 */
export function ordreTexte(
  a: {
    score: { score: number | null; favorables: number; defavorables: number; abstentions: number };
  },
  b: {
    score: { score: number | null; favorables: number; defavorables: number; abstentions: number };
  }
): number {
  return (
    (b.score.score ?? -1) - (a.score.score ?? -1) ||
    Number(abstentionniste(a.score)) - Number(abstentionniste(b.score))
  );
}
