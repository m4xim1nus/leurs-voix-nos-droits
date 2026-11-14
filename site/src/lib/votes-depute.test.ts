import { describe, expect, it } from 'vitest';
import type { VoteDepute } from '$lib/server/vues';
import { bilanTexte, ecartGroupe, lectureVote } from './votes-depute';

const vote = (
  position: VoteDepute['position'],
  favorable: 'pour' | 'contre' = 'pour',
  groupe: 'pour' | 'contre' | 'abstention' | null = null,
  compte = true
): VoteDepute => ({
  scrutin: {
    id: `S${Math.random()}`,
    role: 'decisif',
    objet: 'ensemble',
    date: '2026-01-01',
    etape: 'AN1',
    url: '',
    compte,
    favorable
  },
  position,
  groupe: null,
  ventilation: groupe ? { position: groupe, cohesion: 1 } : null
});

describe('votes d’un·e député·e', () => {
  it('lit chaque vote selon la règle 14, et l’inverse sous l’angle d’un droit contraire', () => {
    expect(lectureVote(vote('pour'), false)).toBe('favorable');
    expect(lectureVote(vote('pour', 'contre'), false)).toBe('defavorable');
    expect(lectureVote(vote('pour'), true)).toBe('defavorable');
    expect(lectureVote(vote('contre', 'contre'), false)).toBe('favorable');
  });
  it('ne compte jamais une abstention, une absence ou un non-vote', () => {
    for (const p of ['abstention', 'non_votant', 'absent'] as const)
      expect(lectureVote(vote(p), false)).toBe('hors');
    expect(lectureVote(vote('pour', 'pour', null, false), false)).toBe('non-compte');
  });
  it('fait le bilan d’un texte', () => {
    expect(bilanTexte([vote('pour'), vote('absent')], false)).toBe('favorable');
    expect(bilanTexte([vote('contre'), vote('abstention')], false)).toBe('defavorable');
    expect(bilanTexte([vote('pour'), vote('contre')], false)).toBe('partage');
    expect(bilanTexte([vote('abstention'), vote('absent')], false)).toBe('hors');
    expect(bilanTexte([vote('pour')], true)).toBe('defavorable');
  });
  it('signale un écart avec le groupe, pas une abstention', () => {
    expect(ecartGroupe(vote('pour', 'pour', 'contre'))).toBe(true);
    expect(ecartGroupe(vote('pour', 'pour', 'pour'))).toBe(false);
    expect(ecartGroupe(vote('abstention', 'pour', 'contre'))).toBe(false);
    expect(ecartGroupe(vote('contre', 'pour', 'abstention'))).toBe(false);
    expect(ecartGroupe(vote('contre'))).toBe(false);
  });
});
