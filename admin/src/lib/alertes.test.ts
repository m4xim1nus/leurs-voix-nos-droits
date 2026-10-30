import { describe, expect, it } from 'vitest';
import { resteATraiter, type Alerte, type TypeAlerte } from './alertes';

const alerte = (type: TypeAlerte, scrutin_id: string | null = null): Alerte => ({
  id: `${type}:D`,
  type,
  dossier_id: 'D',
  scrutin_id,
  date: '2026-11-18',
  titre: 'Titre',
  detail: 'détail'
});

describe('resteATraiter', () => {
  it('texte non traité : une saisie dans D1 suffit, même non publiée', () => {
    for (const t of ['premier_decisif', 'inscrit'] as const) {
      expect(resteATraiter(alerte(t), null, null)).toBe(true);
      expect(resteATraiter(alerte(t), 'brouillon', '{}')).toBe(false);
    }
  });

  it('fiche de suivi : répond à l’inscription, pas au vote qui suit', () => {
    expect(resteATraiter(alerte('inscrit'), 'a-suivre', '{}')).toBe(false);
    expect(resteATraiter(alerte('premier_decisif'), 'a-suivre', '{}')).toBe(true);
  });

  it('vote postérieur : traité quand la qualification retient ce scrutin', () => {
    const a = alerte('vote_posterieur', 'S2');
    expect(resteATraiter(a, 'valide', JSON.stringify({ scrutins: [{ id: 'S1' }] }))).toBe(true);
    expect(resteATraiter(a, 'a-relire', JSON.stringify({ scrutins: [{ id: 'S2' }] }))).toBe(false);
    expect(resteATraiter(a, null, null)).toBe(true);
  });

  it('unanimité contestée : tant que le texte reste écarté', () => {
    const a = alerte('unanimite_contestee', 'S2');
    expect(resteATraiter(a, 'ecarte', '{}')).toBe(true);
    expect(resteATraiter(a, 'brouillon', '{}')).toBe(false);
  });
});
