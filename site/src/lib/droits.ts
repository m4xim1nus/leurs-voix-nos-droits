// Libellés d'affichage des douze droits de la grille v1 (pipeline/referentiels/droits.yaml).
// La grille fait foi : ces libellés ne font que la dire en langage courant, et un test vérifie
// qu'ils couvrent exactement ses codes.

import type { Sens } from './types';

interface Affichage {
  /** Nom court, pour les listes et les tableaux. */
  court: string;
  /** Complément d'objet : « le texte restreint <objet> ». */
  objet: string;
}

export const DROITS: Record<string, Affichage> = {
  libertes: { court: 'Libertés publiques', objet: 'les libertés publiques' },
  'police-justice': {
    court: 'Police et justice',
    objet: 'les garanties face à la police et à la justice'
  },
  'vie-privee': { court: 'Vie privée', objet: 'la vie privée' },
  etrangers: { court: 'Étrangers et asile', objet: 'les droits des personnes étrangères' },
  discriminations: { court: 'Égalité', objet: 'la protection contre les discriminations' },
  'femmes-lgbti': {
    court: 'Femmes et LGBTI',
    objet: 'les droits des femmes et des personnes LGBTI'
  },
  enfants: { court: 'Enfants', objet: 'les droits de l’enfant' },
  logement: { court: 'Logement', objet: 'le droit au logement' },
  'travail-protection-sociale': {
    court: 'Travail et protection sociale',
    objet: 'les droits au travail et à la protection sociale'
  },
  environnement: { court: 'Environnement', objet: 'le droit à un environnement sain' },
  sante: { court: 'Santé et fin de vie', objet: 'les droits en matière de santé et de fin de vie' },
  citoyennete: { court: 'Droits civiques', objet: 'les droits civiques et politiques' }
};

export const ETIQUETTES: Record<string, string> = {
  'outre-mer': 'Outre-mer',
  'regime-exception': 'Régime d’exception'
};

export const court = (code: string) => DROITS[code]?.court ?? code;

/** « Le texte restreint la vie privée. » */
export const phrase = (code: string, sens: Sens) =>
  `${sens === 'etend' ? 'étend' : 'restreint'} ${DROITS[code]?.objet ?? code}`;
