import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { aFaire, etapes } from './etapes';
import { normaliser, valider } from './qualification';
import type { Editorial, Grille, Qualification } from './types';

const RACINE = new URL('../../../', import.meta.url);
const editorial: Editorial = JSON.parse(
  readFileSync(new URL('data/editorial.json', RACINE), 'utf8')
);

const GRILLE: Grille = {
  version: 1,
  droits: [
    { code: 'vie-privee', libelle: 'Vie privée et surveillance' },
    { code: 'libertes', libelle: 'Libertés publiques : expression, conscience' }
  ],
  etiquettes: [],
  sens: []
};

const vide = (): Qualification =>
  normaliser({ id: 'x', titre: 'Titre', droits: [], scrutins: [], sources: {} });

describe('étapes de la fiche', () => {
  it('une fiche vide liste ce qui manque, en clair', () => {
    const e = etapes(vide(), GRILLE, 'brouillon', '');
    expect(e.map((x) => x.titre)).toEqual([
      'Le texte',
      'Droits touchés',
      'Sources',
      'Le vote qui compte'
    ]);
    expect(aFaire(e[0])).toBe(0);
    expect(e[1].points[0]).toEqual({ ok: false, texte: 'Ajouter au moins un droit touché' });
    expect(aFaire(e[3])).toBe(1);
  });

  it('nomme le droit sans source par son libellé court', () => {
    const t = vide();
    t.droits = [
      { code: 'libertes', role: 'principal', sens: 'restreint', sources: [], justification: '' }
    ];
    const sources = etapes(t, GRILLE, 'brouillon', '')[2];
    expect(sources.points).toEqual([
      { ok: false, texte: 'Citer une source pour « Libertés publiques »' }
    ]);
  });

  it('compte les droits principaux en trop', () => {
    const t = vide();
    const d = { sens: 'etend' as const, sources: ['a'], justification: '' };
    t.droits = [
      { ...d, code: 'libertes', role: 'principal' },
      { ...d, code: 'vie-privee', role: 'principal' }
    ];
    expect(etapes(t, GRILLE, 'brouillon', '')[1].points).toContainEqual({
      ok: false,
      texte: 'Garder un seul droit principal (2 aujourd’hui)'
    });
  });

  it('fiche de suivi : pas d’étape de vote ; écarté : le motif seul', () => {
    expect(etapes(vide(), GRILLE, 'a-suivre', '')).toHaveLength(3);
    const e = etapes(vide(), GRILLE, 'ecarte', '');
    expect(e).toHaveLength(1);
    expect(aFaire(e[0])).toBe(1);
    expect(aFaire(etapes(vide(), GRILLE, 'ecarte', 'hors sujet')[0])).toBe(0);
  });

  it('chaque texte publié sans erreur a toutes ses étapes cochées', () => {
    // Les codes utilisés par les textes publiés tiennent lieu de grille.
    const codes = new Set(editorial.textes.flatMap((t) => t.droits.map((d) => d.code)));
    const etiq = new Set(editorial.textes.flatMap((t) => t.etiquettes ?? []));
    const grille: Grille = {
      version: 1,
      droits: [...codes].map((code) => ({ code, libelle: code })),
      etiquettes: [...etiq].map((code) => ({ code, libelle: code })),
      sens: []
    };
    let vus = 0;
    for (const t of editorial.textes) {
      if (valider(t, grille).erreurs.length) continue;
      vus++;
      const restant = etapes(t, grille, 'valide', '').flatMap((e) =>
        e.points.filter((p) => !p.ok).map((p) => `${t.id} : ${p.texte}`)
      );
      expect(restant).toEqual([]);
    }
    expect(vus).toBeGreaterThan(100);
  });
});
