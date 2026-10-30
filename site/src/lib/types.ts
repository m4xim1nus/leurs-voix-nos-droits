// Types partagés entre le prérendu (lib/server) et les pages.

export type Sens = 'etend' | 'restreint';
export type RoleDroit = 'principal' | 'secondaire';
export type RoleScrutin = 'decisif' | 'ensemble' | 'motion' | 'article' | 'amendement' | 'censure';
export type Pour = 'texte' | 'contre-texte' | 'a-trancher';
export type Position = 'pour' | 'contre' | 'abstention' | 'non_votant';
export type PositionGroupe = 'pour' | 'contre' | 'abstention' | 'partage' | 'absent';

/** Où en est un texte : `en_cours_etats.csv`, jamais une appréciation (docs/SOURCES.md). */
export interface EtatTexte {
  etat:
    | 'loi'
    | 'adopte'
    | 'en_navette'
    | 'avant_vote'
    | 'hors_navette'
    | 'a_l_arret'
    | 'rejete'
    | 'retire'
    | 'caduc'
    | 'fusionne';
  /** `lecture`, `transmis`, `cmp`, `cmp_conclusions` ou `navette`. */
  attente: string | null;
  /** `AN`, `SN` ou `CMP`. */
  attente_chambre: string | null;
  date_derniere_lecture: string | null;
  date_derniere_activite: string | null;
  /** Première séance à venir où le texte est inscrit. Inscrit ne veut pas dire voté. */
  seance_inscrite: string | null;
}

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
  /** Lecture du scrutin (AN1, AN2, ANNLEC, CMP…), vide si l'open data ne la donne pas. */
  etape: string | null;
  sort: 'adopte' | 'rejete';
  decompte: { pour: number; contre: number; abstention: number; requis: number | null };
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
  /** Date du vote décisif, ou de la dernière motion de censure (texte adopté par 49.3). */
  date: string;
  /** Adopté par 49.3 sans vote final : qualifié, compté dans aucun score (règle 9). */
  sans_vote: boolean;
  etat: EtatTexte | null;
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
  etat: EtatTexte | null;
}

export interface TexteUnanime {
  dossier_an: string;
  titre: string;
  url_an: string | null;
  etat: EtatTexte | null;
  scrutin: { id: string; date: string; pour: number; contre: number; url: string };
  ventilations: Ventilation[];
}

/** Un vote public de l'AN sur un texte en cours, affiché avec la position de chaque groupe. */
export interface VoteAN {
  id: string;
  numero: number;
  date: string;
  etape: string | null;
  sort: 'adopte' | 'rejete';
  decompte: { pour: number; contre: number; abstention: number };
  ventilations: Ventilation[];
  url: string;
}

/** Point de l'ordre du jour : `eventuel` si la réunion n'est pas confirmée. */
export interface PointAgenda {
  date: string;
  etat: 'confirme' | 'eventuel';
}

/** Ce qu'un texte en cours attend : une séance, une chambre, la CMP, ou rien de connu. */
export type Echeance = 'inscrit' | 'AN' | 'SN' | 'CMP' | 'inconnue';

/** Texte de la page /en-cours : retenu à la main, jamais par les seuls mots-clés. */
export interface TexteEnCours {
  dossier_an: string;
  id: string;
  titre: string;
  /** Sa fiche : /textes/<id> s'il est qualifié, son ancre sur /en-cours sinon. */
  href: string;
  etat: EtatTexte;
  echeance: Echeance;
  /** Chambre où le texte est attendu, si elle est connue. */
  chambre: 'AN' | 'SN' | null;
  seances: PointAgenda[];
  commissions: (PointAgenda & { organe: string })[];
  /** Le texte qualifié : son droit principal, et la date du vote sur lequel le sens a été lu. */
  qualification: { code: string; sens: Sens; date: string | null } | null;
  /** Fiche de suivi d'un texte pas encore qualifié : droits touchés et sources, sans sens ni score. */
  suivi: {
    resume: string;
    note: string;
    droits: { code: string; justification: string; sources: Source[] }[];
  } | null;
  dernier_vote: VoteAN | null;
  /** Le dernier vote est-il celui sur lequel le texte a été qualifié ? */
  vote_qualifie: boolean;
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
