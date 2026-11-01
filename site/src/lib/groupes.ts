// Fiche d'un groupe : l'open data inscrit tous les député·es NI entre l'élection et la formation des groupes.
// Dans NI, on ne liste donc que celles et ceux qui y sont aujourd'hui, ou qui y ont voté.

/** `periodes` : les appartenances de la personne à ce groupe. */
export const membreAffiche = (
  sigle: string,
  periodes: { fin: string | null; a_vote: boolean }[]
): boolean => sigle !== 'NI' || periodes.some((p) => p.fin === null || p.a_vote);
