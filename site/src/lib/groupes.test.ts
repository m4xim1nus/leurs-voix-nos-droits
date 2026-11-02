import { describe, expect, it } from 'vitest';
import { abstentionniste, membreAffiche, ordreTexte } from './groupes';

describe('membres affichés sur la fiche d’un groupe', () => {
  const passage = { fin: '2024-07-18', a_vote: false };
  it('retire de NI le simple passage entre l’élection et la formation des groupes', () => {
    expect(membreAffiche('NI', [passage])).toBe(false);
  });
  it('garde dans NI qui y a voté, ou qui y est encore sans avoir voté', () => {
    expect(membreAffiche('NI', [passage, { fin: '2025-01-01', a_vote: true }])).toBe(true);
    expect(membreAffiche('NI', [{ fin: null, a_vote: false }])).toBe(true);
  });
  it('ne change rien aux autres groupes', () => {
    expect(membreAffiche('SOC', [passage])).toBe(true);
  });
});

describe('règle d’un texte : groupes abstentionnistes', () => {
  const g = (
    score: number | null,
    favorables: number,
    defavorables: number,
    abstentions: number
  ) => ({
    score: { score, favorables, defavorables, abstentions }
  });
  it('repère un groupe majoritairement abstentionniste, comme la position d’un groupe', () => {
    expect(abstentionniste(g(0, 0, 1, 79).score)).toBe(true);
    expect(abstentionniste(g(0, 0, 7, 0).score)).toBe(false);
    expect(abstentionniste(g(70, 7, 0, 3).score)).toBe(false);
    expect(abstentionniste(g(50, 5, 5, 5).score)).toBe(false); // égalité : pas majoritaire
  });
  it('range par score ; l’abstention ne départage que deux scores égaux', () => {
    const rn = g(0, 0, 1, 79);
    const dem = g(0, 0, 7, 0);
    const lfi = g(100, 68, 0, 0);
    const uddplr = g(null, 0, 0, 10);
    const hor = g(0, 0, 2, 8);
    const abst100 = g(100, 1, 0, 9);
    const moitie = g(50, 5, 5, 0);
    expect([rn, uddplr, abst100, dem, moitie, hor, lfi].sort(ordreTexte)).toEqual([
      lfi,
      abst100,
      moitie,
      dem,
      rn,
      hor,
      uddplr
    ]);
  });
});
