// Libellés et mises en forme de l'admin.

import type { Groupe, Statut } from './types';

export const LIBELLES_STATUT: Record<Statut, string> = {
  brouillon: 'brouillon',
  'a-relire': 'à relire',
  valide: 'validé',
  ecarte: 'écarté'
};

export const LIBELLES_ROLE: Record<string, string> = {
  decisif: 'décisif',
  ensemble: 'ensemble (autre lecture)',
  motion: 'motion',
  article: 'article',
  amendement: 'amendement clé'
};

export const LIBELLES_POUR: Record<string, string> = {
  texte: 'voter pour = dans le sens du texte',
  'contre-texte': 'voter pour = contre le texte',
  'a-trancher': 'sens à trancher'
};

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
