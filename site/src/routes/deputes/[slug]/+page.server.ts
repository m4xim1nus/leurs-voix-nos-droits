import { donnees } from '$lib/server/donnees';
import { vueDepute } from '$lib/server/vues';

export const entries = () => donnees().deputes.map((d) => ({ slug: d.slug }));

export const load = ({ params }) => vueDepute(params.slug);
