import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { arrondi, favorable, scoresGroupes, scrutinsComptes } from './scores';
import type { Editorial, PositionGroupe, Qualification } from './types';

const RACINE = new URL('../../../', import.meta.url);
const lire = (chemin: string) => readFileSync(new URL(chemin, RACINE), 'utf8');

function csv(chemin: string): Record<string, string>[] {
  const [entete, ...lignes] = lire(chemin).trimEnd().split('\n');
  const cols = entete.split(',');
  // aucun champ de ces fichiers ne contient de virgule
  return lignes.map((l) => Object.fromEntries(l.split(',').map((v, i) => [cols[i], v])));
}

const T: Qualification = {
  id: 't',
  dossier_an: 'D',
  legislature: 17,
  titre: 'T',
  resume: '',
  droits: [
    { code: 'etrangers', role: 'principal', sens: 'restreint', sources: [], justification: '' },
    { code: 'enfants', role: 'secondaire', sens: 'etend', sources: [], justification: '' }
  ],
  etiquettes: [],
  vigilance: [],
  conseil_constitutionnel: '',
  note: '',
  sources: {},
  scrutins: [
    { id: 'D', role: 'decisif', pour: 'texte', objet: '' },
    { id: 'A1', role: 'amendement', pour: 'contre-texte', objet: '' },
    { id: 'A2', role: 'amendement', pour: 'contre-texte', objet: '' },
    { id: 'M', role: 'motion', pour: 'contre-texte', objet: '' },
    { id: 'X', role: 'amendement', pour: 'a-trancher', objet: '' }
  ]
};

describe('scores', () => {
  it('donne le sens favorable', () => {
    expect(favorable('restreint', 'texte')).toBe('contre');
    expect(favorable('restreint', 'contre-texte')).toBe('pour');
    expect(favorable('etend', 'texte')).toBe('pour');
    expect(favorable('etend', 'a-trancher')).toBeNull();
  });

  it('ne compte ni les motions ni les sens à trancher, et pondère par texte', () => {
    const c = scrutinsComptes([T]);
    expect(new Set(c.map((x) => x.scrutin_id))).toEqual(new Set(['D', 'A1', 'A2']));
    const g = (s: string) => c.find((x) => x.scrutin_id === s && x.droit === 'global')!.poids;
    expect(g('D')).toBe(0.5);
    expect(g('A1')).toBe(0.25);
  });

  it('agrège les ventilations par lignée, abstention hors calcul', () => {
    const pos = new Map<string, PositionGroupe[]>([
      ['D', [['G1', 0, 10, 5, 1, 'contre', 0.62]]],
      ['A1', [['G2', 4, 0, 0, 0, 'pour', 1]]]
    ]);
    const s = scoresGroupes(scrutinsComptes([T]), pos, () => 'L');
    const glob = s.find((x) => x.droit === 'global')!;
    expect(glob).toMatchObject({
      lignee: 'L',
      votes_favorables: 14,
      abstentions: 5,
      non_votants: 1
    });
    expect(glob.score).toBe(100);
  });

  it('arrondit comme Python', () => {
    // round(2.25, 1) == 2.2 ; round(2.35, 1) == 2.4 (2.35 vaut en fait 2.35000000000000008…)
    expect([arrondi(2.25), arrondi(2.75), arrondi(2.35), arrondi(66.66666), arrondi(0.05)]).toEqual(
      [2.2, 2.8, 2.4, 66.7, 0.1]
    );
  });

  it('redonne data/export/scores_groupes.csv (pipeline, votes nominatifs)', () => {
    const editorial: Editorial = JSON.parse(lire('data/editorial.json'));
    const lignee = new Map(csv('data/export/groupes.csv').map((g) => [g.id, g.lignee]));
    const comptes = scrutinsComptes(editorial.textes);
    const utiles = new Set(comptes.map((c) => c.scrutin_id));
    const pos = new Map<string, PositionGroupe[]>();
    for (const p of csv('data/export/positions_groupes.csv')) {
      if (!utiles.has(p.scrutin_id)) continue;
      const n = [p.pour, p.contre, p.abstention, p.non_votants].map(Number);
      if (!n.some(Boolean)) continue;
      if (!pos.has(p.scrutin_id)) pos.set(p.scrutin_id, []);
      pos.get(p.scrutin_id)!.push([p.groupe_id, n[0], n[1], n[2], n[3], p.position, null]);
    }
    const obtenu = scoresGroupes(comptes, pos, (g) => lignee.get(g) ?? g);
    const attendu = csv('data/export/scores_groupes.csv');
    expect(obtenu.length).toBe(attendu.length);
    for (const a of attendu) {
      const o = obtenu.find((x) => x.lignee === a.lignee && x.droit === a.droit)!;
      expect(o, `${a.lignee} ${a.droit}`).toBeDefined();
      expect([
        o.n_textes,
        o.votes_favorables,
        o.votes_defavorables,
        o.abstentions,
        o.non_votants
      ]).toEqual(
        [a.n_textes, a.votes_favorables, a.votes_defavorables, a.abstentions, a.non_votants].map(
          Number
        )
      );
      if (a.score === '') expect(o.score).toBeNull();
      else expect(o.score, `${a.lignee} ${a.droit}`).toBe(Number(a.score));
    }
  });
});
