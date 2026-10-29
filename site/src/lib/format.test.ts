import { describe, expect, it } from 'vitest';
import { date, normaliser, pluriel, pourcent, slug, sensDuPour, typo } from './format';

describe('format', () => {
  it('écrit les scores arrondis, avec espace insécable', () => {
    expect([pourcent(36.9), pourcent(0), pourcent(null)]).toEqual(['37\u202f%', '0\u202f%', '–']);
  });
  it('écrit les dates en toutes lettres', () => {
    expect(date('2025-05-13')).toBe('13 mai 2025');
    expect(date('2024-07-01')).toBe('1er juillet 2024');
    expect(date('2026-02')).toBe('février 2026');
  });
  it('accorde le pluriel', () => {
    expect([pluriel(0, 'texte'), pluriel(1, 'texte'), pluriel(6, 'texte')]).toEqual([
      'aucun texte',
      '1 texte',
      '6 textes'
    ]);
  });
  it('normalise les noms pour la recherche et les slugs', () => {
    expect(normaliser('Éric  CIOTTI')).toBe('eric ciotti');
    expect(slug('Marie-Agnès Poussier-Winsback')).toBe('marie-agnes-poussier-winsback');
    expect(slug('Cœur')).toBe('coeur');
  });
  it('dit ce que signifie voter pour (règle 14)', () => {
    expect(sensDuPour('contre-texte')).toContain('s’opposer');
  });
});

describe('typo', () => {
  it('pose les espaces insécables sans toucher au reste', () => {
    expect(typo('Censure : article 7 ; « VSA » validée ? Oui !')).toBe(
      'Censure : article 7 ; « VSA » validée ? Oui !'
    );
    expect(typo('https://x.fr/a:b')).toBe('https://x.fr/a:b');
  });
});
