import { describe, expect, it } from 'vitest';
import { extremes, lignes, png, svgCarte, svgPortrait } from './cartes';

describe('cartes partageables', () => {
  const carte = {
    titre: 'Libertés, Indépendants & <Territoires>',
    sousTitre: 'Groupe LIOT',
    score: 33.6,
    nTextes: 3,
    reperes: [{ libelle: 'LIOT', couleur: '#FFD96F', score: 33.6 }],
    chemin: '/groupes/liot-17'
  };

  it('échappe le texte et écrit le score arrondi', () => {
    const svg = svgCarte(carte);
    expect(svg).toContain('Indépendants &amp; &lt;Territoires&gt;');
    expect(svg).toContain('>34 %<');
  });

  it('rend un PNG de 1200 × 630', () => {
    const p = png(svgCarte(carte));
    expect([...p.slice(1, 4)].map((c) => String.fromCharCode(c)).join('')).toBe('PNG');
    const vue = new DataView(p.buffer, p.byteOffset);
    expect([vue.getUint32(16), vue.getUint32(20)]).toEqual([1200, 630]);
  });

  it('retient les droits extrêmes, sauf égalité', () => {
    const e = extremes([
      { libelle: 'Vie privée', score: 10 },
      { libelle: 'Logement', score: null },
      { libelle: 'Égalité', score: 90 }
    ]);
    expect([e?.haut.libelle, e?.bas.libelle]).toEqual(['Égalité', 'Vie privée']);
    expect(
      extremes([
        { libelle: 'A', score: 0 },
        { libelle: 'B', score: 0 }
      ])
    ).toBeNull();
    expect(svgCarte({ ...carte, extremes: e })).toContain('Le plus favorable');
  });

  it('coupe les titres longs et rend le format portrait en 1080 × 1350', () => {
    expect(lignes('Libertés, Indépendants, Outre-mer et Territoires', 20)).toEqual([
      'Libertés,',
      'Indépendants,',
      'Outre-mer et',
      'Territoires'
    ]);
    const p = png(svgPortrait(carte));
    const vue = new DataView(p.buffer, p.byteOffset);
    expect([vue.getUint32(16), vue.getUint32(20)]).toEqual([1080, 1350]);
  });
});
