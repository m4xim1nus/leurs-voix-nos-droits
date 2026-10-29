import type { LayoutServerLoad } from './$types';
import { meta } from '$lib/server/db';

export const load: LayoutServerLoad = async ({ locals, platform }) => {
  const db = platform!.env.DB;
  const [sync, exportMeta] = await Promise.all([
    meta<string>(db, 'sync'),
    meta<{ genere_le: string }>(db, 'export')
  ]);
  return { email: locals.email, sync, donnees: exportMeta?.genere_le ?? null };
};
