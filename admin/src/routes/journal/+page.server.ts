import type { PageServerLoad } from './$types';
import { journal } from '$lib/server/db';

export const load: PageServerLoad = async ({ platform }) => ({
  revisions: await journal(platform!.env.DB, 200)
});
