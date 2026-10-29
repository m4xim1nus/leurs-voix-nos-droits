// Données de la page Comparer, chargées à la demande : scores de chaque député et de chaque groupe,
// global, par droit et par texte, en tableaux alignés sur `droits` et `textes` (null : pas de score).
import { json } from '@sveltejs/kit';
import { donnees } from '$lib/server/donnees';
import { entree } from '$lib/server/vues';
import type { Score } from '$lib/types';

export const prerender = true;

export const GET = () => {
  const d = donnees();
  const droits = d.droits.map((x) => x.code);
  const textes = d.textes.map((t) => t.id);
  const valeurs = (s: Map<string, Score> | undefined, cles: string[]) =>
    cles.map((c) => s?.get(c)?.score ?? null);
  const groupes = d.lignees
    .filter((l) => d.scoresGroupes.has(l.id))
    .map((l) => ({
      cle: `g:${l.slug}`,
      nom: `Groupe ${l.sigle}, ${l.legislature === 17 ? 'XVIIe' : 'XVIe'}`,
      sigle: l.sigle,
      couleur: l.couleur,
      lien: `/groupes/${l.slug}`,
      global: d.scoresGroupes.get(l.id)!.get('global')?.score ?? null,
      droits: valeurs(d.scoresGroupes.get(l.id), droits),
      textes: valeurs(d.scoresGroupesTextes.get(l.id), textes)
    }));
  const deputes = d.deputes
    .filter((dep) => d.scoresDeputes.has(dep.id))
    .map((dep) => {
      const e = entree(d, dep);
      return {
        cle: `d:${dep.slug}`,
        nom: e.nom,
        sigle: e.sigle,
        couleur: e.couleur,
        lien: `/deputes/${dep.slug}`,
        global: d.scoresDeputes.get(dep.id)!.get('global')?.score ?? null,
        droits: valeurs(d.scoresDeputes.get(dep.id), droits),
        textes: valeurs(d.scoresDeputesTextes.get(dep.id), textes)
      };
    })
    .sort((a, b) => a.nom.localeCompare(b.nom, 'fr'));
  return json({
    droits: d.droits.map((x) => ({ code: x.code, court: x.court })),
    textes: d.textes.map((t) => ({ id: t.id, titre: t.titre })),
    entites: [...groupes, ...deputes]
  });
};
