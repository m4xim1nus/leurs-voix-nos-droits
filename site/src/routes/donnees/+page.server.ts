import { readdirSync, statSync } from 'node:fs';
import { resolve } from 'node:path';
import { EXPORT, RACINE } from '$lib/server/donnees';

const taille = (chemin: string) => statSync(chemin).size;

export const load = () => {
  const csv = readdirSync(EXPORT)
    .filter((f) => f.endsWith('.csv'))
    .sort()
    .map((f) => ({ nom: f, taille: taille(resolve(EXPORT, f)) }));
  const votes = readdirSync(resolve(EXPORT, 'votes'), { recursive: true, encoding: 'utf8' })
    .filter((f) => f.endsWith('.csv'))
    .sort()
    .map((f) => ({ nom: `votes/${f}`, taille: taille(resolve(EXPORT, 'votes', f)) }));
  return {
    editorial: taille(resolve(RACINE, 'data/editorial.json')),
    csv,
    votes,
    annuaire: ['codes_postaux.csv', 'contacts.csv'].map((f) => ({
      nom: `annuaire/${f}`,
      taille: taille(resolve(RACINE, 'data/annuaire', f))
    }))
  };
};
