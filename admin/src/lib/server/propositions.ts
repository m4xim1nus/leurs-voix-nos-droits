// Propositions du LLM (ROADMAP, cycle Pré-qualification, items 5 et 6) : lues dans D1, chargées ou écartées
// par un humain. Une proposition ne touche jamais une qualification tant qu'on ne la charge pas ; chargée,
// la qualification passe « à relire », et la version publiée reste en ligne jusqu'à sa validation.

import { normaliser } from '../qualification';
import type { Qualification, Statut } from '../types';
import { enregistrer, qualification } from './db';

export type StatutProposition = 'proposee' | 'echec' | 'chargee' | 'ecartee';

export interface Relecture {
  /** Une phrase du LLM au relecteur : ce qu'il propose de faire, et quoi vérifier d'abord. */
  action?: string;
  points_attention?: string[];
  extraits?: string[];
  incertitudes?: string[];
  signataires?: Record<string, string[]>;
  origine?: string;
  echec?: string;
  controles?: { erreurs: string[]; avertissements: string[]; points: string[] };
  documents_lus?: string[];
  /** Veille des sources : la publication qui a déclenché la proposition. */
  publication?: { auteur: string; titre: string; lien: string; date: string; raison?: string };
  /** La question de méthode soulevée a été tranchée (docs/METHODO.md) : la carte quitte cette section. */
  methode_tranchee?: { par: string; le: string };
}

/** Brouillon proposé : une entrée d'editorial.json, plus `statut` et `motif_ecart`. */
export type DocPropose = Partial<Qualification> & {
  dossier_an: string;
  statut?: 'a-relire' | 'ecarte' | 'a-suivre' | 'sans-source';
  motif_ecart?: string | null;
};

export interface Proposition {
  id: number;
  alerte_id: string;
  dossier_an: string;
  mode: string;
  date: string;
  modele: string;
  cout_usd: number;
  doc: DocPropose | null;
  relecture: Relecture;
  statut: StatutProposition;
  motif: string | null;
  traite_par: string | null;
  traite_le: string | null;
}

interface Ligne extends Omit<Proposition, 'doc' | 'relecture'> {
  doc: string | null;
  relecture: string | null;
}

function lire(l: Ligne): Proposition {
  let doc: DocPropose | null = null;
  let relecture: Relecture = {};
  try {
    doc = l.doc ? (JSON.parse(l.doc) as DocPropose) : null;
    relecture = l.relecture ? (JSON.parse(l.relecture) as Relecture) : {};
  } catch {
    relecture = { echec: 'proposition illisible dans D1' };
  }
  return { ...l, doc, relecture };
}

/** Propositions en attente d'un geste (proposées ou en échec), les plus récentes d'abord. */
export async function propositionsOuvertes(db: D1Database): Promise<Proposition[]> {
  const { results } = await db
    .prepare(
      "SELECT * FROM propositions WHERE statut IN ('proposee', 'echec') ORDER BY date DESC, id DESC"
    )
    .all<Ligne>();
  return results.map(lire);
}

export async function propositionsDuTexte(db: D1Database, id: string): Promise<Proposition[]> {
  const { results } = await db
    .prepare('SELECT * FROM propositions WHERE dossier_an = ? ORDER BY id DESC LIMIT 10')
    .bind(id)
    .all<Ligne>();
  return results.map(lire);
}

async function une(db: D1Database, id: number): Promise<Proposition> {
  const l = await db.prepare('SELECT * FROM propositions WHERE id = ?').bind(id).first<Ligne>();
  if (!l) throw new Error(`proposition ${id} introuvable`);
  return lire(l);
}

export class RefusProposition extends Error {}

/** Le document qu'un chargement écrirait, à partir de la qualification actuelle de D1 (ou null). */
export function aCharger(
  p: Proposition,
  actuelle: Qualification | null
): { doc: Qualification; motif_ecart: string | null } {
  const d = p.doc;
  if (!d) throw new RefusProposition('proposition sans brouillon');
  if (d.statut === 'sans-source')
    throw new RefusProposition('aucune source trouvée : rien à charger, écarter la proposition');
  // Bloc du Sénat seul : il complète la qualification existante sans toucher au reste.
  if (!d.titre) {
    if (!actuelle) throw new RefusProposition('bloc du Sénat sans qualification à compléter');
    return {
      doc: normaliser({ ...actuelle, senat: d.senat }),
      motif_ecart: null
    };
  }
  const { statut, motif_ecart, ...reste } = d;
  void statut;
  return {
    doc: normaliser({
      ...reste,
      droits: reste.droits ?? [],
      scrutins: reste.scrutins ?? []
    } as Qualification),
    motif_ecart: d.statut === 'ecarte' ? (motif_ecart ?? null) : null
  };
}

/**
 * Charge une proposition : la qualification passe « à relire » (une proposition d'écart garde son motif,
 * que le relecteur confirme en choisissant « écarté »). La révision dit d'où vient le document.
 */
export async function charger(db: D1Database, id: number, auteur: string): Promise<string> {
  const p = await une(db, id);
  if (p.statut !== 'proposee')
    throw new RefusProposition(`proposition ${p.statut === 'echec' ? 'en échec' : 'déjà traitée'}`);
  const ligne = await qualification(db, p.dossier_an);
  const { doc, motif_ecart } = aCharger(p, ligne?.doc ?? null);
  const statut: Statut = 'a-relire';
  await enregistrer(
    db,
    {
      doc,
      statut,
      motif_ecart,
      commentaire: `proposition LLM n° ${p.id} chargée (${p.relecture.origine ?? p.modele})`
    },
    auteur,
    ligne?.modifie_le ?? null
  );
  await marquer(db, id, 'chargee', null, auteur);
  return p.dossier_an;
}

export async function ecarter(
  db: D1Database,
  id: number,
  motif: string,
  auteur: string
): Promise<void> {
  const p = await une(db, id);
  if (p.statut === 'chargee' || p.statut === 'ecartee')
    throw new RefusProposition('proposition déjà traitée');
  await marquer(db, id, 'ecartee', motif.trim() || p.motif, auteur);
}

async function marquer(
  db: D1Database,
  id: number,
  statut: StatutProposition,
  motif: string | null,
  auteur: string
): Promise<void> {
  await db
    .prepare(
      'UPDATE propositions SET statut = ?, motif = ?, traite_par = ?, traite_le = ? WHERE id = ?'
    )
    .bind(statut, motif, auteur, new Date().toISOString().slice(0, 19) + '+00:00', id)
    .run();
}

/** Résumé d'une proposition en une ligne : jugement proposé. */
export function jugement(d: DocPropose | null): string {
  if (!d) return 'aucun brouillon';
  if (d.statut === 'sans-source') return 'aucune source admise trouvée';
  if (d.statut === 'ecarte') return `écarter : ${d.motif_ecart ?? 'sans motif'}`;
  if (!d.titre) return 'vote du Sénat';
  const p = (d.droits ?? []).find((x) => x.role === 'principal');
  const decisif = (d.scrutins ?? []).find((s) => s.role === 'decisif');
  if (d.statut === 'a-suivre')
    return `fiche de suivi : ${(d.droits ?? []).map((x) => x.code).join(', ')}`;
  return [
    p ? `${p.code}, ${p.sens === 'etend' ? 'étend' : 'restreint'}` : 'sans droit principal',
    decisif ? `décisif ${decisif.id}` : 'sans décisif'
  ].join(' · ');
}

/** Proposition qui soulève une question de méthode (« CAS NON PRÉVU ») encore ouverte. */
export function casNonPrevu(p: Proposition): boolean {
  if (p.relecture.methode_tranchee) return false;
  return [...(p.relecture.points_attention ?? []), ...(p.relecture.controles?.points ?? [])].some(
    (x) => String(x).startsWith('CAS NON PRÉVU')
  );
}

/** Marque la question de méthode d'une proposition comme tranchée : elle reste lisible, la carte change de section. */
export async function trancher(db: D1Database, id: number, auteur: string): Promise<void> {
  const r = await db
    .prepare(
      `UPDATE propositions SET relecture = json_set(COALESCE(relecture, '{}'), '$.methode_tranchee', json(?))
       WHERE id = ? AND statut IN ('proposee', 'echec')`
    )
    .bind(JSON.stringify({ par: auteur, le: new Date().toISOString().slice(0, 19) + '+00:00' }), id)
    .run();
  if (!r.meta.changes) throw new RefusProposition('proposition introuvable ou déjà traitée');
}

export interface Demande {
  alerte_id: string;
  dossier_an: string;
  demande_par: string;
  demande_le: string;
}

export async function demandes(db: D1Database): Promise<Demande[]> {
  const { results } = await db.prepare('SELECT * FROM demandes_llm').all<Demande>();
  return results;
}

/** Demande une proposition pour une alerte : la prochaine passe de l'Action la traite. */
export async function demander(
  db: D1Database,
  alerte: { id: string; dossier_id: string },
  auteur: string
): Promise<void> {
  const deja = await db
    .prepare('SELECT 1 FROM propositions WHERE alerte_id = ?')
    .bind(alerte.id)
    .first();
  if (deja) throw new RefusProposition('une proposition existe déjà pour cette alerte');
  await db
    .prepare(
      `INSERT INTO demandes_llm (alerte_id, dossier_an, demande_par, demande_le) VALUES (?, ?, ?, ?)
       ON CONFLICT (alerte_id) DO NOTHING`
    )
    .bind(alerte.id, alerte.dossier_id, auteur, new Date().toISOString().slice(0, 19) + '+00:00')
    .run();
}
