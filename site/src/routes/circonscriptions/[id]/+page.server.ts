import { donnees } from '$lib/server/donnees';
import { circos, vueCirco } from '$lib/server/vues';

export const entries = () => [...circos(donnees()).keys()].map((id) => ({ id }));

export const load = ({ params }) => vueCirco(params.id);
