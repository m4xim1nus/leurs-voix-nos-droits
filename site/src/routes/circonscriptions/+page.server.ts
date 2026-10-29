import { donnees } from '$lib/server/donnees';
import { circos } from '$lib/server/vues';

export const load = () => {
  const parDep = new Map<string, { id: string; num: number }[]>();
  for (const [id, c] of circos(donnees())) {
    const l = parDep.get(c.departement) ?? [];
    l.push({ id, num: c.num });
    parDep.set(c.departement, l);
  }
  return {
    departements: [...parDep.entries()]
      .map(([nom, cs]) => ({ nom, circos: cs.sort((a, b) => a.num - b.num) }))
      .sort((a, b) => a.circos[0].id.localeCompare(b.circos[0].id))
  };
};
