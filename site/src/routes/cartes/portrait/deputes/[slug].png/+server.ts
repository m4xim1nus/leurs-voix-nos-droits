// Carte partageable d'un député, format portrait (lib/server/cartes.ts).
import { carteDepute, reponsePng, svgPortrait } from '$lib/server/cartes';
import { donnees } from '$lib/server/donnees';

export const prerender = true;
export const entries = () => donnees().deputes.map((d) => ({ slug: d.slug }));

export const GET = ({ params }) => reponsePng(svgPortrait(carteDepute(params.slug)));
