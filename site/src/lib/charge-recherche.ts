// Chargement à la demande des index de la recherche. Une seule fois par page, partagé par la case de l'en-tête, la case
// de l'accueil et la page de résultats. Aucun de ces fichiers ne reçoit ce que l'on cherche : ce sont des JSON statiques.

import { creerMoteur, type Moteur } from './recherche';
import type { EcarteIndex, EntreeIndex, PaysIndex, TableCodesPostaux, TexteIndex } from './types';

async function json<T>(url: string): Promise<T> {
  const r = await fetch(url);
  if (!r.ok) throw new Error(String(r.status));
  return r.json();
}

let moteur: Promise<Moteur> | null = null;

export function chargerMoteur(): Promise<Moteur> {
  moteur ??= Promise.all([
    json<EntreeIndex[]>('/recherche/deputes.json'),
    json<EntreeIndex[]>('/recherche/senateurs.json'),
    json<{ textes: TexteIndex[]; ecartes: EcarteIndex[] }>('/recherche/textes.json'),
    json<PaysIndex[]>('/recherche/pays.json')
  ]).then(([deputes, senateurs, { textes, ecartes }, pays]) =>
    creerMoteur({ elus: [...deputes, ...senateurs], textes, ecartes, pays })
  );
  // Un échec ne se garde pas en cache : la frappe suivante réessaie.
  moteur.catch(() => (moteur = null));
  return moteur;
}

export interface CircoTrouvee {
  id: string;
  libelle: string;
  communes: string[];
  depute: EntreeIndex | null;
}

export type ResultatCP = { erreur: string } | { cp: string; circos: CircoTrouvee[] };

const tables = new Map<string, TableCodesPostaux>();

/** Députés d'un code postal : une circonscription, ou plusieurs avec leurs communes (docs/CONCEPTION.md). */
export async function chercherCodePostal(saisie: string): Promise<ResultatCP> {
  const q = saisie.trim();
  const prefixe = q.slice(0, 2);
  try {
    if (!tables.has(prefixe))
      tables.set(prefixe, await json<TableCodesPostaux>(`/recherche/cp/${prefixe}.json`));
  } catch {
    return { erreur: `Aucun code postal ne commence par ${prefixe}.` };
  }
  const t = tables.get(prefixe)!;
  const lignes = t.codes[q];
  if (!lignes) return { erreur: `Le code postal ${q} n’existe pas dans la base de La Poste.` };
  const ids = [...new Set(lignes.map((l) => l.circo))];
  return {
    cp: q,
    circos: ids.map((id) => ({
      id,
      libelle: t.circos[id].libelle,
      communes: [...new Set(lignes.filter((l) => l.circo === id).map((l) => l.commune))],
      depute: t.circos[id].depute
    }))
  };
}
