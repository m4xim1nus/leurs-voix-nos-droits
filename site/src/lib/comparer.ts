// Page Comparer : un·e député·e face à un groupe se lit sur la seule législature de ce groupe (règle 19).

export interface Entite {
  cle: string;
  nom: string;
  sigle: string;
  couleur: string;
  lien: string;
  global: number | null;
  droits: (number | null)[];
  textes: (number | null)[];
  /** Groupe : sa législature. */
  legislature?: number;
  /** Député·e : score global et par droit, pour chaque législature où il ou elle a voté. */
  legislatures?: Record<string, { global: number | null; droits: (number | null)[] }>;
}

/** La législature commune, quand l'un est député·e et l'autre un groupe ; sinon null. */
export function legislatureCommune(a: Entite, b: Entite): number | null {
  if (a.legislatures && b.legislature !== undefined) return b.legislature;
  if (b.legislatures && a.legislature !== undefined) return a.legislature;
  return null;
}

/** L'entité telle qu'elle se compare à l'autre : un·e député·e sans vote sur la législature n'y a pas de score. */
export function faceA(e: Entite, autre: Entite): Entite {
  const leg = legislatureCommune(e, autre);
  if (leg === null || !e.legislatures) return e;
  const s = e.legislatures[leg];
  return { ...e, global: s?.global ?? null, droits: s?.droits ?? e.droits.map(() => null) };
}
