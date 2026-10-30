// Accès à D1 : catalogue (lecture seule) et tables éditoriales.

import type {
  Grille,
  Groupe,
  LigneQualification,
  PositionGroupe,
  Qualification,
  ScrutinCatalogue,
  Statut,
  TexteCatalogue
} from '../types';
import { resteATraiter, type Alerte } from '../alertes';
import { compact, type InfoScrutin } from '../qualification';

// D1 limite une requête à 100 paramètres liés.
const PAQUET = 90;

export async function meta<T>(db: D1Database, cle: string): Promise<T | null> {
  const r = await db
    .prepare('SELECT valeur FROM catalogue_meta WHERE cle = ?')
    .bind(cle)
    .first<{ valeur: string }>();
  return r ? (JSON.parse(r.valeur) as T) : null;
}

export async function grille(db: D1Database): Promise<Grille> {
  const g = await meta<Grille>(db, 'grille');
  if (!g) throw new Error('catalogue vide : lancer `lvnd sync-admin`');
  return g;
}

export interface LigneListe extends TexteCatalogue {
  statut: Statut | null;
  qualif_id: string | null;
  modifie_par: string | null;
  modifie_le: string | null;
}

export async function textes(db: D1Database): Promise<LigneListe[]> {
  const { results } = await db
    .prepare(
      `SELECT t.*, q.statut, json_extract(q.doc, '$.id') AS qualif_id, q.modifie_par, q.modifie_le
       FROM textes t LEFT JOIN qualifications q ON q.dossier_an = t.id
       ORDER BY t.dernier_scrutin DESC`
    )
    .all<LigneListe>();
  return results;
}

/** Alertes encore à traiter, vu ce que D1 contient déjà (lib/alertes.ts). */
export async function alertes(db: D1Database): Promise<Alerte[]> {
  const { results } = await db
    .prepare(
      `SELECT a.*, q.statut, q.doc FROM alertes a
       LEFT JOIN qualifications q ON q.dossier_an = a.dossier_id
       ORDER BY a.date DESC, a.id`
    )
    .all<Alerte & { statut: Statut | null; doc: string | null }>();
  return results.flatMap(({ statut, doc, ...a }) => (resteATraiter(a, statut, doc) ? [a] : []));
}

export async function texte(db: D1Database, id: string): Promise<TexteCatalogue | null> {
  return db.prepare('SELECT * FROM textes WHERE id = ?').bind(id).first<TexteCatalogue>();
}

type LigneScrutin = Omit<ScrutinCatalogue, 'positions'> & { positions: string };

const decoder = (s: LigneScrutin): ScrutinCatalogue => ({
  ...s,
  positions: JSON.parse(s.positions) as PositionGroupe[]
});

export async function scrutinsDuTexte(db: D1Database, id: string): Promise<ScrutinCatalogue[]> {
  const { results } = await db
    .prepare('SELECT * FROM scrutins WHERE texte_id = ? ORDER BY date DESC, numero DESC')
    .bind(id)
    .all<LigneScrutin>();
  return results.map(decoder);
}

/** Motions de censure votées entre deux dates (texte adopté par 49.3 sans vote final, règle 9). */
export async function censures(
  db: D1Database,
  debut: string,
  fin: string
): Promise<ScrutinCatalogue[]> {
  const { results } = await db
    .prepare(
      "SELECT * FROM scrutins WHERE objet = 'motion_censure' AND date BETWEEN ? AND ? ORDER BY date DESC, numero DESC"
    )
    .bind(debut, fin)
    .all<LigneScrutin>();
  return results.map(decoder);
}

/** Scrutins par identifiant, par paquets (limite de D1 sur les paramètres). */
export async function scrutins(db: D1Database, ids: string[]): Promise<ScrutinCatalogue[]> {
  const out: ScrutinCatalogue[] = [];
  const uniques = [...new Set(ids)];
  for (let i = 0; i < uniques.length; i += PAQUET) {
    const lot = uniques.slice(i, i + PAQUET);
    const { results } = await db
      .prepare(`SELECT * FROM scrutins WHERE id IN (${lot.map(() => '?').join(',')})`)
      .bind(...lot)
      .all<LigneScrutin>();
    out.push(...results.map(decoder));
  }
  return out;
}

export function infos(scrutins: ScrutinCatalogue[]): Map<string, InfoScrutin> {
  return new Map(
    scrutins.map((s) => [
      s.id,
      {
        dossier_id: s.texte_id,
        etape: s.etape,
        division: s.amendement_division,
        objet: s.objet,
        pour: s.pour,
        contre: s.contre
      }
    ])
  );
}

export async function groupes(db: D1Database): Promise<Groupe[]> {
  const { results } = await db
    .prepare('SELECT * FROM groupes ORDER BY legislature, sigle')
    .all<Groupe>();
  return results;
}

type LigneQualifBrute = Omit<LigneQualification, 'doc'> & { doc: string };

const qualif = (r: LigneQualifBrute): LigneQualification => ({
  ...r,
  doc: JSON.parse(r.doc) as Qualification
});

export async function qualification(
  db: D1Database,
  id: string
): Promise<LigneQualification | null> {
  const r = await db
    .prepare('SELECT * FROM qualifications WHERE dossier_an = ?')
    .bind(id)
    .first<LigneQualifBrute>();
  return r ? qualif(r) : null;
}

export async function qualifications(db: D1Database): Promise<LigneQualification[]> {
  const { results } = await db.prepare('SELECT * FROM qualifications').all<LigneQualifBrute>();
  return results.map(qualif);
}

export interface Revision {
  id: number;
  dossier_an: string;
  statut: Statut;
  doc: string;
  motif_ecart: string | null;
  auteur: string;
  date: string;
  commentaire: string | null;
}

export async function revisions(db: D1Database, id: string): Promise<Revision[]> {
  const { results } = await db
    .prepare('SELECT * FROM revisions WHERE dossier_an = ? ORDER BY id DESC LIMIT 50')
    .bind(id)
    .all<Revision>();
  return results;
}

/** Toutes les révisions publiables d'un texte, sans limite : sert à retrouver sa version publiée. */
export async function revisionsPubliables(db: D1Database, id: string): Promise<Revision[]> {
  const { results } = await db
    .prepare(
      "SELECT * FROM revisions WHERE dossier_an = ? AND statut IN ('valide', 'ecarte', 'a-suivre') ORDER BY id DESC"
    )
    .bind(id)
    .all<Revision>();
  return results;
}

export async function journal(db: D1Database, limite = 100) {
  const { results } = await db
    .prepare(
      `SELECT r.id, r.dossier_an, r.statut, r.auteur, r.date, r.commentaire,
              json_extract(r.doc, '$.id') AS qualif_id, t.titre
       FROM revisions r LEFT JOIN textes t ON t.id = r.dossier_an
       ORDER BY r.id DESC LIMIT ?`
    )
    .bind(limite)
    .all<{
      id: number;
      dossier_an: string;
      statut: Statut;
      auteur: string;
      date: string;
      commentaire: string | null;
      qualif_id: string | null;
      titre: string | null;
    }>();
  return results;
}

export class ConflitEdition extends Error {}

/**
 * Enregistre une qualification et sa révision. `attendu` est la date de modification lue à
 * l'ouverture de la fiche : si quelqu'un a enregistré entre-temps, on refuse plutôt que d'écraser.
 */
export async function enregistrer(
  db: D1Database,
  q: { doc: Qualification; statut: Statut; motif_ecart: string | null; commentaire: string | null },
  auteur: string,
  attendu: string | null
): Promise<string> {
  const actuelle = await db
    .prepare('SELECT modifie_le, modifie_par FROM qualifications WHERE dossier_an = ?')
    .bind(q.doc.dossier_an)
    .first<{ modifie_le: string; modifie_par: string }>();
  if ((actuelle?.modifie_le ?? null) !== attendu)
    throw new ConflitEdition(
      `modifiée entre-temps par ${actuelle?.modifie_par} (${actuelle?.modifie_le}) : recharger la fiche`
    );
  const le = new Date().toISOString().slice(0, 19) + '+00:00';
  const doc = compact(q.doc);
  await db.batch([
    db
      .prepare(
        `INSERT INTO qualifications (dossier_an, statut, doc, motif_ecart, modifie_par, modifie_le)
         VALUES (?1, ?2, ?3, ?4, ?5, ?6)
         ON CONFLICT (dossier_an) DO UPDATE SET statut = ?2, doc = ?3, motif_ecart = ?4,
           modifie_par = ?5, modifie_le = ?6`
      )
      .bind(q.doc.dossier_an, q.statut, doc, q.motif_ecart, auteur, le),
    db
      .prepare(
        `INSERT INTO revisions (dossier_an, statut, doc, motif_ecart, auteur, date, commentaire)
         VALUES (?, ?, ?, ?, ?, ?, ?)`
      )
      .bind(q.doc.dossier_an, q.statut, doc, q.motif_ecart, auteur, le, q.commentaire)
  ]);
  return le;
}

export interface Publication {
  id: number;
  auteur: string;
  date: string;
  commit_sha: string | null;
  commit_url: string | null;
  n_textes: number;
  n_ecartes: number;
  resume: string;
}

export async function publications(db: D1Database): Promise<Publication[]> {
  const { results } = await db
    .prepare('SELECT * FROM publications ORDER BY id DESC LIMIT 50')
    .all<Publication>();
  return results;
}
