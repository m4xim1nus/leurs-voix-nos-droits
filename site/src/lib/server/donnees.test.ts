// Cohérence des données lues au prérendu (data/export/, data/editorial.json, data/annuaire/).
import { describe, expect, it } from 'vitest';
import { DROITS } from '$lib/droits';
import { donnees } from './donnees';
import { tableCodesPostaux } from './annuaire';
import { vueDepute } from './vues';

describe('données du site', () => {
  const d = donnees();

  it('a un libellé d’affichage pour chaque droit de la grille, et rien de plus', () => {
    expect(Object.keys(DROITS).sort()).toEqual(d.droits.map((x) => x.code).sort());
  });

  it('retrouve chaque scrutin retenu et un seul décisif par texte (aucun après un 49.3)', () => {
    for (const t of d.textes) {
      const par493 = t.scrutins.some((s) => s.role === 'censure');
      expect(
        t.scrutins.filter((s) => s.role === 'decisif'),
        t.id
      ).toHaveLength(par493 ? 0 : 1);
      for (const s of t.scrutins) expect(s.numero, s.id).toBeGreaterThan(0);
    }
  });

  it('donne des slugs de députés uniques', () => {
    const slugs = d.deputes.map((x) => x.slug);
    expect(new Set(slugs).size).toBe(slugs.length);
  });

  it('relie un code postal à son député', () => {
    const t = tableCodesPostaux('33')!;
    expect(t.codes['33000'].length).toBeGreaterThan(0);
    const circo = t.codes['33000'][0].circo;
    expect(circo).toMatch(/^33-\d\d$/);
    expect(t.circos[circo].libelle).toContain('Gironde');
  });

  it('lit les votes d’un député comme les scores publiés', () => {
    // Le nombre de votes favorables affiché sur la fiche redonne celui de scores_deputes.csv.
    for (const dep of d.deputes.slice(0, 200)) {
      const v = vueDepute(dep.slug);
      if (!v.global) continue;
      const fav = v.textes
        .flatMap((t) => t.votes)
        .filter((x) => x.scrutin.compte && x.position === x.scrutin.favorable).length;
      expect(fav, dep.slug).toBe(v.global.favorables);
    }
  });
});
