// File « À traiter » : les alertes viennent du pipeline (pipeline/lvnd/alertes.py), d'après les
// qualifications publiées ; D1 sait en plus ce qui a été saisi depuis, publié ou non.

import type { Statut } from './types';

export type TypeAlerte =
  | 'vote_posterieur'
  | 'unanimite_contestee'
  | 'premier_decisif'
  | 'inscrit'
  | 'senat_premier_vote'
  | 'senat_vote_posterieur';

export const LIBELLES_ALERTE: Record<TypeAlerte, string> = {
  vote_posterieur: 'Vote sur l’ensemble après le décisif',
  unanimite_contestee: 'Écarté pour unanimité, vote contesté',
  premier_decisif: 'Décisif d’un texte non traité',
  inscrit: 'Texte non traité, inscrit en séance',
  senat_premier_vote: 'Vote du Sénat sur l’ensemble, à lire',
  senat_vote_posterieur: 'Nouveau vote du Sénat sur l’ensemble'
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
  if (a.type === 'senat_premier_vote' || a.type === 'senat_vote_posterieur') {
    if (statut === 'ecarte') return false;
    const senat = doc
      ? (JSON.parse(doc) as { senat?: { scrutins: { id: string }[] } }).senat
      : null;
    if (a.type === 'senat_premier_vote') return !senat;
    return !senat?.scrutins.some((s) => s.id === a.scrutin_id);
  }
  // Une fiche de suivi répond à l'inscription, pas au vote : celui-ci reste à qualifier.
  if (a.type === 'premier_decisif') return statut === null || statut === 'a-suivre';
  return statut === null;
}
