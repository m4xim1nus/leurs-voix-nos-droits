// Types globaux de SvelteKit : liaisons du Worker (wrangler.jsonc) et identité de l'utilisateur.
declare global {
  namespace App {
    interface Locals {
      /** Courriel de l'utilisateur, fourni par Cloudflare Access (src/hooks.server.ts). */
      email: string;
    }
    interface Platform {
      env: {
        DB: D1Database;
        GITHUB_TOKEN?: string;
        GITHUB_REPO: string;
        GITHUB_BRANCH: string;
        EDITORIAL_CHEMIN: string;
        ACCESS_TEAM_DOMAIN: string;
        ACCESS_AUD: string;
      };
    }
  }
}

export {};
