/// <reference types="vitest/config" />
import adapter from '@sveltejs/adapter-static';
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
      // Site entièrement statique : toutes les routes sont prérendues (src/routes/+layout.ts).
      adapter: adapter({ pages: 'build', assets: 'build', precompress: false, strict: true })
    })
  ],
  // Recette sur téléphone via un tunnel éphémère : `cloudflared tunnel --url http://localhost:4173`.
  preview: { allowedHosts: ['.trycloudflare.com'] },
  test: {
    include: ['src/**/*.test.ts'],
    environment: 'node'
  }
});
