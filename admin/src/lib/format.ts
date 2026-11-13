// Libellés et mises en forme de l'admin.

import type { Groupe, Statut } from './types';

export const LIBELLES_STATUT: Record<Statut, string> = {
  brouillon: 'brouillon',
  'a-relire': 'à relire',
  valide: 'validé',
  ecarte: 'écarté',
  'a-suivre': 'à suivre'
};

export const LIBELLES_ROLE: Record<string, string> = {
  decisif: 'décisif : le vote qui compte',
  ensemble: 'ensemble (autre lecture)',
  motion: 'motion',
  article: 'article',
  amendement: 'amendement clé',
  censure: 'motion de censure (49.3)'
};

export const LIBELLES_ROLE_SENAT: Record<string, string> = {
  decisif: 'décisif du Sénat',
  ensemble: 'ensemble, affiché',
  motion: 'motion, affichée'
};

export const LIBELLES_VERSION_SENAT: Record<string, string> = {
  meme: 'même texte que le décisif de l’Assemblée (sens repris)',
  autre: 'autre version (sens relu et sourcé, ou vote affiché)',
  seul: 'pas de décisif à l’Assemblée (droits du texte)'
};

export const LIBELLES_POUR: Record<string, string> = {
  texte: 'voter « pour », c’est soutenir le texte',
  'contre-texte': 'voter « pour », c’est s’opposer au texte',
  'a-trancher': 'sens à trancher (vote non compté)'
};

/** Nature d'un scrutin, en clair (colonne `objet` du catalogue AN et Sénat). */
export const LIBELLES_OBJET: Record<string, string> = {
  ensemble: 'vote sur l’ensemble du texte',
  article_unique: 'vote sur l’article unique',
  suppression_article_unique: 'suppression de l’article unique',
  article: 'vote sur un article',
  amendement: 'amendement',
  partie: 'vote sur une partie du texte',
  motion_rejet: 'motion de rejet',
  motion_renvoi: 'motion de renvoi en commission',
  motion_censure: 'motion de censure',
  motion_autre: 'motion',
  question_prealable: 'question préalable',
  resolution: 'résolution',
  declaration: 'déclaration du Gouvernement',
  autre: 'autre vote'
};

export const libelleObjet = (o: string | null | undefined): string =>
  o ? (LIBELLES_OBJET[o] ?? o.replaceAll('_', ' ')) : '';

/** Début d'un libellé de la grille, avant le deux-points : « Libertés publiques ». */
export const libelleCourt = (l: string): string => l.split(' : ')[0].trim();

export const LIBELLES_ETAPE: Record<string, string> = {
  AN1: '1re lecture',
  AN2: '2e lecture',
  AN21: 'lecture unique',
  ANLUNI: 'lecture unique',
  ANNLEC: 'nouvelle lecture',
  ANLDEF: 'lecture définitive',
  CMP: 'CMP'
};

export const LIBELLES_POSITION: Record<string, string> = {
  pour: 'pour',
  contre: 'contre',
  abstention: 'abst.',
  partage: 'partagé',
  absent: 'absent'
};

export function date(iso: string | null | undefined): string {
  if (!iso) return '';
  const [a, m, j] = iso.slice(0, 10).split('-');
  return `${j}/${m}/${a}`;
}

export function dateHeure(iso: string | null | undefined): string {
  if (!iso) return '';
  return `${date(iso)} ${iso.slice(11, 16)}`;
}

export function pourcent(x: number | null | undefined): string {
  return x == null ? '' : `${Math.round(100 * x)} %`;
}

export function chiffres(x: number | null | undefined): string {
  return x == null ? '' : x.toLocaleString('fr-FR').replace(/ /g, ' ');
}

/** Couleur lisible pour la pastille d'un groupe (couleur officielle AN, ou gris). */
export function couleur(g: Groupe | undefined): string {
  return g?.couleur || '#8d949a';
}

export function legislature(n: number): string {
  return `${['', 'XV', 'XVI', 'XVII'][n - 14] ?? n}e`;
}
