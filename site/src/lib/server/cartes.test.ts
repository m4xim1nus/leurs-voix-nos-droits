import { describe, expect, it } from 'vitest';
import { png, svgCarte } from './cartes';

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
});
