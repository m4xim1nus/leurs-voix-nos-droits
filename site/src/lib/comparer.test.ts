import { describe, expect, it } from 'vitest';
import { faceA, legislatureCommune, type Entite } from './comparer';

const base = { nom: '', sigle: '', couleur: '', lien: '', textes: [] };
const depute: Entite = {
  ...base,
  cle: 'd:x',
  global: 50,
  droits: [50, null],
  legislatures: {
    15: { global: 100, droits: [100, null] },
    17: { global: 0, droits: [0, null] }
  }
};
const groupe = (legislature: number): Entite => ({
  ...base,
  cle: `g:${legislature}`,
  global: 70,
  droits: [70, 60],
  legislature
});

describe('comparaison député·e et groupe (règle 19)', () => {
  it('lit le député sur la législature du groupe, dans les deux sens', () => {
    expect(legislatureCommune(depute, groupe(17))).toBe(17);
    expect(legislatureCommune(groupe(15), depute)).toBe(15);
    expect(faceA(depute, groupe(17))).toMatchObject({ global: 0, droits: [0, null] });
    expect(faceA(depute, groupe(15))).toMatchObject({ global: 100, droits: [100, null] });
  });

  it('ne donne aucun score sur une législature où il n’a pas voté', () => {
    expect(faceA(depute, groupe(16))).toMatchObject({ global: null, droits: [null, null] });
  });

  it('ne change rien au groupe, ni à deux député·es, ni à deux groupes', () => {
    const g = groupe(17);
    expect(faceA(g, depute)).toBe(g);
    expect(legislatureCommune(depute, depute)).toBeNull();
    expect(legislatureCommune(g, groupe(15))).toBeNull();
    expect(faceA(depute, depute)).toBe(depute);
  });
});
