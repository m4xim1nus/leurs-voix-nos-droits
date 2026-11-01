// Données de la page Comparer du Sénat, chargées à la demande : mêmes tableaux que celle de l'Assemblée
// (règle 28 : aucune entité d'une autre chambre). Chaque groupe est lu sur une période (règle 26).
import { json } from '@sveltejs/kit';
import { ancreGroupe } from '$lib/comparer';
import { etatEnListe } from '$lib/format';
import { donnees } from '$lib/server/donnees';
import { baseSenat } from '$lib/server/senat';
import { indexSenateurs, PERIODES, periodeDu } from '$lib/server/vues-senat';
import type { Score } from '$lib/types';

export const prerender = true;

export const GET = () => {
  const d = donnees();
  const b = baseSenat();
  const droits = d.droits.map((x) => x.code);
  const comptes = [...d.textes, ...d.seuls].filter((t) => t.senat?.decisif);
  const textes = comptes.map((t) => t.id);
  const valeurs = (s: Map<string, Score> | undefined, cles: string[]) =>
    cles.map((c) => s?.get(c)?.score ?? null);
  const groupes = PERIODES.flatMap((p) =>
    b.groupes
      .filter((g) => b.scoresGroupes.get(p.id)?.has(g.id))
      .map((g) => {
        const scores = b.scoresGroupes.get(p.id)!.get(g.id)!;
        const parTexte = b.scoresGroupesTextes.get(g.id);
        return {
          cle: `g:${g.id}:${p.id}`,
          nom: `Groupe ${g.sigle}, ${p.court}`,
          sigle: g.sigle,
          couleur: g.couleur,
          legislature: p.id,
          lien: `/senat#${ancreGroupe(g.id, p.id)}`,
          global: scores.get('global')?.score ?? null,
          droits: valeurs(scores, droits),
          textes: comptes.map((t) =>
            periodeDu(t.senat!.decisif!.date).id === p.id
              ? (parTexte?.get(t.id)?.score ?? null)
              : null
          )
        };
      })
  );
  const index = new Map(indexSenateurs().map((e) => [e.slug, e]));
  const senateurs = b.senateurs
    .filter((s) => b.scoresSenateurs.has(s.id))
    .map((s) => {
      const e = index.get(s.slug)!;
      const periodes = b.scoresSenateursPeriodes.get(s.id);
      return {
        cle: `s:${s.slug}`,
        nom: e.nom,
        sigle: e.sigle,
        couleur: e.couleur,
        lien: `/senat/${s.slug}`,
        global: b.scoresSenateurs.get(s.id)!.get('global')?.score ?? null,
        droits: valeurs(b.scoresSenateurs.get(s.id), droits),
        legislatures: Object.fromEntries(
          [...(periodes ?? [])].map(([p, scores]) => [
            p,
            { global: scores.get('global')?.score ?? null, droits: valeurs(scores, droits) }
          ])
        ),
        textes: valeurs(b.scoresSenateursTextes.get(s.id), textes)
      };
    })
    .sort((x, y) => x.nom.localeCompare(y.nom, 'fr'));
  return json({
    droits: d.droits.map((x) => ({ code: x.code, court: x.court })),
    textes: comptes.map((t) => ({
      id: t.id,
      titre: t.titre,
      etat: etatEnListe(t.etat, t.scrutins.find((s) => s.role === 'decisif')?.etape ?? null)
    })),
    entites: [...groupes, ...senateurs]
  });
};
