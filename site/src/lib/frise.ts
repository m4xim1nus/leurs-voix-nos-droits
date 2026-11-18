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
  date: string | null;
  /** Une phrase pour comprendre l'étape, sans jargon. */
  precision: string;
  groupe: GroupeCourt | null;
  lien: { href: string; texte: string } | null;
}

const LECTURE: Record<string, string> = {
  premiere: '1re lecture',
  deuxieme: '2e lecture',
  troisieme: '3e lecture',
  nouvelle: 'Nouvelle lecture',
  definitive: 'Lecture définitive'
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
function issue(e: EtatTexte | null): PointFrise | null {
  if (!e || e.etat === 'loi' || !etatTexte(e)) return null;
  const base = { cle: 'issue', lieu: null, resultat: '', groupe: null, lien: null };
  if (e.etat === 'en_navette')
    return {
      ...base,
      statut: 'attente',
      titre: 'En cours d’examen',
      resultat: majuscule(attenteNavette(e)),
      date: null,
      precision: ''
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
    precision: arret ? `Aucun acte depuis le ${date(e.date_derniere_activite!)}.` : f.precision
  };
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
  }
): PointFrise[] {
  if (!p || (!p.origine && !p.etapes.length)) return [];
  const pts: PointFrise[] = [];
  if (p.origine) pts.push(depot(p.origine));
  for (const e of p.etapes) {
    if (e.etape === 'lecture') pts.push(lecture(e));
    else if (e.etape === 'cmp') pts.push(cmp(e));
    else if (e.etape === 'cc') pts.push(conseil(e, loi.ccUrl, loi.ccNumero));
    else if (e.etape === 'promulgation') pts.push(promulgation(e, loi.numero));
  }
  if (etat?.etat === 'loi' && !pts.some((x) => x.titre === 'Promulgation') && loi.dateLoi)
    pts.push(
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
      )
    );
  const fin = issue(etat);
  if (fin) pts.push(fin);
  return pts;
}

/** Résumé lu par un lecteur d'écran avant la liste : combien d'étapes, et la dernière. */
export function resumeFrise(pts: PointFrise[]): string {
  if (!pts.length) return '';
  const der = pts.at(-1)!;
  return `${pts.length} étape${pts.length > 1 ? 's' : ''}. Dernière étape : ${der.titre}${der.date ? `, le ${date(der.date)}` : ''}.`;
}
