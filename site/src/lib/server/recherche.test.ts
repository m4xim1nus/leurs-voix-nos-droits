// La recherche sur les vraies données : ce que les gens tapent doit mener au bon texte, en tête de liste.
import { describe, expect, it } from 'vitest';
import { creerMoteur } from '$lib/recherche';
import { indexDeputes } from './vues';
import { indexSenateurs } from './vues-senat';
import { indexPays, indexTextes } from './recherche';

const { textes, ecartes } = indexTextes();
const pays = indexPays();
const moteur = creerMoteur({
  elus: [...indexDeputes(), ...indexSenateurs()],
  textes,
  ecartes,
  pays
});
const premiers = (q: string, n = 5) =>
  moteur
    .chercher(q)
    .textes.slice(0, n)
    .map((t) => t.id);

describe('index de la recherche', () => {
  it('contient tous les textes qualifiés et écartés, avec un lien', () => {
    expect(textes.length).toBeGreaterThanOrEqual(199);
    expect(ecartes.length).toBeGreaterThan(600);
    for (const t of textes) expect(t.url, t.id).toMatch(/^\/(textes|en-cours)/);
  });

  it('ne publie ni justification ni scrutin', () => {
    expect(Object.keys(textes[0]).sort()).toEqual(
      ['cles', 'date', 'detail', 'etiquettes', 'id', 'resume', 'titre', 'url'].sort()
    );
  });

  it('donne une circonscription réelle à chaque pays', () => {
    expect(pays.length).toBeGreaterThan(190);
    for (const p of pays) expect(p.circo, p.pays).toMatch(/^099-(0[1-9]|1[01])$/);
  });
});

describe('termes témoins', () => {
  it.each([
    ['squat', 'kasbarian-berge'],
    ['loi Kasbarian', 'kasbarian-berge'],
    ['APL', 'plf-2018'],
    ['loi Duplomb', 'duplomb-2025'],
    ['acétamipride', 'duplomb-2025'],
    ['reconnaissance faciale', 'reconnaissance-biometrique-2023'],
    ['loi Darmanin', 'immigration-2024'],
    ['réforme des retraites', 'retraites-2023'],
    ['64 ans', 'retraites-2023'],
    ['PMA', 'bioethique-2021'],
    ['IVG dans la Constitution', 'ivg-constitution-2024'],
    ['pass sanitaire', 'gestion-crise-sanitaire-2021'],
    ['fin de vie', 'aide-a-mourir'],
    ['loi Avia', 'contenus-haineux-2020'],
    ['ZFE', 'climat-resilience-2021'],
    ['RSA', 'plein-emploi-2023'],
    ['mégabassines', 'moratoire-megabassines-ppl-2023'],
    ['Airbnb', 'meubles-tourisme-2024'],
    ['A69', 'a69-riipm-2025'],
    ['polluants éternels', 'pfas-2025']
  ])('« %s » mène à %s', (q, id) => {
    expect(premiers(q)).toContain(id);
  });

  it('trouve un texte écarté par son surnom', () => {
    expect(moteur.chercher('loi Schiappa').ecartes.map((e) => e.dossier)).toContain(
      'DLR5L15N36496'
    );
  });
});

describe('pays', () => {
  it.each([
    ['Allemagne', '099-07'],
    ['USA', '099-01'],
    ['Angleterre', '099-03'],
    ['Maroc', '099-09'],
    ['Taïwan', '099-11']
  ])('« %s » → %s', (q, circo) => {
    expect(moteur.chercher(q).pays[0]?.circo).toBe(circo);
  });
});
