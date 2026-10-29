// Identité de l'utilisateur, vérifiée à chaque requête (docs/CONCEPTION.md, Admin).
//
// En ligne : jeton Cloudflare Access obligatoire, refus si la configuration Access manque
// (on échoue fermé). En développement (`vite dev`) sans configuration Access : identité locale.

import { dev } from '$app/environment';
import { error, type Handle } from '@sveltejs/kit';
import { verifier } from '$lib/server/access';

export const handle: Handle = async ({ event, resolve }) => {
  const env = event.platform?.env;
  if (!env?.DB) error(500, 'liaison D1 absente (wrangler.jsonc)');
  if (dev && !env.ACCESS_TEAM_DOMAIN) {
    event.locals.email = 'dev@localhost';
  } else {
    if (!env.ACCESS_TEAM_DOMAIN || !env.ACCESS_AUD)
      error(500, 'Cloudflare Access non configuré (ACCESS_TEAM_DOMAIN, ACCESS_AUD)');
    try {
      event.locals.email = await verifier(event.request.headers.get('cf-access-jwt-assertion'), {
        equipe: env.ACCESS_TEAM_DOMAIN.replace(/\/$/, ''),
        audience: env.ACCESS_AUD
      });
    } catch (e) {
      console.warn('accès refusé :', (e as Error).message);
      error(403, 'Accès refusé');
    }
  }
  const reponse = await resolve(event);
  reponse.headers.set('X-Robots-Tag', 'noindex, nofollow');
  reponse.headers.set('Referrer-Policy', 'same-origin');
  reponse.headers.set('X-Frame-Options', 'DENY');
  return reponse;
};
