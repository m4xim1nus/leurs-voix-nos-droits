// Index des noms pour la recherche (chargé à la demande par Recherche.svelte).
import { json } from '@sveltejs/kit';
import { indexDeputes } from '$lib/server/vues';

export const prerender = true;
export const GET = () => json(indexDeputes());
