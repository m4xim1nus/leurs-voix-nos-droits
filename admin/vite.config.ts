/// <reference types="vitest/config" />
import adapter from '@sveltejs/adapter-cloudflare';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [
    sveltekit({
      compilerOptions: {
        // Runes partout dans le projet (Svelte 5), pas dans les bibliothèques.
        runes: ({ filename }) =>
          filename.split(/[/\\]/).includes('node_modules') ? undefined : true
      },
      // Worker Cloudflare avec ses fichiers statiques (docs/CONCEPTION.md, Admin, choix E). En
      // `vite dev`, les liaisons de wrangler.jsonc (D1 locale dans .wrangler/) sont émulées.
      adapter: adapter(),
      // Aucune ressource tierce : tout vient de l'admin elle-même.
      csp: {
        mode: 'auto',
        directives: {
          'default-src': ['self'],
          'script-src': ['self'],
          'style-src': ['self', 'unsafe-inline'],
          'img-src': ['self', 'data:'],
          'connect-src': ['self'],
          'form-action': ['self'],
          'frame-ancestors': ['none'],
          'base-uri': ['self']
        }
      }
    })
  ],
  test: {
    include: ['src/**/*.test.ts'],
    environment: 'node'
  }
});
