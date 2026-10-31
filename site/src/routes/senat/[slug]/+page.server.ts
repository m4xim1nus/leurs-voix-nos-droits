import { slugsSenateurs, vueSenateur } from '$lib/server/vues-senat';

export const entries = () => slugsSenateurs();
export const load = ({ params }) => vueSenateur(params.slug);
