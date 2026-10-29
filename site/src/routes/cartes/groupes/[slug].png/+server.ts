// Carte partageable d'un groupe (lib/server/cartes.ts).
import { legislature } from '$lib/format';
import { extremes, png, svgCarte } from '$lib/server/cartes';
import { donnees } from '$lib/server/donnees';
import { vueGroupe } from '$lib/server/vues';

export const prerender = true;
export const entries = () => donnees().lignees.map((l) => ({ slug: l.slug }));

export const GET = ({ params }) => {
  const v = vueGroupe(params.slug);
  const g = v.groupe;
  const svg = svgCarte({
    titre: g.nom,
    sousTitre: `Groupe ${g.sigle}, ${legislature(g.legislature)} législature`,
    score: v.global?.score ?? null,
    nTextes: v.global?.n_textes ?? 0,
    extremes: extremes(v.droits.map((x) => ({ libelle: x.droit.court, score: x.score.score }))),
    reperes:
      v.global?.score != null
        ? [{ libelle: g.sigle, couleur: g.couleur, score: v.global.score }]
        : [],
    chemin: `/groupes/${g.slug}`
  });
  return new Response(Buffer.from(png(svg)), { headers: { 'content-type': 'image/png' } });
};
