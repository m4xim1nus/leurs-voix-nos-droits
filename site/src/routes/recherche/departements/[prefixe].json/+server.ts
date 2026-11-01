// Code postal → départements d'un préfixe à deux chiffres (sénateur·ices d'un code postal, dans la recherche).
import { error, json } from '@sveltejs/kit';
import { prefixesDepartements, tableDepartements } from '$lib/server/vues-senat';

export const prerender = true;
export const entries = () => prefixesDepartements().map((prefixe) => ({ prefixe }));

export const GET = ({ params }) => {
  const t = tableDepartements(params.prefixe);
  if (!t) error(404, 'Préfixe inconnu');
  return json(t);
};
