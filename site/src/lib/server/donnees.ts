// Lecture des données au prérendu (Node) : data/export/ (open data et scores recalculés par
// `lvnd scores`), data/editorial.json (qualifications publiées) et data/annuaire/. Rien de ce
// module n'est envoyé au navigateur : chaque page reçoit seulement ce que sa fonction `load` en
// extrait. Aucun score n'est calculé ici (docs/CONCEPTION.md, choix F1).

import { existsSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { csvParse } from 'd3-dsv';
import { DROITS } from '$lib/droits';
import { slug, typo } from '$lib/format';
import type {
  Appartenance,
  Depute,
  Droit,
  Ecarte,
  GroupeCourt,
  Lignee,
  Mandat,
  Participation,
  Position,
  PositionGroupe,
  Score,
  ScrutinRetenu,
  Texte,
  TexteUnanime,
  Ventilation
} from '$lib/types';

/** Racine du dépôt, relative à site/ (cwd de vite). */
export const RACINE = resolve(process.cwd(), '..');
export const EXPORT = resolve(RACINE, 'data/export');
const ANNUAIRE = resolve(RACINE, 'data/annuaire');
const EDITORIAL = resolve(RACINE, 'data/editorial.json');

type Ligne = Record<string, string | undefined>;

const lire = (chemin: string): Ligne[] => csvParse(readFileSync(chemin, 'utf8'));
const exp = (nom: string) => lire(resolve(EXPORT, `${nom}.csv`));
const txt = (v: string | undefined) => (v === undefined || v === '' ? null : v);
const num = (v: string | undefined) => (v === undefined || v === '' ? null : Number(v));

export const circoId = (dep: string, n: number) => `${dep}-${String(n).padStart(2, '0')}`;
export const urlScrutin = (leg: number, numero: number) =>
  `https://www.assemblee-nationale.fr/dyn/${leg}/scrutins/${numero}`;

/** Motif d'écart d'un texte dont le décisif n'a eu aucune voix contre (ou pour). */
export const SANS_OPPOSITION = /sans aucune voix (contre|pour) au scrutin décisif/i;

export interface Donnees {
  genereLe: string;
  droits: Droit[];
  /** Textes qualifiés, du plus récent au plus ancien (date du vote décisif). */
  textes: Texte[];
  ecartes: Ecarte[];
  /** Textes écartés faute d'opposition au décisif (règle 9), avec ce scrutin. */
  unanimes: TexteUnanime[];
  lignees: Lignee[];
  ligneeDe: Map<string, Lignee>;
  groupe: Map<string, GroupeCourt>;
  deputes: Depute[];
  deputeParId: Map<string, Depute>;
  scoresDeputes: Map<string, Map<string, Score>>;
  scoresGroupes: Map<string, Map<string, Score>>;
  scoresDeputesTextes: Map<string, Map<string, Score>>;
  scoresGroupesTextes: Map<string, Map<string, Score>>;
  participation: Map<string, Participation>;
  /** Votes nominatifs des scrutins retenus : scrutin → député → position. */
  votes: Map<string, Map<string, Position>>;
}

function score(r: Ligne): Score {
  return {
    n_textes: Number(r.n_textes ?? 1),
    favorables: Number(r.votes_favorables),
    defavorables: Number(r.votes_defavorables),
    abstentions: Number(r.abstentions),
    non_votants: Number(r.non_votants),
    score: num(r.score)
  };
}

function indexer(lignes: Ligne[], cle: string, sous: string): Map<string, Map<string, Score>> {
  const out = new Map<string, Map<string, Score>>();
  for (const r of lignes) {
    const k = r[cle]!;
    if (!out.has(k)) out.set(k, new Map());
    out.get(k)!.set(r[sous]!, score(r));
  }
  return out;
}

function groupes() {
  const rows = exp('groupes');
  const groupe = new Map<string, GroupeCourt>(
    rows.map((g) => [g.id!, { id: g.id!, sigle: g.sigle!, nom: g.nom!, couleur: g.couleur! }])
  );
  const lignees: Lignee[] = rows
    .filter((g) => g.id === g.lignee)
    .map((g) => ({
      ...groupe.get(g.id!)!,
      legislature: Number(g.legislature),
      slug: `${slug(g.sigle!)}-${g.legislature}`,
      organes: rows.filter((x) => x.lignee === g.id).map((x) => x.id!),
      actif: !g.date_fin
    }));
  const ligneeDe = new Map<string, Lignee>();
  for (const l of lignees) for (const o of l.organes) ligneeDe.set(o, l);
  return { groupe, lignees, ligneeDe };
}

function deputes(groupe: Map<string, GroupeCourt>): Depute[] {
  const contacts = new Map(
    lire(resolve(ANNUAIRE, 'contacts.csv')).map((c) => [c.acteur_id!, c] as const)
  );
  const mandats = new Map<string, Mandat[]>();
  for (const m of exp('mandats')) {
    const l = mandats.get(m.acteur_id!) ?? [];
    l.push({
      legislature: Number(m.legislature),
      departement: m.departement!,
      circo: circoId(m.num_departement!, Number(m.num_circo)),
      num_circo: Number(m.num_circo),
      debut: m.debut!,
      fin: txt(m.fin),
      cause_fin: txt(m.cause_fin)
    });
    mandats.set(m.acteur_id!, l);
  }
  const appart = new Map<string, Appartenance[]>();
  for (const a of exp('appartenances')) {
    const g = groupe.get(a.groupe_id!);
    if (!g) continue;
    const l = appart.get(a.acteur_id!) ?? [];
    l.push({
      groupe: g,
      legislature: Number(a.legislature),
      debut: a.debut!,
      fin: txt(a.fin),
      qualite: a.qualite!
    });
    appart.set(a.acteur_id!, l);
  }
  const rows = exp('deputes');
  const base = new Map<string, number>();
  for (const d of rows) {
    const s = slug(`${d.prenom} ${d.nom}`);
    base.set(s, (base.get(s) ?? 0) + 1);
  }
  return rows.map((d) => {
    const s = slug(`${d.prenom} ${d.nom}`);
    const c = contacts.get(d.id!);
    return {
      id: d.id!,
      slug: base.get(s)! > 1 ? `${s}-${d.id!.toLowerCase()}` : s,
      civ: d.civ!,
      prenom: d.prenom!,
      nom: d.nom!,
      nom_tri: d.nom_tri!,
      mandats: (mandats.get(d.id!) ?? []).sort((a, b) => b.debut.localeCompare(a.debut)),
      groupes: (appart.get(d.id!) ?? []).sort((a, b) => b.debut.localeCompare(a.debut)),
      courriel: txt(c?.courriel),
      site: txt(c?.site)
    };
  });
}

const CODES: Record<string, Position> = {
  P: 'pour',
  C: 'contre',
  A: 'abstention',
  N: 'non_votant'
};

/** Votes nominatifs des scrutins donnés, depuis votes/<législature>/<AAAA-MM>.csv. */
function votes(scrutins: Ligne[]): Map<string, Map<string, Position>> {
  const out = new Map<string, Map<string, Position>>();
  const parFichier = new Map<string, Map<string, string>>();
  for (const s of scrutins) {
    const f = `votes/${s.legislature}/${s.date!.slice(0, 7)}.csv`;
    if (!parFichier.has(f)) parFichier.set(f, new Map());
    parFichier.get(f)!.set(s.numero!, s.id!);
    out.set(s.id!, new Map());
  }
  for (const [f, ids] of parFichier)
    for (const v of lire(resolve(EXPORT, f))) {
      const id = ids.get(v.scrutin!);
      if (id) out.get(id)!.set(`PA${v.acteur}`, CODES[v.position!]);
    }
  return out;
}

function charger(): Donnees {
  const meta = JSON.parse(readFileSync(resolve(EXPORT, 'meta.json'), 'utf8'));
  const editorial = JSON.parse(readFileSync(EDITORIAL, 'utf8'));
  const droits: Droit[] = meta.referentiels.droits.droits.map(
    (d: { code: string; libelle: string }) => ({ ...d, court: DROITS[d.code]?.court ?? d.code })
  );
  const { groupe, lignees, ligneeDe } = groupes();
  const deps = deputes(groupe);
  const deputeParId = new Map(deps.map((d) => [d.id, d]));
  const catalogue = new Map(exp('textes').map((t) => [t.id!, t]));

  // Textes écartés parce que leur décisif n'a eu aucune voix d'un côté (règle 9) : affichés sur
  // les fiches, hors des scores. Le motif, écrit par l'admin, suit toujours ce modèle.
  const ecartesBruts: Ecarte[] = editorial.ecartes ?? [];
  const unanimesBruts = ecartesBruts.flatMap((e) => {
    const s = catalogue.get(e.dossier_an)?.decisif_propose;
    return SANS_OPPOSITION.test(e.motif) && s ? [{ e, scrutin: s }] : [];
  });
  const retenus = new Set<string>([
    ...editorial.textes.flatMap((t: { scrutins: { id: string }[] }) => t.scrutins.map((s) => s.id)),
    ...unanimesBruts.map((u) => u.scrutin)
  ]);
  const scrutins = new Map(
    exp('scrutins')
      .filter((s) => retenus.has(s.id!))
      .map((s) => [s.id!, s])
  );
  const amendementIds = new Set([...scrutins.values()].map((s) => s.amendement_id).filter(Boolean));
  const amendements = new Map(
    exp('amendements')
      .filter((a) => amendementIds.has(a.id))
      .map((a) => [a.id!, a])
  );
  const ventilations = new Map<string, Ventilation[]>();
  for (const p of exp('positions_groupes')) {
    if (!retenus.has(p.scrutin_id!)) continue;
    const l = ventilations.get(p.scrutin_id!) ?? [];
    l.push({
      groupe: groupe.get(p.groupe_id!)!,
      membres: Number(p.membres),
      pour: Number(p.pour),
      contre: Number(p.contre),
      abstention: Number(p.abstention),
      non_votants: Number(p.non_votants),
      position: p.position as PositionGroupe,
      cohesion: num(p.cohesion)
    });
    ventilations.set(p.scrutin_id!, l);
  }
  // Poids et position favorable de chaque scrutin compté, au sens du droit principal.
  const comptes = new Map(
    exp('scores_scrutins')
      .filter((c) => c.droit === 'global')
      .map((c) => [`${c.texte_id}\t${c.scrutin_id}`, c])
  );

  const ORDRE = ['decisif', 'amendement', 'censure', 'ensemble', 'article', 'motion'];
  const textes: Texte[] = editorial.textes.map((t: Texte) => {
    const cat = catalogue.get(t.dossier_an);
    const retenus: ScrutinRetenu[] = t.scrutins.map((r) => {
      const s = scrutins.get(r.id)!;
      const c = comptes.get(`${t.id}\t${r.id}`);
      const a = s.amendement_id ? amendements.get(s.amendement_id) : undefined;
      const auteur = a?.auteur_id ? deputeParId.get(a.auteur_id) : undefined;
      return {
        id: r.id,
        numero: Number(s.numero),
        legislature: Number(s.legislature),
        role: r.role,
        pour: r.pour,
        objet: typo(r.objet),
        date: s.date!,
        sort: s.sort as 'adopte' | 'rejete',
        decompte: {
          pour: Number(s.pour),
          contre: Number(s.contre),
          abstention: Number(s.abstention),
          requis: num(s.requis)
        },
        compte: c !== undefined && c.favorable !== '',
        poids: c ? Number(c.poids) : 0,
        favorable: (txt(c?.favorable) as 'pour' | 'contre' | null) ?? null,
        amendement: a
          ? {
              numero: a.numero!,
              division: a.division!,
              auteur: auteur ? `${auteur.prenom} ${auteur.nom}` : null,
              groupe: a.groupe_id ? (groupe.get(a.groupe_id)?.sigle ?? null) : null,
              sort: a.sort!
            }
          : null,
        ventilations: (ventilations.get(r.id) ?? []).sort((x, y) => y.membres - x.membres),
        url: urlScrutin(Number(s.legislature), Number(s.numero))
      };
    });
    retenus.sort(
      (a, b) => ORDRE.indexOf(a.role) - ORDRE.indexOf(b.role) || a.date.localeCompare(b.date)
    );
    const decisif = retenus.find((s) => s.role === 'decisif');
    const censures = retenus.filter((s) => s.role === 'censure').map((s) => s.date);
    return {
      ...t,
      titre: typo(t.titre),
      resume: typo(t.resume),
      droits: t.droits.map((d) => ({ ...d, justification: typo(d.justification) })),
      vigilance: t.vigilance.map((v) => ({ ...v, texte: typo(v.texte) })),
      conseil_constitutionnel: typo(t.conseil_constitutionnel),
      note: typo(t.note),
      sources: Object.fromEntries(
        Object.entries(t.sources).map(([id, s]) => [id, { ...s, id, titre: typo(s.titre) }])
      ),
      principal: t.droits.find((d) => d.role === 'principal')!,
      scrutins: retenus,
      date: decisif?.date ?? censures.sort().at(-1)!,
      // Législature du vote décisif : un dossier déposé en XVIe peut n'avoir été voté qu'en XVIIe.
      legislature: decisif?.legislature ?? t.legislature,
      sans_vote: !decisif,
      loi: txt(cat?.loi),
      date_loi: txt(cat?.date_loi),
      url_an: txt(cat?.url_an),
      url_loi: txt(cat?.url_loi),
      cc_decision: txt(cat?.cc_decision),
      cc_url: txt(cat?.cc_url)
    };
  });
  textes.sort((a, b) => b.date.localeCompare(a.date));

  const ecartes: Ecarte[] = ecartesBruts.map((e) => ({
    ...e,
    titre: typo(e.titre),
    motif: typo(e.motif),
    url_an: txt(catalogue.get(e.dossier_an)?.url_an)
  }));
  const unanimes: TexteUnanime[] = unanimesBruts
    .flatMap(({ e, scrutin }) => {
      const s = scrutins.get(scrutin);
      if (!s) return [];
      return [
        {
          dossier_an: e.dossier_an,
          titre: typo(e.titre),
          url_an: txt(catalogue.get(e.dossier_an)?.url_an),
          scrutin: {
            id: s.id!,
            date: s.date!,
            pour: Number(s.pour),
            contre: Number(s.contre),
            url: urlScrutin(Number(s.legislature), Number(s.numero))
          },
          ventilations: ventilations.get(s.id!) ?? []
        }
      ];
    })
    .sort((a, b) => b.scrutin.date.localeCompare(a.scrutin.date));

  const participation = new Map<string, Participation>(
    (existsSync(resolve(EXPORT, 'participation.csv')) ? exp('participation') : []).map((p) => [
      p.acteur_id!,
      {
        scrutins: Number(p.scrutins),
        votes: Number(p.votes),
        non_votants: Number(p.non_votants),
        taux: Number(p.taux)
      }
    ])
  );

  return {
    genereLe: meta.genere_le,
    droits,
    textes,
    ecartes,
    unanimes,
    lignees,
    ligneeDe,
    groupe,
    deputes: deps,
    deputeParId,
    scoresDeputes: indexer(exp('scores_deputes'), 'acteur_id', 'droit'),
    scoresGroupes: indexer(exp('scores_groupes'), 'lignee', 'droit'),
    scoresDeputesTextes: indexer(exp('scores_deputes_textes'), 'acteur_id', 'texte_id'),
    scoresGroupesTextes: indexer(exp('scores_groupes_textes'), 'lignee', 'texte_id'),
    participation,
    votes: votes([...scrutins.values()])
  };
}

let cache: Donnees | null = null;

/** Toutes les données, lues une seule fois par build. */
export function donnees(): Donnees {
  cache ??= charger();
  return cache;
}
