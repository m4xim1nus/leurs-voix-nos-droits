// Frise du parcours d'un texte : les grandes étapes en clair, d'après `etapes.csv` et l'état du texte.
// Des faits datés de l'open data, jamais une appréciation. Fonctions pures, testées.

import { attenteNavette, date, etatTexte, majuscule } from './format';
import type { EtapeParcours, EtatTexte, GroupeCourt, OrigineTexte, Parcours } from './types';

/** `fait` : acte accompli ; `bloque` : le texte s'arrête ou est rejeté ; `attente` : ce qui vient ensuite. */
export type Statut = 'fait' | 'bloque' | 'attente';
export type Lieu = 'AN' | 'SN' | 'CMP' | 'CC' | 'GOUV' | null;

export interface PointFrise {
  cle: string;
  lieu: Lieu;
  statut: Statut;
  /** Intitulé court, en clair. */
  titre: string;
  /** Ce que l'acte a donné (« Adopté », « Désaccord »…) ; vide s'il n'y a rien à dire. */
  resultat: string;
  /** Décompte du vote décisif, s'il a eu lieu à cette étape (« adopté par 291 voix contre 241 »). */
  decompte: string;
  date: string | null;
  /** Une phrase pour comprendre l'étape, sans jargon. */
  precision: string;
  groupe: GroupeCourt | null;
  lien: { href: string; texte: string } | null;
}

/**
 * Le vote décisif, quand voter pour revient à soutenir le texte : son décompte s'affiche sur l'étape
 * où il a eu lieu. `etape` est celle du scrutin à l'Assemblée (`AN1`, `CMP`, `ANLDEF`…).
 */
export interface VoteDecisif {
  chambre: 'AN' | 'SN';
  date: string;
  etape: string | null;
  /** « adopté par 291 voix contre 241 ». */
  texte: string;
}

const LECTURE: Record<string, string> = {
  premiere: '1re lecture',
  deuxieme: '2e lecture',
  troisieme: '3e lecture',
  nouvelle: 'Nouvelle lecture',
  definitive: 'Lecture définitive'
};
/** Étape d'un scrutin de l'Assemblée → lecture de `etapes.csv`. */
const LECTURE_SCRUTIN: Record<string, string> = {
  AN1: 'premiere',
  AN2: 'deuxieme',
  AN3: 'troisieme',
  ANNLEC: 'nouvelle',
  ANLDEF: 'definitive'
};
const LIEU: Record<string, string> = { AN: 'à l’Assemblée nationale', SN: 'au Sénat' };
const ISSUE: Record<string, string> = { adopte: 'Adopté', rejete: 'Rejeté' };
const CMP: Record<string, string> = {
  accord: 'Accord : un texte commun est proposé aux deux chambres',
  desaccord: 'Désaccord : pas de texte commun',
  convoquee: 'Réunie'
};

/** « Proposition de loi » ou « Projet de loi » : l'origine, dite sans jargon. */
export function phraseOrigine(o: OrigineTexte): string {
  const lieu = o.chambre ? ` ${LIEU[o.chambre]}` : '';
  if (o.type === 'gouvernement') return `Texte déposé par le gouvernement${lieu}`;
  const par = o.auteur ? ` par ${o.auteur.nom}` : ' par des parlementaires';
  return `Texte déposé${lieu}${par}`;
}

function depot(o: OrigineTexte): PointFrise {
  const parl = o.type === 'parlementaire';
  const cosign =
    parl && o.cosignataires
      ? `${o.cosignataires} cosignataire${o.cosignataires > 1 ? 's' : ''}. `
      : '';
  return {
    cle: 'depot',
    lieu: parl ? (o.chambre ?? null) : 'GOUV',
    statut: 'fait',
    titre: 'Dépôt',
    resultat: '',
    decompte: '',
    date: o.date,
    precision: parl
      ? `${phraseOrigine(o)}${o.groupe ? `, du groupe ${o.groupe.nom}` : ''}. ${cosign}`.trim()
      : `${phraseOrigine(o)}.`,
    groupe: o.groupe,
    lien: o.auteur ? { href: `/deputes/${o.auteur.slug}`, texte: o.auteur.nom } : null
  };
}

function lecture(e: EtapeParcours): PointFrise {
  const nom = (e.lecture && LECTURE[e.lecture]) || 'Lecture';
  const lieu = e.chambre ? LIEU[e.chambre] : '';
  return {
    cle: `${e.etape}-${e.chambre}-${e.lecture}-${e.date}`,
    lieu: e.chambre,
    statut: e.issue === 'rejete' ? 'bloque' : 'fait',
    titre: `${nom} ${lieu}`.trim(),
    resultat: (e.issue && ISSUE[e.issue]) || '',
    decompte: '',
    date: e.date,
    precision: '',
    groupe: null,
    lien: null
  };
}

function cmp(e: EtapeParcours): PointFrise {
  return {
    cle: `cmp-${e.date}`,
    lieu: 'CMP',
    statut: e.issue === 'desaccord' ? 'bloque' : 'fait',
    titre: 'Commission mixte paritaire',
    resultat: (e.issue && CMP[e.issue]) || '',
    decompte: '',
    date: e.date,
    precision: 'Députés et sénateurs cherchent ensemble un texte commun.',
    groupe: null,
    lien: null
  };
}

function conseil(e: EtapeParcours, url: string | null, numero: string | null): PointFrise {
  return {
    cle: `cc-${e.date}`,
    lieu: 'CC',
    statut: 'fait',
    titre: 'Conseil constitutionnel',
    resultat: e.detail ?? 'Décision rendue',
    decompte: '',
    date: e.date,
    precision: 'Il vérifie que la loi respecte la Constitution.',
    groupe: null,
    lien: url ? { href: url, texte: numero ? `Décision n° ${numero}` : 'Décision' } : null
  };
}

function promulgation(e: EtapeParcours, loi: string | null): PointFrise {
  const numero = e.detail ?? loi;
  return {
    cle: `prom-${e.date}`,
    lieu: null,
    statut: 'fait',
    titre: 'Promulgation',
    resultat: numero ? `Loi n° ${numero}` : 'Loi promulguée',
    decompte: '',
    date: e.date,
    precision: 'Le texte devient une loi.',
    groupe: null,
    lien: null
  };
}

const FIN: Record<string, { titre: string; precision: string }> = {
  adopte: { titre: 'Adopté définitivement', precision: 'Pas encore promulgué.' },
  avant_vote: { titre: 'En attente d’un vote', precision: 'Pas encore voté en séance.' },
  a_l_arret: { titre: 'À l’arrêt', precision: '' },
  rejete: { titre: 'Rejeté', precision: 'Le texte n’a pas été adopté.' },
  retire: { titre: 'Retiré', precision: 'Son auteur l’a retiré.' },
  caduc: { titre: 'Caduc', precision: 'Le texte n’a plus d’effet.' },
  fusionne: { titre: 'Fusionné', precision: 'Repris dans un autre texte.' }
};

/** Où le texte en est maintenant, quand il n'est pas une loi : le dernier point de la frise. */
function issue(e: EtatTexte | null, dateEtat: string | null): PointFrise | null {
  if (!e || e.etat === 'loi' || !etatTexte(e)) return null;
  const base = { cle: 'issue', lieu: null, resultat: '', decompte: '', groupe: null, lien: null };
  // Ce que l'état n'est pas seul à dire : la séance où le texte est inscrit, et la date de l'état.
  const suite = [
    e.seance_inscrite ? `Inscrit en séance le ${date(e.seance_inscrite)}.` : '',
    dateEtat ? `État au ${date(dateEtat)}.` : ''
  ];
  if (e.etat === 'en_navette')
    return {
      ...base,
      statut: 'attente',
      titre: 'En cours d’examen',
      resultat: majuscule(attenteNavette(e)),
      date: null,
      precision: suite.filter(Boolean).join(' ')
    };
  const f = FIN[e.etat];
  if (!f) return null;
  const attente = e.etat === 'adopte' || e.etat === 'avant_vote';
  const arret = e.etat === 'a_l_arret' && e.date_derniere_activite;
  return {
    ...base,
    statut: attente ? 'attente' : 'bloque',
    titre: f.titre,
    date: attente ? null : e.date_derniere_activite,
    precision: [
      arret ? `Aucun acte depuis le ${date(e.date_derniere_activite!)}.` : f.precision,
      ...(attente ? suite : [])
    ]
      .filter(Boolean)
      .join(' ')
  };
}

/**
 * Le décompte du vote décisif va sur son étape : la CMP pour le texte de la CMP, sinon la lecture de
 * la même chambre à la même date, puis la lecture du même rang. Faute d'étape, un point « Vote
 * décisif » s'insère à sa date, pour que le décompte ne se perde pas.
 */
function placerVote(pts: PointFrise[], sources: (EtapeParcours | null)[], v: VoteDecisif) {
  const lectures = pts
    .map((p, i) => ({ p, e: sources[i] }))
    .filter((x) => x.e?.etape === 'lecture' && x.e.chambre === v.chambre);
  const cible =
    (v.etape === 'CMP' ? pts.findLast((p) => p.lieu === 'CMP') : undefined) ??
    lectures.find((x) => x.e!.date === v.date)?.p ??
    (v.etape && LECTURE_SCRUTIN[v.etape]
      ? lectures.findLast((x) => x.e!.lecture === LECTURE_SCRUTIN[v.etape!])?.p
      : undefined);
  if (cible) {
    // Le texte de la CMP se vote après la réunion de la commission : le décompte dit alors sa date.
    cible.decompte = cible.date === v.date ? v.texte : `${v.texte}, le ${date(v.date)}`;
    return;
  }
  const point: PointFrise = {
    cle: 'vote-decisif',
    lieu: v.chambre,
    statut: 'fait',
    titre: `Vote décisif ${LIEU[v.chambre]}`,
    resultat: majuscule(v.texte),
    decompte: '',
    date: v.date,
    precision: '',
    groupe: null,
    lien: null
  };
  // Avant le premier point daté plus tard, ou avant l'issue (non datée) qui clôt la frise.
  const i = pts.findIndex((p, k) => k > 0 && (p.date ? p.date > v.date : p.cle === 'issue'));
  pts.splice(i < 0 ? pts.length : i, 0, point);
}

/**
 * Points de la frise, dans l'ordre. Vide si l'open data ne donne ni dépôt ni étape : la page n'affiche
 * alors aucune frise plutôt qu'une frise inventée. Pour un texte devenu loi, la promulgation clôt la
 * frise ; sinon, l'état du texte (en navette, à l'arrêt, rejeté…) la clôt.
 */
export function pointsFrise(
  p: Parcours | null,
  etat: EtatTexte | null,
  loi: {
    numero: string | null;
    dateLoi: string | null;
    ccUrl: string | null;
    ccNumero: string | null;
  },
  { vote = null, dateEtat = null }: { vote?: VoteDecisif | null; dateEtat?: string | null } = {}
): PointFrise[] {
  if (!p || (!p.origine && !p.etapes.length)) return [];
  const pts: PointFrise[] = [];
  // L'étape d'où vient chaque point, pour y placer le vote décisif.
  const sources: (EtapeParcours | null)[] = [];
  const ajouter = (pt: PointFrise, e: EtapeParcours | null) => {
    pts.push(pt);
    sources.push(e);
  };
  if (p.origine) ajouter(depot(p.origine), null);
  for (const e of p.etapes) {
    if (e.etape === 'lecture') ajouter(lecture(e), e);
    else if (e.etape === 'cmp') ajouter(cmp(e), e);
    else if (e.etape === 'cc') ajouter(conseil(e, loi.ccUrl, loi.ccNumero), e);
    else if (e.etape === 'promulgation') ajouter(promulgation(e, loi.numero), e);
  }
  if (etat?.etat === 'loi' && !pts.some((x) => x.titre === 'Promulgation') && loi.dateLoi)
    ajouter(
      promulgation(
        {
          etape: 'promulgation',
          chambre: null,
          lecture: null,
          date: loi.dateLoi,
          issue: null,
          detail: null
        },
        loi.numero
      ),
      null
    );
  const fin = issue(etat, dateEtat);
  if (fin) ajouter(fin, null);
  if (vote) placerVote(pts, sources, vote);
  return pts;
}

/** Résumé lu par un lecteur d'écran avant la liste : combien d'étapes, et la dernière. */
export function resumeFrise(pts: PointFrise[]): string {
  if (!pts.length) return '';
  const der = pts.at(-1)!;
  return `${pts.length} étape${pts.length > 1 ? 's' : ''}. Dernière étape : ${der.titre}${der.date ? `, le ${date(der.date)}` : ''}.`;
}
