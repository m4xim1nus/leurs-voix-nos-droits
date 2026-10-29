import { donnees } from '$lib/server/donnees';
import { vueGroupe } from '$lib/server/vues';

export const entries = () => donnees().lignees.map((l) => ({ slug: l.slug }));

export const load = ({ params }) => vueGroupe(params.slug);
