// Pays → circonscription des Français établis hors de France (chargé à la demande par $lib/charge-recherche).
import { json } from '@sveltejs/kit';
import { indexPays } from '$lib/server/recherche';

export const prerender = true;
export const GET = () => json(indexPays());
