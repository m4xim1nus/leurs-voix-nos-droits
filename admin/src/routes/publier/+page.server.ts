import { fail } from '@sveltejs/kit';
import type { Actions, PageServerLoad } from './$types';
import * as db from '$lib/server/db';
import { ConflitGitHub } from '$lib/server/github';
import { message, preparer, publier } from '$lib/server/publication';

export const load: PageServerLoad = async ({ platform }) => {
  const env = platform!.env;
  const prep = await preparer(env.DB, await db.grille(env.DB));
  return {
    textes: prep.textes,
    bloquant: prep.bloquant,
    message: message(prep.textes),
    taille: prep.contenu.length,
    configure: Boolean(env.GITHUB_TOKEN),
    depot: env.GITHUB_REPO,
    branche: env.GITHUB_BRANCH,
    chemin: env.EDITORIAL_CHEMIN,
    publications: await db.publications(env.DB)
  };
};

export const actions: Actions = {
  publier: async ({ platform, locals }) => {
    const env = platform!.env;
    if (!env.GITHUB_TOKEN) return fail(500, { erreur: 'secret GITHUB_TOKEN absent' });
    try {
      const r = await publier(
        env.DB,
        await db.grille(env.DB),
        {
          jeton: env.GITHUB_TOKEN,
          depot: env.GITHUB_REPO,
          branche: env.GITHUB_BRANCH,
          chemin: env.EDITORIAL_CHEMIN
        },
        locals.email
      );
      return { ok: true, commit: r.commit };
    } catch (e) {
      if (e instanceof ConflitGitHub) return fail(409, { erreur: e.message });
      return fail(500, { erreur: (e as Error).message });
    }
  }
};
