// Mise en forme française : nombres, dates, libellés des votes et des droits.

import type { Pour, Position, PositionGroupe, RoleScrutin, Sens } from './types';

const ENTIER = new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 0 });
const DATE = new Intl.DateTimeFormat('fr-FR', {
  day: 'numeric',
  month: 'long',
  year: 'numeric',
  timeZone: 'UTC'
});
const MOIS = new Intl.DateTimeFormat('fr-FR', { month: 'long', year: 'numeric', timeZone: 'UTC' });

export const entier = (n: number) => ENTIER.format(n);

/** Score de 0 à 100, arrondi à l'unité pour l'affichage (le dixième reste dans les données). */
export const pourcent = (n: number | null) => (n === null ? '–' : `${ENTIER.format(n)}\u202f%`);

/** Date ISO (AAAA-MM-JJ, ou AAAA-MM) en toutes lettres. */
export function date(iso: string | null): string {
  if (!iso) return '';
  if (/^\d{4}$/.test(iso)) return iso;
  if (/^\d{4}-\d{2}$/.test(iso)) return MOIS.format(new Date(`${iso}-01T00:00:00Z`));
  return DATE.format(new Date(`${iso.slice(0, 10)}T00:00:00Z`)).replace(/^1 /, '1er ');
}

export const legislature = (n: number) => (n === 16 ? 'XVIe' : n === 17 ? 'XVIIe' : `${n}e`);

/** « 3 textes », « 1 texte », « aucun texte ». */
export function pluriel(n: number, mot: string, pl = `${mot}s`, zero = `aucun ${mot}`): string {
  if (n === 0) return zero;
  return `${entier(n)} ${n > 1 ? pl : mot}`;
}

export const SENS: Record<Sens, string> = { etend: 'étend', restreint: 'restreint' };

export const POSITION: Record<Position | 'absent', string> = {
  pour: 'Pour',
  contre: 'Contre',
  abstention: 'Abstention',
  non_votant: 'Non-votant',
  absent: 'Absent'
};

export const POSITION_GROUPE: Record<PositionGroupe, string> = {
  pour: 'pour',
  contre: 'contre',
  abstention: 'majoritairement abstentionniste',
  partage: 'partagé',
  absent: 'absent'
};

export const ROLE: Record<RoleScrutin, string> = {
  decisif: 'Vote décisif',
  ensemble: 'Autre vote sur l’ensemble',
  motion: 'Motion',
  article: 'Vote sur un article',
  amendement: 'Amendement clé'
};

/** Ce que veut dire « voter pour » sur ce scrutin (règle 14). */
export function sensDuPour(pour: Pour): string {
  if (pour === 'texte') return 'voter pour, c’est soutenir le texte';
  if (pour === 'contre-texte') return 'voter pour, c’est s’opposer au texte';
  return 'sens à trancher, scrutin non compté';
}

/** Députée ou député, selon la civilité publiée par l'AN. */
export const depute = (civ: string, majuscule = false) =>
  (majuscule ? 'D' : 'd') + (civ === 'Mme' ? 'éputée' : 'éputé');

/** « 1re circonscription », « 4e circonscription ». */
export const circonscription = (num: number) => `${num}${num === 1 ? 're' : 'e'} circonscription`;

/** Minuscules sans accents ni ponctuation, pour les slugs et la recherche. */
export function normaliser(s: string): string {
  return s
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .replace(/[œ]/g, 'oe')
    .replace(/[^a-z0-9]+/g, ' ')
    .trim();
}

export const slug = (s: string) => normaliser(s).replace(/ /g, '-');

/** Espaces insécables du français avant « : ; ! ? » et dans les guillemets, pour les textes saisis. */
export function typo(t: string): string {
  return t
    .replace(/(?<=[\p{L}\p{N}»)%’.]) :(?=\s|$)/gu, ' :')
    .replace(/(?<=[\p{L}\p{N}»)’]) ([;!?])(?=\s|$)/gu, ' $1')
    .replace(/« /g, '« ')
    .replace(/ »/g, ' »');
}
