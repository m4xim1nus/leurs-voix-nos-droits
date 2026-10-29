import { donnees } from '$lib/server/donnees';
import { vueDroit } from '$lib/server/vues';

export const entries = () => donnees().droits.map((d) => ({ code: d.code }));

export const load = ({ params }) => vueDroit(params.code);
