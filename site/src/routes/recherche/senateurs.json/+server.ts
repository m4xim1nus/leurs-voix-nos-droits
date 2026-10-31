// Index des sénateur·ices pour la recherche (chargé à la demande).
import { json } from '@sveltejs/kit';
import { indexSenateurs } from '$lib/server/vues-senat';

export const prerender = true;
export const GET = () => json(indexSenateurs());
