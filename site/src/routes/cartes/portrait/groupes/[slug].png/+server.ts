// Carte partageable d'un groupe, format portrait (lib/server/cartes.ts).
import { carteGroupe, reponsePng, svgPortrait } from '$lib/server/cartes';
import { donnees } from '$lib/server/donnees';

export const prerender = true;
export const entries = () => donnees().lignees.map((l) => ({ slug: l.slug }));

export const GET = ({ params }) => reponsePng(svgPortrait(carteGroupe(params.slug)));
