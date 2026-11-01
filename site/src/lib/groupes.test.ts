import { describe, expect, it } from 'vitest';
import { membreAffiche } from './groupes';

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
