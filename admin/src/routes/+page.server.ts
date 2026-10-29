import type { PageServerLoad } from './$types';
import { grille, textes } from '$lib/server/db';

export const load: PageServerLoad = async ({ platform }) => {
  const db = platform!.env.DB;
  const [lignes, g] = await Promise.all([textes(db), grille(db)]);
  return { textes: lignes, grille: g };
};
