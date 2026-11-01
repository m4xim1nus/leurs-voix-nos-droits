import { describe, expect, it } from 'vitest';
import {
  creerMoteur,
  distance,
  estCodePostal,
  motCorrespond,
  motsCherches,
  motsProches,
  nombreResultats
} from './recherche';
import type { EntreeIndex, EcarteIndex, PaysIndex, TexteIndex } from './types';

const texte = (id: string, titre: string, x: Partial<TexteIndex> = {}): TexteIndex => ({
  id,
  titre,
  resume: '',
  etiquettes: [],
  cles: [],
  date: '2024-01-01',
  detail: '',
  url: `/textes/${id}`,
  ...x
});
const ecarte = (dossier: string, titre: string, x: Partial<EcarteIndex> = {}): EcarteIndex => ({
  dossier,
  titre,
  motif: 'Adopté sans aucune voix contre (règle 9).',
  legislature: 17,
  url: null,
  cles: [],
  ...x
});
const elu = (nom: string, x: Partial<EntreeIndex> = {}): EntreeIndex => ({
  slug: nom.toLowerCase(),
  nom,
  feminin: false,
  tri: nom,
  circo: '',
  departement: '',
  sigle: '',
  couleur: '',
  actuel: true,
  ...x
});
const pays = (nom: string, alias: string[] = []): PaysIndex => ({
  pays: nom,
  alias,
  circo: '099-07',
  libelle: '7e circonscription',
  hors_tableau: false,
  depute: null
});

const moteur = creerMoteur({
  elus: [
    elu('Marie Dupont', { actuel: false }),
    elu('Jean Dupont'),
    elu('Éloi Martin'),
    elu('Paul Dupont', { senat: true })
  ],
  textes: [
    texte('duplomb', 'Loi visant à lever les contraintes du métier d’agriculteur', {
      cles: ['loi Duplomb', 'pesticides']
    }),
    texte('kasbarian', 'Loi visant à protéger les logements contre l’occupation illicite', {
      cles: ['squat'],
      date: '2023-07-01'
    }),
    texte('logement', 'Loi sur le logement social', { date: '2020-01-01' }),
    texte('budget', 'Loi de finances', {
      resume: 'Elle supprime l’aide au logement pour certains étudiants.',
      cles: ['APL'],
      date: '2026-01-01'
    }),
    texte('nitrites', 'Additifs nitrés', { etiquettes: ['Alimentation'] }),
    texte('applicable', 'Loi applicable aux aplombs')
  ],
  ecartes: [ecarte('D1', 'Interdiction du glyphosate', { cles: ['Roundup'] })],
  pays: [pays('Allemagne'), pays('Royaume-Uni', ['Angleterre']), pays('Autriche')]
});

const ids = (q: string) => moteur.chercher(q).textes.map((t) => t.id);

describe('motsCherches', () => {
  it('retire les mots vides et le pluriel, accents et casse compris', () => {
    expect(motsCherches('La loi sur les Écrans')).toEqual(['ecran']);
    expect(motsCherches('l’immigration')).toEqual(['immigration']);
  });
  it('garde une saisie faite seulement de mots vides', () => {
    expect(motsCherches('loi')).toEqual(['loi']);
  });
});

describe('motCorrespond', () => {
  it('veut un mot court entier, à un pluriel près', () => {
    expect(motCorrespond('apl', 'apl')).toBe(true);
    expect(motCorrespond('apls', 'apl')).toBe(true);
    expect(motCorrespond('eaux', 'eau')).toBe(true);
    expect(motCorrespond('aplomb', 'apl')).toBe(false);
  });
  it('complète un mot long', () => {
    expect(motCorrespond('logement', 'logem')).toBe(true);
    expect(motCorrespond('relogement', 'logem')).toBe(false);
  });
});

describe('recherche des textes', () => {
  it('trouve un texte par un terme courant absent du titre', () => {
    expect(ids('squat')).toEqual(['kasbarian']);
    expect(ids('Squat')).toEqual(['kasbarian']);
    expect(ids('APL')).toEqual(['budget']);
  });
  it('trouve un surnom, avec ou sans le mot loi', () => {
    expect(ids('loi Duplomb')).toEqual(['duplomb']);
    expect(ids('duplomb')).toEqual(['duplomb']);
  });
  it('ne prend pas APL pour le début de « applicable » ni d’« aplomb »', () => {
    expect(ids('apl')).not.toContain('applicable');
  });
  it('exige tous les mots, dans n’importe quel champ', () => {
    expect(ids('additifs alimentation')).toEqual(['nitrites']);
    expect(ids('additifs logement')).toEqual([]);
  });
  it('place le mot exact du titre, puis un mot voisin, puis le résumé', () => {
    expect(ids('logement')).toEqual(['logement', 'kasbarian', 'budget']);
  });
  it('place une clé exacte en premier', () => {
    const m = creerMoteur({
      elus: [],
      ecartes: [],
      pays: [],
      textes: [
        texte('titre', 'Loi sur les pesticides', { date: '2026-01-01' }),
        texte('cle', 'Loi agricole', { cles: ['pesticides'], date: '2020-01-01' })
      ]
    });
    expect(m.chercher('pesticides').textes.map((t) => t.id)).toEqual(['cle', 'titre']);
  });
  it('traite pluriel et accents dans les deux sens', () => {
    expect(ids('logements')).toContain('logement');
    expect(ids('ECRAN')).toEqual([]);
  });
});

describe('recherche des écartés', () => {
  it('cherche le titre et les termes, pas le motif', () => {
    const e = (q: string) => moteur.chercher(q).ecartes.map((x) => x.dossier);
    expect(e('glyphosate')).toEqual(['D1']);
    expect(e('roundup')).toEqual(['D1']);
    expect(e('voix')).toEqual([]);
  });
});

describe('recherche des élu·es', () => {
  it('range les élu·es en poste, député·es avant sénateur·ices', () => {
    expect(moteur.chercher('dupont').elus.map((e) => e.nom)).toEqual([
      'Jean Dupont',
      'Paul Dupont',
      'Marie Dupont'
    ]);
  });
  it('ne trouve un nom que par le début de ses mots', () => {
    expect(moteur.chercher('loi').elus).toEqual([]);
    expect(moteur.chercher('elo').elus.map((e) => e.nom)).toEqual(['Éloi Martin']);
  });
});

describe('recherche des pays', () => {
  it('trouve un pays par son nom, un alias ou son début', () => {
    expect(moteur.chercher('allemagne').pays.map((p) => p.pays)).toEqual(['Allemagne']);
    expect(moteur.chercher('angleterre').pays.map((p) => p.pays)).toEqual(['Royaume-Uni']);
    expect(moteur.chercher('roya').pays.map((p) => p.pays)).toEqual(['Royaume-Uni']);
  });
  it('demande trois lettres pour compléter un nom', () => {
    expect(moteur.chercher('au').pays).toEqual([]);
    expect(moteur.chercher('aut').pays.map((p) => p.pays)).toEqual(['Autriche']);
  });
});

describe('saisies limites', () => {
  it('ne cherche rien sous deux caractères', () => {
    expect(nombreResultats(moteur.chercher(''))).toBe(0);
    expect(nombreResultats(moteur.chercher('a'))).toBe(0);
    expect(nombreResultats(moteur.chercher(' ; '))).toBe(0);
  });
  it('reconnaît un code postal', () => {
    expect(estCodePostal(' 33000 ')).toBe(true);
    expect(estCodePostal('3300')).toBe(false);
    expect(estCodePostal('2024-42')).toBe(false);
  });
});

describe('tolérance aux fautes de frappe', () => {
  it('compte une inversion de lettres pour une faute', () => {
    expect(distance('kasbarien', 'kasbarian')).toBe(1);
    expect(distance('logmeent', 'logement')).toBe(1);
    expect(distance('abc', 'abc')).toBe(0);
  });
  it('tolère une faute jusqu’à 7 lettres, deux au-delà, aucune sous 4 lettres', () => {
    const voc = ['logement', 'marine', 'mariage', 'apl'];
    expect(motsProches('logemant', voc)).toEqual(['logement']);
    expect(motsProches('lagemant', voc)).toEqual(['logement']);
    expect(motsProches('mariae', voc)).toEqual(['marine', 'mariage']);
    expect(motsProches('mariage', voc)).toEqual(['mariage']);
    expect(motsProches('morige', voc)).toEqual([]);
    expect(motsProches('apk', voc)).toEqual([]);
  });
  const m = creerMoteur({
    elus: [elu('Guillaume Kasbarian')],
    pays: [],
    ecartes: [ecarte('D2', 'Protection des logements')],
    textes: [texte('squat', 'Loi contre l’occupation illicite', { cles: ['loi Kasbarian'] })]
  });
  it('se replie sur la saisie corrigée quand rien ne correspond, et le signale', () => {
    const r = m.chercher('Kasbarien');
    expect(r.approche).toBe(true);
    expect(r.elus.map((e) => e.nom)).toEqual(['Guillaume Kasbarian']);
    expect(r.textes.map((t) => t.id)).toEqual(['squat']);
  });
  it('ne se replie pas dès qu’une recherche exacte donne un résultat', () => {
    const r = m.chercher('Kasbarian');
    expect(r.approche).toBeUndefined();
  });
  it('corrige chaque mot, tous les mots restant exigés', () => {
    expect(m.chercher('occupaton illicite').textes.map((t) => t.id)).toEqual(['squat']);
    expect(m.chercher('occupaton zzzzzz').textes).toEqual([]);
  });
  it('ne renvoie rien, sans le signaler, quand aucune correction n’existe', () => {
    const r = m.chercher('zzzzzz');
    expect(nombreResultats(r)).toBe(0);
    expect(r.approche).toBeUndefined();
  });
});
