import { donnees } from '$lib/server/donnees';
import { vueTexte } from '$lib/server/vues';

export const entries = () => [...donnees().textes, ...donnees().seuls].map((t) => ({ id: t.id }));

export const load = ({ params }) => vueTexte(params.id);
