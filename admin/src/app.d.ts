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
        /** Termes jamais publiés, un par ligne (secret ; CLAUDE.md, règles dures). */
        TERMES_INTERDITS?: string;
        /** Chiffre la clé d'API du LLM dans D1 ; même valeur dans les secrets du dépôt (lib/server/llm.ts). */
        LLM_CHIFFREMENT?: string;
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
