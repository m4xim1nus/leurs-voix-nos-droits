// Moteur de la recherche du site : fonctions pures, testées sans navigateur (recherche.test.ts). Tout se passe dans le
// navigateur, sur des JSON statiques : aucune requête ne part vers un serveur avec ce que l'on cherche.

import { normaliser } from './format';
import type { EcarteIndex, EntreeIndex, PaysIndex, TexteIndex } from './types';

/** Mots sans valeur de recherche : « la loi sur le logement » cherche « logement ». */
const MOTS_VIDES = new Set(
  (
    'a au aux c d de des du en et j l la le les m n ou par pour qu que s sur t un une dans avec contre ' +
    'loi lois texte textes proposition projet'
  ).split(' ')
);

/** Pluriel ramené au singulier, pour que « logements » trouve « logement ». */
const singulier = (m: string) => (m.length > 3 ? m.replace(/[sx]$/, '') : m);

/** Mots utiles d'une saisie. Une saisie faite seulement de mots vides (« loi ») les garde. */
export function motsCherches(q: string): string[] {
  const mots = normaliser(q).split(' ').filter(Boolean);
  const utiles = mots.filter((m) => !MOTS_VIDES.has(m));
  return (utiles.length ? utiles : mots).map(singulier);
}

/**
 * Un mot court doit être entier, à un pluriel près : « APL » ne trouve pas « aplomb », « eau » trouve
 * « eaux » mais pas « eaubonne ». Un mot plus long se complète (« logem » trouve « logement »).
 */
export function motCorrespond(mot: string, cherche: string): boolean {
  if (cherche.length <= 3) return mot === cherche || mot === `${cherche}s` || mot === `${cherche}x`;
  return mot.startsWith(cherche);
}

const dans = (mots: string[], cherche: string) => mots.some((m) => motCorrespond(m, cherche));
const decoupe = (s: string) => normaliser(s).split(' ').filter(Boolean);

interface Prepare {
  /** Termes courants et surnoms, normalisés. */
  cles: string[];
  motsCles: string[];
  motsTitre: string[];
  motsEtiquettes: string[];
  motsResume: string[];
  phraseTitre: string;
}

function preparer(titre: string, cles: string[], etiquettes: string[], resume: string): Prepare {
  const normalisees = cles.map(normaliser);
  return {
    cles: normalisees,
    motsCles: normalisees.flatMap((c) => c.split(' ')),
    motsTitre: decoupe(titre),
    motsEtiquettes: etiquettes.flatMap(decoupe),
    motsResume: decoupe(resume),
    phraseTitre: normaliser(titre)
  };
}

const POIDS = {
  cleExacte: 100,
  clePhrase: 60,
  titrePhrase: 50,
  cle: 12,
  titre: 10,
  etiquette: 6,
  resume: 2
};

const contientPhrase = (texte: string, phrase: string) => ` ${texte} `.includes(` ${phrase} `);

/** Score d'un document, 0 si l'un des mots cherchés n'y figure pas. */
function noter(p: Prepare, mots: string[], phrase: string): number {
  let score = 0;
  for (const m of mots) {
    const poids = Math.max(
      dans(p.motsCles, m) ? POIDS.cle : 0,
      dans(p.motsTitre, m) ? POIDS.titre : 0,
      dans(p.motsEtiquettes, m) ? POIDS.etiquette : 0,
      dans(p.motsResume, m) ? POIDS.resume : 0
    );
    if (!poids) return 0;
    score += poids;
  }
  if (p.cles.includes(phrase)) score += POIDS.cleExacte;
  else if (p.cles.some((c) => contientPhrase(c, phrase))) score += POIDS.clePhrase;
  if (contientPhrase(p.phraseTitre, phrase)) score += POIDS.titrePhrase;
  return score;
}

export interface IndexRecherche {
  elus: EntreeIndex[];
  textes: TexteIndex[];
  ecartes: EcarteIndex[];
  pays: PaysIndex[];
}

export interface Resultats {
  elus: EntreeIndex[];
  pays: PaysIndex[];
  textes: TexteIndex[];
  ecartes: EcarteIndex[];
}

export interface Moteur {
  chercher(q: string): Resultats;
}

/** Prépare l'index une fois pour toutes : la normalisation de 800 textes ne se refait pas à chaque frappe. */
export function creerMoteur(index: IndexRecherche): Moteur {
  const textes = index.textes.map((t) => ({
    t,
    p: preparer(t.titre, t.cles, t.etiquettes, t.resume)
  }));
  // Un motif d'écart n'est pas cherché : il est fait de formules répétées (« règle 9 », « aucune voix contre »).
  const ecartes = index.ecartes.map((e) => ({ e, p: preparer(e.titre, e.cles, [], '') }));
  const elus = index.elus.map((e) => ({ e, mots: decoupe(e.nom) }));
  const pays = index.pays.map((p) => ({
    p,
    noms: [p.pays, ...p.alias].map(normaliser)
  }));

  return {
    chercher(q) {
      const phrase = normaliser(q);
      if (phrase.length < 2) return { elus: [], pays: [], textes: [], ecartes: [] };
      const mots = motsCherches(q);
      const motsBruts = phrase.split(' ');
      const trouveTextes = textes
        .map(({ t, p }) => ({ t, s: noter(p, mots, phrase) }))
        .filter((x) => x.s > 0)
        .sort((a, b) => b.s - a.s || b.t.date.localeCompare(a.t.date))
        .map((x) => x.t);
      const trouveEcartes = ecartes
        .map(({ e, p }) => ({ e, s: noter(p, mots, phrase) }))
        .filter((x) => x.s > 0)
        .sort((a, b) => b.s - a.s || b.e.legislature - a.e.legislature)
        .map((x) => x.e);
      return {
        // Élu·es : chaque mot saisi commence un mot du nom, pour que « loi » ne trouve pas Éloi.
        elus: elus
          .filter(({ mots: nom }) => motsBruts.every((m) => nom.some((n) => n.startsWith(m))))
          .map((x) => x.e)
          .sort(
            (a, b) =>
              Number(b.actuel) - Number(a.actuel) ||
              Number(a.senat ?? false) - Number(b.senat ?? false)
          ),
        pays: pays
          .filter(({ noms }) =>
            noms.some(
              (n) =>
                n === phrase ||
                n.startsWith(`${phrase} `) ||
                (phrase.length >= 3 && n.startsWith(phrase))
            )
          )
          .map((x) => x.p),
        textes: trouveTextes,
        ecartes: trouveEcartes
      };
    }
  };
}

export const nombreResultats = (r: Resultats) =>
  r.elus.length + r.pays.length + r.textes.length + r.ecartes.length;

/** Code postal : cinq chiffres, seule saisie traitée à part. */
export const estCodePostal = (q: string) => /^\d{5}$/.test(q.trim());
