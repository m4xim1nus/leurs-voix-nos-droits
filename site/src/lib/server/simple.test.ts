import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { empreinteSimple, phrasesSimples } from './simple';

// Même fixture que le pipeline et l'admin : mêmes empreintes.
const f = JSON.parse(
  readFileSync(
    new URL('../../../../pipeline/tests/fixtures/editorial_simple.json', import.meta.url),
    'utf8'
  )
);

describe('résumé simple', () => {
  it('calcule les mêmes empreintes que le pipeline', () => {
    for (const x of f.empreintes) {
      const t = { conseil_constitutionnel: '', resume: '', ...x.doc };
      t.conseil_constitutionnel = t.conseil_constitutionnel.replace(/[ \t\n\r]+/g, ' ').trim();
      t.resume = t.resume.trim();
      expect(empreinteSimple(t)).toBe(x.empreinte);
    }
  });

  it('n’affiche qu’un résumé simple à jour', () => {
    const doc = JSON.parse(f.sortie).textes[0];
    expect(phrasesSimples(doc)).toEqual([
      'Cette loi crée un seul guichet.',
      'On y fait ses démarches.'
    ]);
    expect(phrasesSimples({ ...doc, resume: 'Autre.' })).toBeNull();
    expect(phrasesSimples({ ...doc, resume_simple: undefined })).toBeNull();
  });
});
