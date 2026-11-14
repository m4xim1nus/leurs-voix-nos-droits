import { vueSenat } from '$lib/server/vues-senat';

export const load = () => ({ departements: vueSenat().departements });
