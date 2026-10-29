import { describe, expect, it } from 'vitest';
import { scoreSousAngle, sousAngle } from './droits';

describe('droits', () => {
  const texte = {
    principal: { code: 'libertes', sens: 'restreint' as const },
    droits: [
      { code: 'libertes', sens: 'restreint' as const },
      { code: 'enfants', sens: 'etend' as const }
    ]
  };
  it('lit un texte sous l’angle d’un droit', () => {
    expect(sousAngle(texte, 'enfants')).toEqual({ code: 'enfants', sens: 'etend', inverse: true });
    expect(sousAngle(texte, 'libertes').inverse).toBe(false);
    expect(sousAngle(texte, null)).toEqual({ code: 'libertes', sens: 'restreint', inverse: false });
  });
  it('inverse le score pour un droit de sens contraire', () => {
    expect([
      scoreSousAngle(30, true),
      scoreSousAngle(30, false),
      scoreSousAngle(null, true)
    ]).toEqual([70, 30, null]);
  });
});
