import { describe, expect, it } from 'vitest';
import { termesInterdits } from './publication';

describe('termes interdits', () => {
  const liste = '# commentaire\nABC\nAssociation Exemple\n';
  it('trouve un terme, insensible à la casse, en mot entier', () => {
    expect(termesInterdits('Source : abc, avis', liste)).toEqual(['ABC']);
    expect(termesInterdits('ABCD et xabc ne comptent pas', liste)).toEqual([]);
    expect(termesInterdits("l'association exemple a dit", liste)).toEqual(['Association Exemple']);
    expect(termesInterdits('Éabc', liste)).toEqual([]);
  });
  it('ne bloque rien sans liste', () => {
    expect(termesInterdits('ABC', undefined)).toEqual([]);
  });
});
