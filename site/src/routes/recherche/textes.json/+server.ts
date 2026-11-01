// Index des textes pour la recherche du site (chargé à la demande par $lib/charge-recherche).
import { json } from '@sveltejs/kit';
import { indexTextes } from '$lib/server/recherche';

export const prerender = true;
export const GET = () => json(indexTextes());
