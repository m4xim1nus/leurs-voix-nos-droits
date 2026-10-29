// Carte partageable d'un député, format paysage (lib/server/cartes.ts).
import { carteDepute, reponsePng, svgCarte } from '$lib/server/cartes';
import { donnees } from '$lib/server/donnees';

export const prerender = true;
export const entries = () => donnees().deputes.map((d) => ({ slug: d.slug }));

export const GET = ({ params }) => reponsePng(svgCarte(carteDepute(params.slug)));
