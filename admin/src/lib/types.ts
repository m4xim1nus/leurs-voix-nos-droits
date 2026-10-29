// Types partagés : catalogue (tables remplies par `lvnd sync-admin`) et qualification (format 1
// d'editorial.json, docs/CONCEPTION.md).

export type Statut = 'brouillon' | 'a-relire' | 'valide' | 'ecarte';
export type RoleDroit = 'principal' | 'secondaire';
export type Sens = 'etend' | 'restreint';
export type RoleScrutin = 'decisif' | 'ensemble' | 'motion' | 'article' | 'amendement' | 'censure';
export type Pour = 'texte' | 'contre-texte' | 'a-trancher';

export interface DroitQualifie {
  code: string;
  role: RoleDroit;
  sens: Sens;
  sources: string[];
  justification: string;
}

export interface Source {
  auteur: string;
  titre: string;
  date: string;
  url: string;
}

export interface Vigilance {
  texte: string;
  sources: string[];
}

export interface ScrutinRetenu {
  id: string;
  role: RoleScrutin;
  pour: Pour;
  objet: string;
}

/** Une entrée de `textes` dans editorial.json. */
export interface Qualification {
  id: string;
  dossier_an: string;
  legislature: number;
  titre: string;
  resume: string;
  droits: DroitQualifie[];
  etiquettes: string[];
  vigilance: Vigilance[];
  conseil_constitutionnel: string;
  note: string;
  sources: Record<string, Source>;
  scrutins: ScrutinRetenu[];
}

export interface Ecarte {
  dossier_an: string;
  legislature: number;
  titre: string;
  motif: string;
}

export interface Editorial {
  format: number;
  grille: number;
  textes: Qualification[];
  ecartes: Ecarte[];
}

export interface Grille {
  version: number;
  droits: { code: string; libelle: string }[];
  etiquettes: { code: string; libelle: string }[];
  sens: { code: Sens; libelle: string }[];
}

/** Ligne de la table `textes` (catalogue). */
export interface TexteCatalogue {
  id: string;
  legislature: number;
  titre: string;
  procedure: string | null;
  initiative: string | null;
  nature: string | null;
  url_an: string | null;
  loi: string | null;
  date_loi: string | null;
  nor: string | null;
  url_loi: string | null;
  cc_decision: string | null;
  cc_sens: string | null;
  cc_url: string | null;
  n_scrutins: number;
  n_amendements: number;
  n_ensemble: number;
  decisif_propose: string | null;
  premier_scrutin: string | null;
  dernier_scrutin: string | null;
  droits_candidats: string | null;
  etiquettes_candidates: string | null;
  motifs: string | null;
}

/** [groupe, pour, contre, abstention, non_votants, position, cohésion] */
export type PositionGroupe = [string, number, number, number, number, string, number | null];

/** Ligne de la table `scrutins`, positions décodées. */
export interface ScrutinCatalogue {
  id: string;
  texte_id: string;
  legislature: number;
  numero: number;
  date: string;
  type_vote: string | null;
  titre: string | null;
  objet: string | null;
  etape: string | null;
  sort: string | null;
  pour: number;
  contre: number;
  abstention: number;
  non_votants: number;
  amendement_id: string | null;
  amendement_numero: string | null;
  amendement_division: string | null;
  amendement_auteur: string | null;
  amendement_sort: string | null;
  positions: PositionGroupe[];
}

export interface Groupe {
  id: string;
  lignee: string;
  legislature: number;
  sigle: string;
  nom: string;
  couleur: string | null;
  date_debut: string | null;
  date_fin: string | null;
}

/** Ligne de la table `qualifications`, document décodé. */
export interface LigneQualification {
  dossier_an: string;
  statut: Statut;
  doc: Qualification;
  motif_ecart: string | null;
  modifie_par: string;
  modifie_le: string;
  publie_empreinte: string | null;
}
