// File « À traiter » : les alertes viennent du pipeline (pipeline/lvnd/alertes.py), d'après les
// qualifications publiées ; D1 sait en plus ce qui a été saisi depuis, publié ou non.

import type { Statut } from './types';

export type TypeAlerte = 'vote_posterieur' | 'unanimite_contestee' | 'premier_decisif' | 'inscrit';

export const LIBELLES_ALERTE: Record<TypeAlerte, string> = {
  vote_posterieur: 'Vote sur l’ensemble après le décisif',
  unanimite_contestee: 'Écarté pour unanimité, vote contesté',
  premier_decisif: 'Décisif d’un texte non traité',
  inscrit: 'Texte non traité, inscrit en séance'
};

export interface Alerte {
  id: string;
  type: TypeAlerte;
  dossier_id: string;
  scrutin_id: string | null;
  date: string;
  titre: string | null;
  detail: string;
}

/** L'alerte reste-t-elle à traiter, vu la qualification de D1 (statut et document JSON) ? */
export function resteATraiter(a: Alerte, statut: Statut | null, doc: string | null): boolean {
  if (a.type === 'unanimite_contestee') return statut === 'ecarte';
  if (a.type === 'vote_posterieur') {
    if (!doc) return true;
    const scrutins = (JSON.parse(doc) as { scrutins?: { id: string }[] }).scrutins ?? [];
    return !scrutins.some((s) => s.id === a.scrutin_id);
  }
  return statut === null;
}
