// Carte partageable d'un·e sénateur·ice, format paysage (lib/server/cartes.ts). Sans vote compté, pas de carte.
import { carteSenateur, reponsePng, svgCarte } from '$lib/server/cartes';
import { baseSenat } from '$lib/server/senat';

export const prerender = true;
export const entries = () => {
  const b = baseSenat();
  return b.senateurs.filter((s) => b.scoresSenateurs.has(s.id)).map((s) => ({ slug: s.slug }));
};

export const GET = ({ params }) => reponsePng(svgCarte(carteSenateur(params.slug)));
