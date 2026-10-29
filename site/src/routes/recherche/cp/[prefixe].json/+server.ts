// Table des codes postaux d'un préfixe à deux chiffres (chargée à la demande par Recherche.svelte).
import { error, json } from '@sveltejs/kit';
import { prefixes, tableCodesPostaux } from '$lib/server/annuaire';

export const prerender = true;
export const entries = () => prefixes().map((prefixe) => ({ prefixe }));

export const GET = ({ params }) => {
  const t = tableCodesPostaux(params.prefixe);
  if (!t) error(404, 'Préfixe inconnu');
  return json(t);
};
