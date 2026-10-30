import { describe, expect, it } from 'vitest';
import { courrielProchainVote } from './courriel';

describe('courriel des prochains votes', () => {
  const base = {
    titre: 'Proposition de loi X',
    url: 'https://exemple.fr/textes/x',
    feminin: true,
    seances: ['2026-11-18', '2026-11-19']
  };

  it('donne l’inscription, le vote et la position du groupe, puis une question', () => {
    const { sujet, corps } = courrielProchainVote({
      ...base,
      vote: {
        date: '2025-12-11',
        etape: 'AN1',
        position: 'contre',
        groupe: { sigle: 'RN', position: 'contre' }
      }
    });
    expect(sujet).toBe('Votre position sur : Proposition de loi X');
    expect(corps).toContain('Madame la Députée');
    expect(corps).toContain('est inscrit en séance à l’Assemblée les 18 et 19 novembre 2026');
    expect(corps).toContain('le 11 décembre 2025 (vote de 1re lecture) : vous avez voté contre.');
    expect(corps).toContain('Position de votre groupe ce jour-là (RN) : contre.');
    expect(corps).toContain('connaître votre position');
    expect(corps).not.toMatch(/sera voté|votez|nous vous demandons/i);
  });

  it('dit les cas sans vote exprimé', () => {
    const vote = { date: '2025-12-11', etape: 'AN1', groupe: null };
    const c = (position: 'absent' | 'abstention' | null, feminin = true) =>
      courrielProchainVote({ ...base, feminin, vote: { ...vote, position } }).corps;
    expect(c('absent')).toContain('vous n’avez pas pris part à ce vote');
    expect(c('abstention', false)).toContain('vous vous êtes abstenu.');
    expect(c(null)).toContain('vous n’étiez pas encore députée');
  });

  it('dit qu’un texte non inscrit est attendu, sans vote à citer', () => {
    const { corps } = courrielProchainVote({ ...base, seances: [], vote: null });
    expect(corps).toContain('est attendu à l’Assemblée.');
    expect(corps).not.toContain('Dernier vote');
  });
});
