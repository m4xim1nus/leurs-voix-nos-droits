import type { PageServerLoad } from './$types';
import { alertes, notesInternes } from '$lib/server/db';

export const load: PageServerLoad = async ({ platform }) => {
  const [a, notes] = await Promise.all([
    alertes(platform!.env.DB),
    notesInternes(platform!.env.DB)
  ]);
  return { alertes: a, notes };
};
