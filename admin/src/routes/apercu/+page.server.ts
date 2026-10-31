import type { PageServerLoad } from './$types';
import * as db from '$lib/server/db';
import { qualifSenat, scoresGroupes, scrutinsComptes } from '$lib/scores';

export const load: PageServerLoad = async ({ platform, url }) => {
  const base = platform!.env.DB;
  const brouillons = url.searchParams.get('brouillons') === 'oui';
  const [lignes, groupes, grille] = await Promise.all([
    db.qualifications(base),
    db.groupes(base),
    db.grille(base)
  ]);
  const retenues = lignes.filter(
    (l) => l.statut === 'valide' || (brouillons && ['brouillon', 'a-relire'].includes(l.statut))
  );
  const comptes = scrutinsComptes(retenues.map((l) => l.doc));
  const scrutins = await db.scrutins(
    base,
    comptes.map((c) => c.scrutin_id)
  );
  const lignee = new Map(groupes.map((g) => [g.id, g.lignee]));
  const scores = scoresGroupes(
    comptes,
    new Map(scrutins.map((s) => [s.id, s.positions])),
    (g) => lignee.get(g) ?? g
  );
  // Sénat (règle 26) : à part, chaque groupe sous son sigle, sans lien avec ceux de l'Assemblée.
  const comptesSenat = scrutinsComptes(qualifSenat(retenues.map((l) => l.doc)));
  const scrutinsSenat = await db.scrutinsSenat(
    base,
    comptesSenat.map((c) => c.scrutin_id)
  );
  const scoresSenat = scoresGroupes(
    comptesSenat,
    new Map(scrutinsSenat.map((s) => [s.id, s.positions])),
    (g) => g
  );
  return {
    brouillons,
    scores,
    scoresSenat,
    groupesSenat: await db.groupesSenat(base),
    groupes,
    droits: grille.droits,
    textes: retenues.map((l) => ({ id: l.doc.id, dossier_an: l.dossier_an, statut: l.statut }))
  };
};
