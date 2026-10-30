// Cohérence des données lues au prérendu (data/export/, data/editorial.json, data/annuaire/).
import { describe, expect, it } from 'vitest';
import { DROITS } from '$lib/droits';
import { mentionNavette } from '$lib/format';
import { donnees } from './donnees';
import { tableCodesPostaux } from './annuaire';
import { situation, vueDepute } from './vues';

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

  it('connaît l’état de chaque texte qualifié ou écarté', () => {
    for (const t of d.textes) expect(t.etat, t.id).not.toBeNull();
    for (const e of d.ecartes) expect(e.etat, e.dossier_an).not.toBeNull();
    expect(d.dateEtat).toMatch(/^\d{4}-\d{2}-\d{2}$/);
  });

  it('nomme une lecture connue pour chaque vote compté d’un texte en navette', () => {
    const navette = d.textes.filter((t) => t.etat?.etat === 'en_navette');
    expect(navette.length).toBeGreaterThan(0);
    for (const t of navette)
      for (const s of t.scrutins.filter((x) => x.compte))
        expect(mentionNavette(t.etat, s.etape), s.id).toMatch(/^vote .*, texte encore en navette$/);
  });

  it('ne met en cours que des textes retenus, chacun avec son échéance', () => {
    expect(d.enCours.length).toBeGreaterThan(0);
    const qualifies = new Set(d.textes.map((t) => t.dossier_an));
    for (const t of d.enCours) {
      // Qualifié en navette, ou fiche de suivi sans sens : jamais les deux, jamais aucun des deux.
      expect(t.qualification === null, t.id).toBe(t.suivi !== null);
      if (t.qualification) {
        expect(qualifies.has(t.dossier_an), t.id).toBe(true);
        expect(t.etat.etat, t.id).toBe('en_navette');
      } else {
        expect(qualifies.has(t.dossier_an), t.id).toBe(false);
      }
      expect(t.echeance === 'inscrit', t.id).toBe(t.etat.seance_inscrite !== null);
      if (t.dernier_vote) expect(t.dernier_vote.ventilations.length, t.id).toBeGreaterThan(0);
    }
  });

  it('ne propose aux députés en cours que les textes attendus à l’Assemblée', () => {
    const attendus = new Set(
      d.enCours
        .filter((t) => t.echeance === 'AN' || t.seances.length > 0 || t.chambre === 'AN')
        .map((t) => t.id)
    );
    const dep = d.deputes.find((x) => situation(x).actuel)!;
    const v = vueDepute(dep.slug);
    expect(v.prochains.map((p) => p.id).sort()).toEqual([...attendus].sort());
    const ancien = d.deputes.find((x) => !situation(x).actuel)!;
    expect(vueDepute(ancien.slug).prochains).toEqual([]);
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
