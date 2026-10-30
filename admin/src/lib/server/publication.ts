// « Publier » : export des qualifications validées vers data/editorial.json, en un commit.
//
// Sont publiés les textes `valide` (dans `textes`), `ecarte` (dans `ecartes`, avec leur motif) et
// `a-suivre` (dans `suivis`), cf. docs/CONCEPTION.md, choix B. Un texte publié puis repassé en brouillon ou « à relire »
// (requalification) garde sa version publiée jusqu'à sa validation ; pour le retirer, on l'écarte.
// Aucune publication tant qu'un texte à publier a une erreur bloquante.

import type { Ecarte, Grille, LigneQualification, Qualification, Statut } from '../types';
import {
  compact,
  documentEditorial,
  empreinte,
  serialiser,
  valider,
  validerSuivi
} from '../qualification';
import * as db from './db';
import { ecrireFichier, lireFichier, shaBlob, type ConfigGitHub } from './github';

export interface EtatTexte {
  dossier_an: string;
  id: string;
  titre: string;
  statut: LigneQualification['statut'];
  changement: 'nouveau' | 'modifie' | null;
  en_ligne: boolean; // repassé en brouillon ou « à relire » : sa version publiée reste sur le site
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

const PUBLIABLES = new Set(['valide', 'ecarte', 'a-suivre']);

export interface VersionPubliee {
  doc: Qualification;
  statut: Statut;
  motif_ecart: string | null;
  date: string;
}

/** Version publiée d'un texte : la révision dont l'empreinte est celle de la dernière publication. */
export async function versionPubliee(
  base: D1Database,
  dossier: string,
  publie: string
): Promise<VersionPubliee | null> {
  for (const r of await db.revisionsPubliables(base, dossier)) {
    const doc = JSON.parse(r.doc) as Qualification;
    if ((await empreinte(compact(doc), r.statut, r.motif_ecart)) === publie)
      return { doc, statut: r.statut, motif_ecart: r.motif_ecart, date: r.date };
  }
  return null;
}

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
  // Textes en cours de requalification : le fichier garde leur version publiée.
  const enLigne = new Map<string, VersionPubliee>();
  const introuvables = new Set<string>();
  for (const l of lignes) {
    if (PUBLIABLES.has(l.statut) || !l.publie_empreinte) continue;
    const v = await versionPubliee(base, l.dossier_an, l.publie_empreinte);
    if (v) enLigne.set(l.dossier_an, v);
    else introuvables.add(l.dossier_an);
  }
  const conserves = [...enLigne.values()];
  const docsValides = [
    ...valides.map((l) => l.doc),
    ...conserves.filter((v) => v.statut === 'valide').map((v) => v.doc)
  ];
  const docsSuivis = [...lignes, ...conserves]
    .filter((l) => l.statut === 'a-suivre')
    .map((l) => l.doc);
  const infos = db.infos(
    await db.scrutins(
      base,
      valides.flatMap((l) => l.doc.scrutins.map((s) => s.id))
    )
  );
  const ids = new Map<string, number>();
  for (const d of [...docsValides, ...docsSuivis]) ids.set(d.id, (ids.get(d.id) ?? 0) + 1);

  const textes: EtatTexte[] = [];
  for (const l of lignes) {
    const publiable = PUBLIABLES.has(l.statut);
    const e = await empreinte(compact(l.doc), l.statut, l.motif_ecart);
    let changement: EtatTexte['changement'] = null;
    if (publiable && !l.publie_empreinte) changement = 'nouveau';
    else if (publiable && l.publie_empreinte !== e) changement = 'modifie';
    const v =
      l.statut === 'valide'
        ? valider(l.doc, g, infos)
        : l.statut === 'a-suivre'
          ? validerSuivi(l.doc, g)
          : { erreurs: [], avertissements: [] };
    if ((l.statut === 'valide' || l.statut === 'a-suivre') && (ids.get(l.doc.id) ?? 0) > 1)
      v.erreurs.push(`identifiant ${l.doc.id} utilisé par plusieurs textes`);
    if (l.statut === 'ecarte' && !(l.motif_ecart ?? '').trim()) v.erreurs.push('motif manquant');
    const conserve = enLigne.get(l.dossier_an);
    if (conserve && conserve.statut !== 'ecarte' && (ids.get(conserve.doc.id) ?? 0) > 1)
      v.erreurs.push(`identifiant ${conserve.doc.id} utilisé par plusieurs textes`);
    if (introuvables.has(l.dossier_an))
      v.erreurs.push(
        'version publiée introuvable dans les révisions : valider ou écarter le texte avant de publier'
      );
    textes.push({
      dossier_an: l.dossier_an,
      id: l.doc.id,
      titre: l.doc.titre,
      statut: l.statut,
      changement,
      en_ligne: !publiable && Boolean(l.publie_empreinte),
      erreurs: v.erreurs,
      avertissements: v.avertissements,
      modifie_par: l.modifie_par,
      modifie_le: l.modifie_le
    });
  }
  const ecartes: Ecarte[] = [...lignes, ...conserves]
    .filter((l) => l.statut === 'ecarte')
    .map((l) => ({
      dossier_an: l.doc.dossier_an,
      legislature: l.doc.legislature,
      titre: l.doc.titre,
      motif: (l.motif_ecart ?? '').trim()
    }));
  const contenu = serialiser(documentEditorial(g.version, docsValides, ecartes, docsSuivis));
  // Un terme interdit (CLAUDE.md, règles dures) bloque la publication : on signale le texte fautif.
  for (const t of textes) {
    const l = lignes.find((x) => x.dossier_an === t.dossier_an)!;
    const q = PUBLIABLES.has(t.statut) ? l : enLigne.get(t.dossier_an);
    if (!q) continue;
    const trouves = termesInterdits(compact(q.doc) + (q.motif_ecart ?? ''), interdits);
    if (trouves.length)
      t.erreurs.push(`terme interdit dans la qualification : ${trouves.join(', ')}`);
  }
  const bloquant = textes.some((t) => (PUBLIABLES.has(t.statut) || t.en_ligne) && t.erreurs.length);
  return { textes, bloquant, contenu, lignes };
}

export function message(textes: EtatTexte[]): string {
  const par = (c: EtatTexte['changement'], statut: Statut = 'valide') =>
    textes
      .filter((t) => t.changement === c && t.statut === statut)
      .map((t) => (statut === 'ecarte' ? t.dossier_an : t.id))
      .sort();
  const listes: [string, string[]][] = [
    ['Ajoutés', par('nouveau')],
    ['Modifiés', par('modifie')],
    ['Écartés', [...par('nouveau', 'ecarte'), ...par('modifie', 'ecarte')]],
    ['À suivre', [...par('nouveau', 'a-suivre'), ...par('modifie', 'a-suivre')]]
  ];
  const mots = ['ajouté', 'modifié', 'écarté'];
  const titre = listes
    .map(([, l], i) =>
      !l.length
        ? 0
        : i === 3
          ? `${l.length} à suivre`
          : `${l.length} ${mots[i]}${l.length > 1 ? 's' : ''}`
    )
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
      // Texte en cours de requalification : sa version publiée n'a pas bougé, son empreinte non plus.
      const e = PUBLIABLES.has(l.statut)
        ? await empreinte(compact(l.doc), l.statut, l.motif_ecart)
        : l.publie_empreinte;
      return base
        .prepare(
          'UPDATE qualifications SET publie_empreinte = ? WHERE dossier_an = ? AND modifie_le = ?'
        )
        .bind(e, l.dossier_an, l.modifie_le);
    })
  );
  const fichier = JSON.parse(prep.contenu) as { textes: unknown[]; ecartes: unknown[] };
  const n = fichier.textes.length;
  const nEcartes = fichier.ecartes.length;
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
