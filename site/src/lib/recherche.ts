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

/** Distance d'édition, une inversion de deux lettres voisines comptant pour une faute. */
export function distance(a: string, b: string): number {
  let avant: number[] = [];
  let prec = Array.from({ length: b.length + 1 }, (_, j) => j);
  for (let i = 1; i <= a.length; i++) {
    const ligne = [i];
    for (let j = 1; j <= b.length; j++) {
      const cout = a[i - 1] === b[j - 1] ? 0 : 1;
      let d = Math.min(prec[j] + 1, ligne[j - 1] + 1, prec[j - 1] + cout);
      if (i > 1 && j > 1 && a[i - 1] === b[j - 2] && a[i - 2] === b[j - 1])
        d = Math.min(d, avant[j - 2] + 1);
      ligne.push(d);
    }
    avant = prec;
    prec = ligne;
  }
  return prec[b.length];
}

/** Fautes tolérées selon la longueur du mot : aucune sous quatre lettres, où tout se ressemble. */
export const fautesTolerees = (mot: string) => (mot.length < 4 ? 0 : mot.length < 8 ? 1 : 2);

/** Les mots du vocabulaire les plus proches de `mot` : lui-même s'il s'y trouve, sinon ceux à la plus petite distance. */
export function motsProches(mot: string, vocabulaire: Iterable<string>): string[] {
  const seuil = fautesTolerees(mot);
  let meilleure = seuil + 1;
  let proches: string[] = [];
  for (const v of vocabulaire) {
    if (v === mot) return [mot];
    if (Math.abs(v.length - mot.length) > meilleure) continue;
    const d = distance(mot, v);
    if (d > seuil) continue;
    if (d < meilleure) {
      meilleure = d;
      proches = [v];
    } else if (d === meilleure) proches.push(v);
  }
  return proches;
}
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
  /** Vrai si rien ne correspondait exactement : ce sont les résultats d'une saisie corrigée. */
  approche?: boolean;
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

  const textesTries = (mots: string[], phrase: string) =>
    textes
      .map(({ t, p }) => ({ t, s: noter(p, mots, phrase) }))
      .filter((x) => x.s > 0)
      .sort((a, b) => b.s - a.s || b.t.date.localeCompare(a.t.date))
      .map((x) => x.t);
  const ecartesTries = (mots: string[], phrase: string) =>
    ecartes
      .map(({ e, p }) => ({ e, s: noter(p, mots, phrase) }))
      .filter((x) => x.s > 0)
      .sort((a, b) => b.s - a.s || b.e.legislature - a.e.legislature)
      .map((x) => x.e);
  // Élu·es : chaque mot saisi commence un mot du nom, pour que « loi » ne trouve pas Éloi.
  const elusTries = (motsBruts: string[]) =>
    elus
      .filter(({ mots: nom }) => motsBruts.every((m) => nom.some((n) => n.startsWith(m))))
      .map((x) => x.e)
      .sort(
        (a, b) =>
          Number(b.actuel) - Number(a.actuel) || Number(a.senat ?? false) - Number(b.senat ?? false)
      );

  // Vocabulaires de la recherche approchée, construits à la première faute seulement.
  let vocabulaires: { documents: Set<string>; noms: Set<string> } | null = null;
  const vocabulaire = () =>
    (vocabulaires ??= {
      documents: new Set(
        [...textes, ...ecartes].flatMap(({ p }) =>
          [...p.motsCles, ...p.motsTitre, ...p.motsEtiquettes, ...p.motsResume].map(singulier)
        )
      ),
      noms: new Set(elus.flatMap((x) => x.mots))
    });

  /** Toutes les corrections d'une saisie, chaque mot remplacé par l'un de ses voisins (au plus quelques-unes). */
  function corrections(mots: string[], voc: Set<string>): string[][] {
    let lignes: string[][] = [[]];
    for (const m of mots) {
      const proches = motsProches(m, voc);
      if (!proches.length) return [];
      lignes = lignes.flatMap((l) => proches.slice(0, 4).map((p) => [...l, p])).slice(0, 8);
    }
    return lignes;
  }

  /** Repli quand rien ne correspond : mêmes règles, sur la saisie corrigée (« Kasbarien » → « kasbarian »). */
  function approchee(phrase: string, mots: string[], motsBruts: string[]): Resultats {
    const { documents, noms } = vocabulaire();
    const unir = <T>(listes: T[][], cle: (x: T) => string) => {
      const vus = new Map<string, T>();
      for (const x of listes.flat()) if (!vus.has(cle(x))) vus.set(cle(x), x);
      return [...vus.values()];
    };
    const docs = corrections(mots, documents);
    return {
      elus: unir(
        corrections(motsBruts, noms).map((l) => elusTries(l)),
        (e) => `${e.senat ? 's' : 'd'}-${e.slug}`
      ),
      pays: pays
        .filter(({ noms }) =>
          noms.some(
            (n) => fautesTolerees(phrase) > 0 && distance(n, phrase) <= fautesTolerees(phrase)
          )
        )
        .map((x) => x.p),
      textes: unir(
        docs.map((l) => textesTries(l, l.join(' '))),
        (t) => t.id
      ),
      ecartes: unir(
        docs.map((l) => ecartesTries(l, l.join(' '))),
        (e) => e.dossier
      ),
      approche: true
    };
  }

  return {
    chercher(q) {
      const phrase = normaliser(q);
      if (phrase.length < 2) return { elus: [], pays: [], textes: [], ecartes: [] };
      const mots = motsCherches(q);
      const motsBruts = phrase.split(' ');
      const exacts: Resultats = {
        elus: elusTries(motsBruts),
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
        textes: textesTries(mots, phrase),
        ecartes: ecartesTries(mots, phrase)
      };
      if (nombreResultats(exacts) > 0) return exacts;
      const r = approchee(phrase, mots, motsBruts);
      return nombreResultats(r) > 0 ? r : exacts;
    }
  };
}

export const nombreResultats = (r: Resultats) =>
  r.elus.length + r.pays.length + r.textes.length + r.ecartes.length;

/** Code postal : cinq chiffres, seule saisie traitée à part. */
export const estCodePostal = (q: string) => /^\d{5}$/.test(q.trim());
