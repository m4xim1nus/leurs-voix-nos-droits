// Index de la recherche du site, écrits au build dans /recherche/*.json et chargés à la demande. Hors index, par
// décision (cycle Recherche) : les 18 000 scrutins et les justifications détaillées, sources de bruit.

import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { csvParse } from 'd3-dsv';
import { DROITS } from '$lib/droits';
import { circonscription, legislature, SENS } from '$lib/format';
import type { EcarteIndex, PaysIndex, Texte, TexteIndex } from '$lib/types';
import { donnees, EXPORT } from './donnees';
import { vueCirco } from './vues';

/** Termes et surnoms d'un texte, par `id` de qualification ou par dossier. */
function clesParTexte(): Map<string, string[]> {
  const out = new Map<string, string[]>();
  for (const l of csvParse(readFileSync(resolve(EXPORT, 'termes_recherche.csv'), 'utf8')))
    out.set(l.cle!, [...(out.get(l.cle!) ?? []), l.terme!]);
  return out;
}

function detailTexte(t: Texte): string {
  const droit = t.principal ? `${DROITS[t.principal.code].court} : ${SENS[t.principal.sens]}` : '';
  const ou = t.seul ? 'vote du seul Sénat' : `${legislature(t.legislature)} législature`;
  return droit ? `${droit}, ${ou}` : ou;
}

export function indexTextes(): { textes: TexteIndex[]; ecartes: EcarteIndex[] } {
  const d = donnees();
  const cles = clesParTexte();
  const qualifies = [...d.textes, ...d.seuls].map((t): TexteIndex => ({
    id: t.id,
    titre: t.titre,
    resume: t.resume,
    etiquettes: t.etiquettes,
    cles: cles.get(t.id) ?? [],
    date: t.date,
    detail: detailTexte(t),
    url: `/textes/${t.id}`
  }));
  const suivis = d.enCoursTous.flatMap((t): TexteIndex[] =>
    t.suivi
      ? [
          {
            id: t.id,
            titre: t.titre,
            resume: t.suivi.resume ?? '',
            etiquettes: [],
            cles: cles.get(t.id) ?? [],
            date: '',
            detail: 'À suivre, pas encore voté',
            url: `/en-cours#${t.id}`
          }
        ]
      : []
  );
  const ecartes = d.ecartes.map((e): EcarteIndex => ({
    dossier: e.dossier_an,
    titre: e.titre,
    motif: e.motif,
    legislature: e.legislature,
    url: e.url_an,
    cles: cles.get(e.dossier_an) ?? []
  }));
  return { textes: [...qualifies, ...suivis], ecartes };
}

export function indexPays(): PaysIndex[] {
  return csvParse(readFileSync(resolve(EXPORT, 'pays_circonscriptions.csv'), 'utf8')).map((l) => {
    const num = Number(l.circo!.slice(-2));
    return {
      pays: l.pays!,
      alias: l.alias ? l.alias.split('|') : [],
      circo: l.circo!,
      libelle: `Français établis hors de France, ${circonscription(num)}`,
      hors_tableau: l.hors_tableau === 'oui',
      depute: vueCirco(l.circo!).actuel?.depute ?? null
    };
  });
}
