import type { PageServerLoad } from './$types';
import { alertes } from '$lib/server/db';

export const load: PageServerLoad = async ({ platform }) => ({
  alertes: await alertes(platform!.env.DB)
});
