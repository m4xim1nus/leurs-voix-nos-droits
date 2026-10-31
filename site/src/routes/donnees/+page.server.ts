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
  const SENAT = resolve(EXPORT, 'senat');
  const senat = readdirSync(SENAT)
    .filter((f) => f.endsWith('.csv'))
    .sort()
    .map((f) => ({ nom: `senat/${f}`, taille: taille(resolve(SENAT, f)) }));
  const votesSenat = readdirSync(resolve(SENAT, 'votes'))
    .filter((f) => f.endsWith('.csv'))
    .sort()
    .map((f) => ({ nom: `senat/votes/${f}`, taille: taille(resolve(SENAT, 'votes', f)) }));
  return {
    senat,
    votesSenat,
    editorial: taille(resolve(RACINE, 'data/editorial.json')),
    csv,
    votes,
    annuaire: ['codes_postaux.csv', 'contacts.csv', 'cp_departements.csv'].map((f) => ({
      nom: `annuaire/${f}`,
      taille: taille(resolve(RACINE, 'data/annuaire', f))
    }))
  };
};
