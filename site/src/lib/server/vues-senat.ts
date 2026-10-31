// Ce que reçoivent les pages du Sénat (règles 26 à 28). Aucun taux de participation : presque tous les
// sièges ont un vote enregistré, qui ne dit pas qui était présent (règle 27).

import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { csvParse } from 'd3-dsv';
import { error } from '@sveltejs/kit';
import type {
  EntreeIndex,
  GroupeCourt,
  Position,
  PositionGroupe,
  Score,
  ScrutinSenat,
  Senateur,
  Sens,
  Texte
} from '$lib/types';
import { donnees, RACINE } from './donnees';
import { baseSenat } from './senat';

const groupeDuJour = (s: Senateur, date: string): GroupeCourt | null =>
  s.groupes.find((g) => (g.debut ?? '') <= date && (g.fin === null || date <= g.fin))?.groupe ??
  null;

function textesComptes(): { texte: Texte; scrutin: ScrutinSenat }[] {
  const d = donnees();
  return [...d.textes, ...d.seuls].flatMap((t) =>
    t.senat?.decisif ? [{ texte: t, scrutin: t.senat.decisif }] : []
  );
}

export function indexSenateurs(): EntreeIndex[] {
  return baseSenat()
    .senateurs.map((s) => ({
      slug: s.slug,
      nom: `${s.prenom} ${s.nom}`,
      feminin: s.civ === 'Mme',
      tri: s.tri,
      circo: s.departement,
      departement: s.circonscription,
      sigle: s.groupes[0]?.groupe.sigle ?? '',
      couleur: s.groupes[0]?.groupe.couleur ?? '',
      actuel: s.actuel,
      senat: true
    }))
    .sort((a, b) => a.tri.localeCompare(b.tri, 'fr'));
}

let parPrefixe: Map<string, Record<string, string[]>> | null = null;

/** Code postal → départements, par préfixe à deux chiffres (data/annuaire/cp_departements.csv). */
function tablesDepartements() {
  if (parPrefixe) return parPrefixe;
  parPrefixe = new Map();
  const lignes = csvParse(
    readFileSync(resolve(RACINE, 'data/annuaire/cp_departements.csv'), 'utf8')
  );
  for (const l of lignes) {
    const p = l.cp!.slice(0, 2);
    if (!parPrefixe.has(p)) parPrefixe.set(p, {});
    (parPrefixe.get(p)![l.cp!] ??= []).push(l.departement!);
  }
  return parPrefixe;
}

export const prefixesDepartements = () => [...tablesDepartements().keys()].sort();
export const tableDepartements = (prefixe: string) => tablesDepartements().get(prefixe) ?? null;

export function vueSenat() {
  const d = donnees();
  const b = baseSenat();
  const groupes = b.groupes
    .filter((g) => b.scoresGroupes.has(g.id))
    .map((g) => ({
      groupe: g,
      global: b.scoresGroupes.get(g.id)!.get('global') ?? null,
      droits: Object.fromEntries(
        d.droits.map((dr) => [dr.code, b.scoresGroupes.get(g.id)!.get(dr.code) ?? null])
      )
    }))
    .sort((x, y) => (y.global?.score ?? -1) - (x.global?.score ?? -1));
  const parDepartement = new Map<
    string,
    { code: string; nom: string; senateurs: (EntreeIndex & { score: Score | null })[] }
  >();
  const index = new Map(indexSenateurs().map((e) => [e.slug, e]));
  for (const s of b.senateurs) {
    if (!s.actuel) continue;
    const c = parDepartement.get(s.departement) ?? {
      code: s.departement,
      nom: s.circonscription,
      senateurs: []
    };
    c.senateurs.push({
      ...index.get(s.slug)!,
      score: b.scoresSenateurs.get(s.id)?.get('global') ?? null
    });
    parDepartement.set(s.departement, c);
  }
  return {
    droits: d.droits,
    groupes,
    n_textes: textesComptes().length,
    departements: [...parDepartement.values()]
      .map((c) => ({ ...c, senateurs: c.senateurs.sort((x, y) => x.tri.localeCompare(y.tri)) }))
      .sort((x, y) => x.code.localeCompare(y.code))
  };
}

export interface VoteSenateur {
  /** Le droit principal de la version votée au Sénat, pas forcément celui de l'Assemblée (règle 24). */
  texte: { id: string; titre: string; seul: boolean; principal: { code: string; sens: Sens } };
  scrutin: Pick<ScrutinSenat, 'id' | 'objet' | 'date' | 'url' | 'favorable'>;
  position: Position;
  delegue_a: { nom: string; slug: string } | null;
  statut: string | null;
  groupe: GroupeCourt | null;
  position_groupe: PositionGroupe | null;
  /** A voté pour quand son groupe votait majoritairement contre, ou l'inverse. */
  ecart: boolean;
  score: Score | null;
}

export function vueSenateur(slug: string) {
  const d = donnees();
  const b = baseSenat();
  const s = b.senateurs.find((x) => x.slug === slug);
  if (!s) error(404, 'Sénateur·ice inconnu·e');
  const votes: VoteSenateur[] = textesComptes().flatMap(({ texte, scrutin }) => {
    const v = b.votes().get(scrutin.id)?.get(s.id);
    if (!v) return [];
    const groupe = groupeDuJour(s, scrutin.date);
    const pos = groupe
      ? (scrutin.ventilations.find((x) => x.groupe.id === groupe.id)?.position ?? null)
      : null;
    const delegue = v.delegue_a ? b.senateurParId.get(v.delegue_a) : undefined;
    return [
      {
        texte: {
          id: texte.id,
          titre: texte.titre,
          seul: texte.seul,
          principal: {
            code: (texte.senat?.principal ?? texte.principal).code,
            sens: (texte.senat?.principal ?? texte.principal).sens
          }
        },
        scrutin: {
          id: scrutin.id,
          objet: scrutin.objet,
          date: scrutin.date,
          url: scrutin.url,
          favorable: scrutin.favorable
        },
        position: v.position,
        delegue_a: delegue ? { nom: `${delegue.prenom} ${delegue.nom}`, slug: delegue.slug } : null,
        statut: v.statut,
        groupe,
        position_groupe: pos,
        ecart:
          (v.position === 'pour' || v.position === 'contre') &&
          (pos === 'pour' || pos === 'contre') &&
          v.position !== pos,
        score: b.scoresSenateursTextes.get(s.id)?.get(texte.id) ?? null
      }
    ];
  });
  votes.sort((x, y) => y.scrutin.date.localeCompare(x.scrutin.date));
  const scores = b.scoresSenateurs.get(s.id) ?? new Map<string, Score>();
  const actuel = s.groupes.find((g) => g.fin === null)?.groupe ?? null;
  return {
    senateur: s,
    groupeActuel: actuel,
    global: scores.get('global') ?? null,
    droits: d.droits.flatMap((dr) => {
      const x = scores.get(dr.code);
      return x ? [{ droit: dr, score: x }] : [];
    }),
    votes,
    ecarts: votes.filter((v) => v.ecart),
    scoreGroupe: actuel ? (b.scoresGroupes.get(actuel.id)?.get('global') ?? null) : null
  };
}

export const slugsSenateurs = () => baseSenat().senateurs.map((s) => ({ slug: s.slug }));
