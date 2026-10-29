import { vueAccueil } from '$lib/server/vues';

export const load = () => ({ droits: vueAccueil().droits });
