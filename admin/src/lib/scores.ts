// Aperçu des scores de groupe, avant publication (docs/METHODO.md, règles 14 à 19).
//
// Même calcul que pipeline/lvnd/scores.py, mais depuis les ventilations officielles (décompte
// pour / contre / abstention de chaque groupe sur chaque scrutin) plutôt que depuis les votes
// nominatifs, que D1 n'a pas : le score d'un groupe agrège les votes de ses membres, ce que la
// ventilation donne directement. scores.test.ts vérifie qu'on retrouve data/export/scores_groupes.csv.

import type { PositionGroupe, Pour, Qualification, RoleDroit, RoleScrutin, Sens } from './types';

export const COMPTES: RoleScrutin[] = ['decisif', 'amendement'];
export const PART_DECISIF = 0.5;

export interface Compte {
  texte_id: string;
  scrutin_id: string;
  role: RoleScrutin;
  droit: string; // code du droit, ou « global » (droit principal de chaque texte)
  droit_role: RoleDroit;
  sens: Sens;
  poids: number;
  favorable: 'pour' | 'contre' | null;
}

/** Position (« pour » / « contre ») favorable aux droits, ou null si le sens du scrutin n'est pas fixé. */
export function favorable(sens: Sens, pour: Pour): 'pour' | 'contre' | null {
  if (pour !== 'texte' && pour !== 'contre-texte') return null;
  const soutien = pour === 'texte' ? 'pour' : 'contre';
  if (sens === 'etend') return soutien;
  return soutien === 'pour' ? 'contre' : 'pour';
}

/** Une ligne par (texte, scrutin compté, droit) : poids et position favorable (règle 18 : chaque texte pèse 1). */
export function scrutinsComptes(textes: Qualification[]): Compte[] {
  const out: Compte[] = [];
  for (const t of textes) {
    const comptes = t.scrutins.filter(
      (s) => COMPTES.includes(s.role) && (s.pour === 'texte' || s.pour === 'contre-texte')
    );
    const decisif = comptes.filter((s) => s.role === 'decisif');
    const amdts = comptes.filter((s) => s.role === 'amendement');
    const principal = t.droits.find((d) => d.role === 'principal');
    for (const s of [...decisif, ...amdts]) {
      const poids =
        s.role === 'decisif'
          ? amdts.length
            ? PART_DECISIF
            : 1
          : (1 - PART_DECISIF) / amdts.length;
      const base = { texte_id: t.id, scrutin_id: s.id, role: s.role, poids };
      for (const d of t.droits)
        out.push({
          ...base,
          droit: d.code,
          droit_role: d.role,
          sens: d.sens,
          favorable: favorable(d.sens, s.pour)
        });
      if (principal)
        out.push({
          ...base,
          droit: 'global',
          droit_role: 'principal',
          sens: principal.sens,
          favorable: favorable(principal.sens, s.pour)
        });
    }
  }
  return out;
}

/**
 * Arrondi au dixième comme `round(x, 1)` en Python : sur la valeur exacte du flottant, égalité
 * au pair. `toFixed` arrondit lui aussi la valeur exacte, mais tranche les égalités vers le haut.
 * Les seules égalités exactes au dixième sont les valeurs en ,25 et ,75 (x × 4 entier impair,
 * multiplication exacte) : on les tranche à part.
 */
export function arrondi(x: number): number {
  const q = x * 4;
  if (Number.isInteger(q) && q % 2 !== 0) {
    const y = Math.floor(x * 10); // 2,25 → 22 ; 2,75 → 27 (exact pour ces valeurs)
    return (y % 2 === 0 ? y : y + 1) / 10;
  }
  return Number(x.toFixed(1));
}

export interface Score {
  lignee: string;
  droit: string;
  n_textes: number;
  votes_favorables: number;
  votes_defavorables: number;
  abstentions: number;
  non_votants: number;
  score: number | null;
}

/**
 * Scores des groupes, réunis par lignée (règle 19). Abstentions et non-votants hors calcul
 * (règles 16 et 17), affichés à côté.
 */
export function scoresGroupes(
  comptes: Compte[],
  positions: Map<string, PositionGroupe[]>,
  lignee: (groupe: string) => string
): Score[] {
  const acc = new Map<
    string,
    {
      num: number;
      den: number;
      textes: Set<string>;
      fav: number;
      def: number;
      abs: number;
      nv: number;
    }
  >();
  for (const c of comptes) {
    if (c.favorable === null) continue;
    for (const [g, pour, contre, abst, nv] of positions.get(c.scrutin_id) ?? []) {
      const cle = `${lignee(g)}\t${c.droit}`;
      let a = acc.get(cle);
      if (!a) {
        a = { num: 0, den: 0, textes: new Set(), fav: 0, def: 0, abs: 0, nv: 0 };
        acc.set(cle, a);
      }
      const [f, d] = c.favorable === 'pour' ? [pour, contre] : [contre, pour];
      a.textes.add(c.texte_id);
      a.num += c.poids * f;
      a.den += c.poids * (f + d);
      a.fav += f;
      a.def += d;
      a.abs += abst;
      a.nv += nv;
    }
  }
  return [...acc.entries()]
    .sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0))
    .map(([cle, a]) => {
      const [lig, droit] = cle.split('\t');
      return {
        lignee: lig,
        droit,
        n_textes: a.textes.size,
        votes_favorables: a.fav,
        votes_defavorables: a.def,
        abstentions: a.abs,
        non_votants: a.nv,
        score: a.den ? arrondi((100 * a.num) / a.den) : null
      };
    });
}
