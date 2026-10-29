import { donnees } from '$lib/server/donnees';

export const load = () => {
  const d = donnees();
  return { genereLe: d.genereLe, nTextes: d.textes.length };
};
