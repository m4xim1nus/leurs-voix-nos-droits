// Carte partageable d'un groupe, format paysage (lib/server/cartes.ts).
import { carteGroupe, reponsePng, svgCarte } from '$lib/server/cartes';
import { donnees } from '$lib/server/donnees';

export const prerender = true;
export const entries = () => donnees().lignees.map((l) => ({ slug: l.slug }));

export const GET = ({ params }) => reponsePng(svgCarte(carteGroupe(params.slug)));
