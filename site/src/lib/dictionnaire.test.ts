// Le dictionnaire des données suit les exports : un fichier ou une colonne ajoutés sans y être décrits font échouer le test.
import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const racine = resolve(import.meta.dirname, '../../..');
const dico = readFileSync(resolve(racine, 'site/static/donnees.md'), 'utf8');
const llms = readFileSync(resolve(racine, 'site/static/llms.txt'), 'utf8');

const colonnes = (chemin: string) => readFileSync(chemin, 'utf8').split('\n', 1)[0].split(',');
const csv = (dossier: string) => readdirSync(dossier).filter((f) => f.endsWith('.csv'));

/** Texte de la section `### `nom``, jusqu'à la section suivante. */
function section(nom: string): string {
  const debut = dico.indexOf(`### \`${nom}\``);
  if (debut < 0) return '';
  const fin = dico.slice(debut + 4).search(/^##/m);
  return fin < 0 ? dico.slice(debut) : dico.slice(debut, debut + 4 + fin);
}

const COMMUNES = ['votes_favorables', 'votes_defavorables', 'abstentions', 'non_votants', 'score'];

function manquantes(nom: string, chemin: string): string[] {
  const s = section(nom);
  if (!s) return [`section ${nom}`];
  return colonnes(chemin)
    .filter((c) => !s.includes(`\`${c}\``))
    .filter((c) => !(s.includes('colonnes communes') && [...COMMUNES, 'n_textes'].includes(c)))
    .map((c) => `${nom} : ${c}`);
}

describe('dictionnaire des données', () => {
  const exportDir = resolve(racine, 'data/export');
  it('décrit chaque colonne de chaque fichier', () => {
    const fichiers: [string, string][] = [
      ...csv(exportDir).map((f): [string, string] => [f, resolve(exportDir, f)]),
      ...csv(resolve(exportDir, 'senat')).map((f): [string, string] => [
        `senat/${f}`,
        resolve(exportDir, 'senat', f)
      ]),
      ...csv(resolve(racine, 'data/annuaire')).map((f): [string, string] => [
        `annuaire/${f}`,
        resolve(racine, 'data/annuaire', f)
      ])
    ];
    expect(fichiers.flatMap(([n, c]) => manquantes(n, c))).toEqual([]);
  });
  it('décrit les votes nominatifs', () => {
    const v = resolve(exportDir, 'votes/17');
    expect(manquantes('votes/<législature>/<AAAA-MM>.csv', resolve(v, csv(v)[0]))).toEqual([]);
    const s = resolve(exportDir, 'senat/votes');
    expect(manquantes('senat/votes/<AAAA-MM>.csv', resolve(s, csv(s)[0]))).toEqual([]);
  });
  it('ne pointe llms.txt que vers des fichiers qui existent', () => {
    const donnees = [...llms.matchAll(/technoperchoir\.fr\/donnees\/([\w/.-]+)/g)].map((m) => m[1]);
    expect(donnees.length).toBeGreaterThan(5);
    const absent = donnees.filter((f) =>
      f === 'editorial.json'
        ? !existsSync(resolve(racine, 'data/editorial.json'))
        : !existsSync(resolve(exportDir, f))
    );
    expect(absent).toEqual([]);
  });
});
