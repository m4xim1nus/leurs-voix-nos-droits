// Types partagés entre le prérendu (lib/server) et les pages.

export type Sens = 'etend' | 'restreint';
export type RoleDroit = 'principal' | 'secondaire';
export type RoleScrutin = 'decisif' | 'ensemble' | 'motion' | 'article' | 'amendement';
export type Pour = 'texte' | 'contre-texte' | 'a-trancher';
export type Position = 'pour' | 'contre' | 'abstention' | 'non_votant';
export type PositionGroupe = 'pour' | 'contre' | 'abstention' | 'partage' | 'absent';

export interface Droit {
  code: string;
  libelle: string;
  court: string;
}

export interface Source {
  id: string;
  auteur: string;
  titre: string;
  date: string;
  url: string;
}

export interface DroitTouche {
  code: string;
  role: RoleDroit;
  sens: Sens;
  sources: string[];
  justification: string;
}

/** Un groupe tel qu'affiché : sigle et couleur officiels de l'AN. */
export interface GroupeCourt {
  id: string;
  sigle: string;
  nom: string;
  couleur: string;
}

export interface Lignee extends GroupeCourt {
  /** Organe le plus récent : identifiant des scores de groupe. */
  id: string;
  legislature: number;
  slug: string;
  organes: string[];
  /** Le groupe existe-t-il encore ? */
  actif: boolean;
}

export interface Score {
  n_textes: number;
  favorables: number;
  defavorables: number;
  abstentions: number;
  non_votants: number;
  /** De 0 à 100, ou null si aucun vote pour ou contre. */
  score: number | null;
}

export interface Ventilation {
  groupe: GroupeCourt;
  membres: number;
  pour: number;
  contre: number;
  abstention: number;
  non_votants: number;
  position: PositionGroupe;
  cohesion: number | null;
}

export interface Amendement {
  numero: string;
  division: string;
  auteur: string | null;
  groupe: string | null;
  sort: string;
}

export interface ScrutinRetenu {
  id: string;
  numero: number;
  legislature: number;
  role: RoleScrutin;
  pour: Pour;
  objet: string;
  date: string;
  sort: 'adopte' | 'rejete';
  decompte: { pour: number; contre: number; abstention: number };
  /** Compté dans les scores (décisif ou amendement clé, sens fixé). */
  compte: boolean;
  poids: number;
  /** Position favorable aux droits, au sens du droit principal du texte. */
  favorable: 'pour' | 'contre' | null;
  amendement: Amendement | null;
  ventilations: Ventilation[];
  url: string;
}

export interface Texte {
  id: string;
  dossier_an: string;
  legislature: number;
  titre: string;
  resume: string;
  droits: DroitTouche[];
  principal: DroitTouche;
  etiquettes: string[];
  vigilance: { texte: string; sources: string[] }[];
  conseil_constitutionnel: string;
  note: string;
  sources: Record<string, Source>;
  scrutins: ScrutinRetenu[];
  date: string;
  loi: string | null;
  date_loi: string | null;
  url_an: string | null;
  url_loi: string | null;
  cc_decision: string | null;
  cc_url: string | null;
}

export interface Ecarte {
  dossier_an: string;
  legislature: number;
  titre: string;
  motif: string;
  url_an: string | null;
}

export interface Mandat {
  legislature: number;
  departement: string;
  circo: string;
  num_circo: number;
  debut: string;
  fin: string | null;
  cause_fin: string | null;
}

export interface Appartenance {
  groupe: GroupeCourt;
  legislature: number;
  debut: string;
  fin: string | null;
  qualite: string;
}

export interface Depute {
  id: string;
  slug: string;
  civ: string;
  prenom: string;
  nom: string;
  nom_tri: string;
  mandats: Mandat[];
  groupes: Appartenance[];
  courriel: string | null;
  site: string | null;
}

export interface Participation {
  scrutins: number;
  votes: number;
  non_votants: number;
  taux: number;
}

/** Entrée de l'index de recherche par nom (JSON chargé à la demande). */
export interface EntreeIndex {
  slug: string;
  nom: string;
  feminin: boolean;
  tri: string;
  circo: string;
  departement: string;
  sigle: string;
  couleur: string;
  actuel: boolean;
}

/** Table d'un préfixe de code postal (JSON chargé à la demande). */
export interface TableCodesPostaux {
  codes: Record<string, { commune: string; circo: string; part: number | null }[]>;
  circos: Record<string, { libelle: string; depute: EntreeIndex | null }>;
}
