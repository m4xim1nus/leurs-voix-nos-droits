// Données du Sénat (data/export/senat/, règles 23 à 28), à part de celles de l'Assemblée : aucune
// page ne mélange les deux chambres. Rien n'est calculé ici : les scores viennent de `lvnd scores`.

import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { csvParse } from 'd3-dsv';
import { slug, typo } from '$lib/format';
import type {
  GroupeCourt,
  Position,
  PositionGroupe,
  Pour,
  RoleSenat,
  Score,
  ScrutinSenat,
  Senateur,
  Source,
  VersionSenat,
  VoteSenat
} from '$lib/types';

const SENAT = resolve(process.cwd(), '../data/export/senat');
/** Pas de couleur officielle ni de correspondance avec les groupes de l'Assemblée (règle 28). */
const COULEUR = 'var(--ardoise)';
const ENSEMBLE = new Set(['ensemble', 'article_unique']);
const CODES: Record<string, Position> = {
  P: 'pour',
  C: 'contre',
  A: 'abstention',
  N: 'non_votant'
};

type Ligne = Record<string, string | undefined>;
const lire = (chemin: string): Ligne[] =>
  csvParse(readFileSync(resolve(SENAT, `${chemin}.csv`), 'utf8'));
const txt = (v: string | undefined) => (v === undefined || v === '' ? null : v);
const num = (v: string | undefined) => (v === undefined || v === '' ? null : Number(v));

export interface VoteNominatif {
  position: Position;
  delegue_a: string | null;
  statut: string | null;
}

export interface BaseSenat {
  groupes: GroupeCourt[];
  groupe: Map<string, GroupeCourt>;
  senateurs: Senateur[];
  senateurParId: Map<string, Senateur>;
  scoresSenateurs: Map<string, Map<string, Score>>;
  scoresGroupes: Map<string, Map<string, Score>>;
  scoresSenateursTextes: Map<string, Map<string, Score>>;
  scoresGroupesTextes: Map<string, Map<string, Score>>;
  scrutins: Map<string, Ligne>;
  parDossier: Map<string, Ligne[]>;
  comptes: Map<string, Ligne>;
  /** Votes nominatifs des décisifs comptés : scrutin → sénateur → vote. */
  votes: () => Map<string, Map<string, VoteNominatif>>;
  ventilations: (id: string) => ScrutinSenat['ventilations'];
  misesAuPoint: Map<string, { texte: string; url: string | null }[]>;
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

function indexer(nom: string, cle: string, sous: string): Map<string, Map<string, Score>> {
  const out = new Map<string, Map<string, Score>>();
  for (const r of lire(nom)) {
    if (!out.has(r[cle]!)) out.set(r[cle]!, new Map());
    out.get(r[cle]!)!.set(r[sous]!, score(r));
  }
  return out;
}

function chargerBase(): BaseSenat {
  const groupes: GroupeCourt[] = lire('groupes').map((g) => ({
    id: g.id!,
    sigle: g.sigle!,
    nom: g.nom!,
    couleur: COULEUR
  }));
  const groupe = new Map(groupes.map((g) => [g.id, g]));
  const appart = new Map<string, Senateur['groupes']>();
  for (const a of lire('appartenances')) {
    const g = groupe.get(a.groupe_id!);
    if (!g) continue;
    appart.set(a.senateur_id!, [
      ...(appart.get(a.senateur_id!) ?? []),
      { groupe: g, debut: txt(a.debut), fin: txt(a.fin) }
    ]);
  }
  const mandats = new Map<string, Senateur['mandats']>();
  for (const m of lire('mandats'))
    mandats.set(m.senateur_id!, [
      ...(mandats.get(m.senateur_id!) ?? []),
      { debut: m.debut!, fin: txt(m.fin) }
    ]);
  const rows = lire('senateurs');
  const base = new Map<string, number>();
  for (const s of rows) {
    const k = slug(`${s.prenom} ${s.nom}`);
    base.set(k, (base.get(k) ?? 0) + 1);
  }
  const senateurs: Senateur[] = rows.map((s) => {
    const k = slug(`${s.prenom} ${s.nom}`);
    return {
      id: s.id!,
      slug: base.get(k)! > 1 ? `${k}-${s.id!.toLowerCase()}` : k,
      civ: s.civ!,
      prenom: s.prenom!,
      nom: s.nom!,
      tri: slug(`${s.nom} ${s.prenom}`),
      actuel: s.etat === 'actif',
      circonscription: s.circonscription!,
      departement: s.departement!,
      courriel: txt(s.courriel),
      groupes: (appart.get(s.id!) ?? []).sort((a, b) =>
        (b.debut ?? '').localeCompare(a.debut ?? '')
      ),
      mandats: (mandats.get(s.id!) ?? []).sort((a, b) => b.debut.localeCompare(a.debut))
    };
  });

  const scrutins = new Map(lire('scrutins').map((s) => [s.id!, s]));
  const parDossier = new Map<string, Ligne[]>();
  for (const s of scrutins.values())
    if (s.dossier_id) parDossier.set(s.dossier_id, [...(parDossier.get(s.dossier_id) ?? []), s]);
  const comptes = new Map(
    lire('scores_scrutins')
      .filter((c) => c.droit === 'global')
      .map((c) => [`${c.texte_id}\t${c.scrutin_id}`, c])
  );

  const parScrutin = new Map<string, ScrutinSenat['ventilations']>();
  for (const p of lire('positions_groupes')) {
    const g = groupe.get(p.groupe_id!);
    if (!g) continue;
    const v = {
      groupe: g,
      membres: Number(p.membres),
      pour: Number(p.pour),
      contre: Number(p.contre),
      abstention: Number(p.abstention),
      non_votants: Number(p.non_votants),
      position: p.position as PositionGroupe,
      cohesion: num(p.cohesion)
    };
    if (!parScrutin.has(p.scrutin_id!)) parScrutin.set(p.scrutin_id!, []);
    parScrutin.get(p.scrutin_id!)!.push(v);
  }
  const misesAuPoint = new Map<string, { texte: string; url: string | null }[]>();
  for (const m of lire('mises_au_point'))
    misesAuPoint.set(m.scrutin_id!, [
      ...(misesAuPoint.get(m.scrutin_id!) ?? []),
      { texte: typo(m.texte!), url: txt(m.url) }
    ]);

  let cache: Map<string, Map<string, VoteNominatif>> | null = null;
  const votes = () => {
    if (cache) return cache;
    const ids = new Set([...comptes.values()].map((c) => c.scrutin_id!));
    cache = new Map([...ids].map((i) => [i, new Map()]));
    for (const mois of new Set([...ids].map((i) => scrutins.get(i)!.date!.slice(0, 7))))
      for (const v of lire(`votes/${mois}`)) {
        const m = cache.get(`SN${v.scrutin}`);
        if (m)
          m.set(v.senateur!, {
            position: CODES[v.position!],
            delegue_a: txt(v.delegue_a),
            statut: txt(v.statut)
          });
      }
    return cache;
  };

  return {
    groupes,
    groupe,
    senateurs,
    senateurParId: new Map(senateurs.map((s) => [s.id, s])),
    scoresSenateurs: indexer('scores_senateurs', 'senateur_id', 'droit'),
    scoresGroupes: indexer('scores_groupes', 'groupe_id', 'droit'),
    scoresSenateursTextes: indexer('scores_senateurs_textes', 'senateur_id', 'texte_id'),
    scoresGroupesTextes: indexer('scores_groupes_textes', 'groupe_id', 'texte_id'),
    scrutins,
    parDossier,
    comptes,
    votes,
    ventilations: (id) => [...(parScrutin.get(id) ?? [])].sort((a, b) => b.membres - a.membres),
    misesAuPoint
  };
}

let cache: BaseSenat | null = null;

export function baseSenat(): BaseSenat {
  cache ??= chargerBase();
  return cache;
}

/** Le bloc `senat` d'une entrée d'editorial.json. */
export interface BlocSenat {
  version: VersionSenat;
  scrutins: { id: string; role: RoleSenat; pour: Pour; objet: string }[];
  droits: VoteSenat['droits'];
  etiquettes: string[];
  vigilance: { texte: string; sources: string[] }[];
  sources: Record<string, Omit<Source, 'id'>>;
  note: string;
}

const ORDRE: RoleSenat[] = ['decisif', 'ensemble', 'motion'];
const rang = (s: Ligne) => `${s.date}\t${String(s.numero).padStart(6, '0')}`;

/** Dernier vote du Sénat sur l'ensemble d'un dossier, s'il y en a un. */
export function dernierVoteEnsemble(b: BaseSenat, dossier: string) {
  const l = (b.parDossier.get(dossier) ?? [])
    .filter((x) => ENSEMBLE.has(x.objet!))
    .sort((x, y) => rang(x).localeCompare(rang(y)))
    .at(-1);
  return l ? { date: l.date!, pour: Number(l.pour), contre: Number(l.contre), url: l.url! } : null;
}

/** Vote du Sénat d'un texte qualifié, tel qu'il s'affiche sur sa fiche. */
export function voteSenat(b: BaseSenat, idTexte: string, dossier: string, s: BlocSenat): VoteSenat {
  const scrutins: ScrutinSenat[] = s.scrutins
    .map((r): ScrutinSenat => {
      const l = b.scrutins.get(r.id)!;
      const c = b.comptes.get(`${idTexte}\t${r.id}`);
      return {
        id: r.id,
        numero: Number(l.numero),
        role: r.role,
        pour: r.pour,
        objet: typo(r.objet),
        date: l.date!,
        lecture: txt(l.lecture),
        sort: l.sort as 'adopte' | 'rejete',
        decompte: {
          pour: Number(l.pour),
          contre: Number(l.contre),
          abstention: Number(l.abstention),
          requis: num(l.requis)
        },
        compte: c !== undefined && c.favorable !== '',
        favorable: (txt(c?.favorable) as 'pour' | 'contre' | null) ?? null,
        ventilations: b.ventilations(r.id),
        url: l.url!,
        note: txt(l.note),
        mises_au_point: b.misesAuPoint.get(r.id) ?? []
      };
    })
    .sort((x, y) => ORDRE.indexOf(x.role) - ORDRE.indexOf(y.role) || y.date.localeCompare(x.date));
  // Règle 25 : un vote sur l'ensemble postérieur à ceux qui sont retenus attend sa relecture.
  const retenus = s.scrutins.map((r) => b.scrutins.get(r.id)!);
  const dernier = retenus.map(rang).sort().at(-1) ?? '';
  const nouveau = (b.parDossier.get(dossier) ?? [])
    .filter(
      (l) => ENSEMBLE.has(l.objet!) && rang(l) > dernier && !s.scrutins.some((r) => r.id === l.id)
    )
    .sort((x, y) => rang(x).localeCompare(rang(y)))
    .at(-1);
  const droits = s.droits.map((d) => ({ ...d, justification: typo(d.justification) }));
  return {
    version: s.version,
    scrutins,
    decisif: scrutins.find((x) => x.role === 'decisif' && x.compte) ?? null,
    droits,
    principal: droits.find((d) => d.role === 'principal') ?? null,
    etiquettes: s.etiquettes,
    vigilance: s.vigilance.map((v) => ({ ...v, texte: typo(v.texte) })),
    sources: Object.fromEntries(
      Object.entries(s.sources).map(([id, x]) => [id, { ...x, id, titre: typo(x.titre) }])
    ),
    note: typo(s.note),
    nouveau: nouveau
      ? {
          id: nouveau.id!,
          date: nouveau.date!,
          pour: Number(nouveau.pour),
          contre: Number(nouveau.contre),
          url: nouveau.url!
        }
      : null
  };
}
