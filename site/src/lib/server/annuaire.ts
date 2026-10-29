// Code postal → circonscription(s) → député en cours (data/annuaire/codes_postaux.csv, écrit par
// `lvnd annuaire`).

import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { csvParse } from 'd3-dsv';
import { circonscription } from '$lib/format';
import type { TableCodesPostaux } from '$lib/types';
import { donnees, RACINE } from './donnees';
import { circos, entree } from './vues';

let lignes: Record<string, string | undefined>[] | null = null;
const codes = () =>
  (lignes ??= csvParse(readFileSync(resolve(RACINE, 'data/annuaire/codes_postaux.csv'), 'utf8')));

export const prefixes = () => [...new Set(codes().map((l) => l.cp!.slice(0, 2)))].sort();

/** Libellé d'une circonscription : « Gironde, 4e circonscription ». */
export const libelleCirco = (departement: string, num: number) =>
  `${departement}, ${circonscription(num)}`;

export function tableCodesPostaux(prefixe: string): TableCodesPostaux | null {
  const d = donnees();
  const toutes = circos(d);
  const t: TableCodesPostaux = { codes: {}, circos: {} };
  for (const l of codes()) {
    if (!l.cp!.startsWith(prefixe)) continue;
    (t.codes[l.cp!] ??= []).push({
      commune: l.commune!,
      circo: l.circo!,
      part: l.part ? Number(l.part) : null
    });
    if (!t.circos[l.circo!]) {
      const c = toutes.get(l.circo!);
      const dep = c?.deputes.find((x) =>
        x.mandats.some((m) => m.circo === l.circo && m.legislature === 17 && m.fin === null)
      );
      t.circos[l.circo!] = {
        libelle: c ? libelleCirco(c.departement, c.num) : l.circo!,
        depute: dep ? entree(d, dep) : null
      };
    }
  }
  return Object.keys(t.codes).length ? t : null;
}
