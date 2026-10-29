// « Publier » : export des qualifications validées vers data/editorial.json, en un commit.
//
// Sont publiés les textes `valide` (dans `textes`) et `ecarte` (dans `ecartes`, avec leur
// motif), cf. docs/CONCEPTION.md, choix B. Un texte publié puis repassé en brouillon est retiré.
// Aucune publication tant qu'un texte validé a une erreur bloquante.

import type { Ecarte, Grille, LigneQualification } from '../types';
import { compact, documentEditorial, empreinte, serialiser, valider } from '../qualification';
import * as db from './db';
import { ecrireFichier, lireFichier, shaBlob, type ConfigGitHub } from './github';

export interface EtatTexte {
  dossier_an: string;
  id: string;
  titre: string;
  statut: LigneQualification['statut'];
  changement: 'nouveau' | 'modifie' | 'retire' | null;
  erreurs: string[];
  avertissements: string[];
  modifie_par: string;
  modifie_le: string;
}

export interface Preparation {
  textes: EtatTexte[];
  bloquant: boolean;
  contenu: string;
  lignes: LigneQualification[];
}

const PUBLIABLES = new Set(['valide', 'ecarte']);

/** Termes de la liste privée (secret TERMES_INTERDITS, un par ligne) présents dans `texte`. */
export function termesInterdits(texte: string, liste: string | undefined): string[] {
  const termes = (liste ?? '')
    .split('\n')
    .map((t) => t.trim())
    .filter((t) => t && !t.startsWith('#'));
  const echapper = (t: string) => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  return termes.filter((t) =>
    new RegExp(`(?<![\\p{L}\\p{N}_])${echapper(t)}(?![\\p{L}\\p{N}_])`, 'iu').test(texte)
  );
}

export async function preparer(
  base: D1Database,
  g: Grille,
  interdits?: string
): Promise<Preparation> {
  const lignes = await db.qualifications(base);
  const valides = lignes.filter((l) => l.statut === 'valide');
  const infos = db.infos(
    await db.scrutins(
      base,
      valides.flatMap((l) => l.doc.scrutins.map((s) => s.id))
    )
  );
  const ids = new Map<string, number>();
  for (const l of valides) ids.set(l.doc.id, (ids.get(l.doc.id) ?? 0) + 1);

  const textes: EtatTexte[] = [];
  for (const l of lignes) {
    const publiable = PUBLIABLES.has(l.statut);
    const e = await empreinte(compact(l.doc), l.statut, l.motif_ecart);
    let changement: EtatTexte['changement'] = null;
    if (publiable && !l.publie_empreinte) changement = 'nouveau';
    else if (publiable && l.publie_empreinte !== e) changement = 'modifie';
    else if (!publiable && l.publie_empreinte) changement = 'retire';
    const v =
      l.statut === 'valide' ? valider(l.doc, g, infos) : { erreurs: [], avertissements: [] };
    if (l.statut === 'valide' && (ids.get(l.doc.id) ?? 0) > 1)
      v.erreurs.push(`identifiant ${l.doc.id} utilisé par plusieurs textes`);
    if (l.statut === 'ecarte' && !(l.motif_ecart ?? '').trim()) v.erreurs.push('motif manquant');
    textes.push({
      dossier_an: l.dossier_an,
      id: l.doc.id,
      titre: l.doc.titre,
      statut: l.statut,
      changement,
      erreurs: v.erreurs,
      avertissements: v.avertissements,
      modifie_par: l.modifie_par,
      modifie_le: l.modifie_le
    });
  }
  const ecartes: Ecarte[] = lignes
    .filter((l) => l.statut === 'ecarte')
    .map((l) => ({
      dossier_an: l.dossier_an,
      legislature: l.doc.legislature,
      titre: l.doc.titre,
      motif: (l.motif_ecart ?? '').trim()
    }));
  const contenu = serialiser(
    documentEditorial(
      g.version,
      valides.map((l) => l.doc),
      ecartes
    )
  );
  // Un terme interdit (CLAUDE.md, règles dures) bloque la publication : on signale le texte fautif.
  for (const t of textes) {
    if (!PUBLIABLES.has(t.statut)) continue;
    const l = lignes.find((x) => x.dossier_an === t.dossier_an)!;
    const trouves = termesInterdits(compact(l.doc) + (l.motif_ecart ?? ''), interdits);
    if (trouves.length)
      t.erreurs.push(`terme interdit dans la qualification : ${trouves.join(', ')}`);
  }
  const bloquant = textes.some((t) => PUBLIABLES.has(t.statut) && t.erreurs.length);
  return { textes, bloquant, contenu, lignes };
}

export function message(textes: EtatTexte[]): string {
  const par = (c: EtatTexte['changement'], ecarte = false) =>
    textes
      .filter((t) => t.changement === c && (t.statut === 'ecarte') === ecarte)
      .map((t) => (ecarte ? t.dossier_an : t.id))
      .sort();
  const listes: [string, string[]][] = [
    ['Ajoutés', par('nouveau')],
    ['Modifiés', par('modifie')],
    ['Écartés', [...par('nouveau', true), ...par('modifie', true)]],
    ['Retirés', textes.filter((t) => t.changement === 'retire').map((t) => t.id || t.dossier_an)]
  ];
  const mots = ['ajouté', 'modifié', 'écarté', 'retiré'];
  const titre = listes
    .map(([, l], i) => l.length && `${l.length} ${mots[i]}${l.length > 1 ? 's' : ''}`)
    .filter(Boolean);
  const corps = listes.filter(([, l]) => l.length).map(([k, l]) => `${k} : ${l.join(', ')}`);
  return [
    `Publication éditoriale : ${titre.join(', ') || 'mise à jour'}`,
    '',
    ...corps,
    '',
    "Publié depuis l'admin."
  ].join('\n');
}

export interface Resultat {
  commit: { sha: string; url: string } | null; // null : rien de nouveau à écrire
  resume: string;
}

export async function publier(
  base: D1Database,
  g: Grille,
  cfg: ConfigGitHub,
  auteur: string,
  f: typeof fetch = fetch,
  interdits?: string
): Promise<Resultat> {
  const prep = await preparer(base, g, interdits);
  if (prep.bloquant) throw new Error('des textes à publier ont des erreurs bloquantes');
  const distant = await lireFichier(cfg, f);
  const msg = message(prep.textes);
  let commit: Resultat['commit'] = null;
  if (distant.sha !== (await shaBlob(prep.contenu)))
    commit = await ecrireFichier(cfg, prep.contenu, distant.sha, msg, f);

  // Empreintes de ce qui vient d'être publié (les documents lus, pas ceux d'une édition parallèle).
  const maj = await Promise.all(
    prep.lignes.map(async (l) => {
      const e = PUBLIABLES.has(l.statut)
        ? await empreinte(compact(l.doc), l.statut, l.motif_ecart)
        : null;
      return base
        .prepare(
          'UPDATE qualifications SET publie_empreinte = ? WHERE dossier_an = ? AND modifie_le = ?'
        )
        .bind(e, l.dossier_an, l.modifie_le);
    })
  );
  const n = prep.lignes.filter((l) => l.statut === 'valide').length;
  const nEcartes = prep.lignes.filter((l) => l.statut === 'ecarte').length;
  const le = new Date().toISOString().slice(0, 19) + '+00:00';
  await base.batch([
    ...maj,
    base
      .prepare(
        `INSERT INTO publications (auteur, date, commit_sha, commit_url, n_textes, n_ecartes, resume)
         VALUES (?, ?, ?, ?, ?, ?, ?)`
      )
      .bind(auteur, le, commit?.sha ?? null, commit?.url ?? null, n, nEcartes, msg)
  ]);
  return { commit, resume: msg };
}
