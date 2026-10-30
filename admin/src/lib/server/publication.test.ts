// Publication de bout en bout : D1 émulée par wrangler (base neuve, schéma de migrations/), API
// GitHub simulée.
import { mkdtempSync, readdirSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { afterAll, beforeAll, describe, expect, it } from 'vitest';
import { getPlatformProxy } from 'wrangler';
import { normaliser } from '../qualification';
import type { Grille, Qualification } from '../types';
import { enregistrer, ConflitEdition } from './db';
import { shaBlob, depuisBase64 } from './github';
import { preparer, publier } from './publication';

const RACINE = new URL('../../../../', import.meta.url);
const GRILLE: Grille = {
  version: 0,
  droits: [{ code: 'vie-privee', libelle: '' }],
  etiquettes: [],
  sens: []
};
const CFG = { jeton: 'j', depot: 'moi/depot', branche: 'main', chemin: 'data/editorial.json' };

let dossier: string;
let proxy: Awaited<ReturnType<typeof getPlatformProxy<{ DB: D1Database }>>>;
let db: D1Database;

function texte(p: Partial<Qualification> = {}): Qualification {
  return normaliser({
    id: 'essai',
    dossier_an: 'DLR5L17N1',
    legislature: 17,
    titre: 'Loi essai',
    droits: [
      {
        code: 'vie-privee',
        role: 'principal',
        sens: 'restreint',
        sources: ['s'],
        justification: 'j'
      }
    ],
    sources: { s: { auteur: 'CNIL', titre: 'Avis', date: '2024-01-01', url: 'https://cnil.fr' } },
    scrutins: [{ id: 'VTANR5L17V1', role: 'decisif', pour: 'texte', objet: 'ensemble (10-5)' }],
    ...p
  });
}

/** Faux dépôt : un fichier, son sha, et les commits reçus. */
function faux() {
  const etat = {
    contenu: null as string | null,
    sha: null as string | null,
    commits: [] as string[]
  };
  const f = (async (url: string, init?: RequestInit) => {
    if (!init?.method) {
      if (etat.contenu === null) return new Response('', { status: 404 });
      return Response.json({
        sha: etat.sha,
        encoding: 'base64',
        content: btoa(unescape(encodeURIComponent(etat.contenu)))
      });
    }
    const corps = JSON.parse(String(init.body));
    if ((corps.sha ?? null) !== etat.sha) return new Response('conflit', { status: 409 });
    etat.contenu = depuisBase64(corps.content);
    etat.sha = await shaBlob(etat.contenu);
    etat.commits.push(corps.message);
    return Response.json({
      commit: { sha: `c${etat.commits.length}`, html_url: `https://x/${etat.commits.length}` }
    });
  }) as typeof fetch;
  return { etat, f };
}

beforeAll(async () => {
  dossier = mkdtempSync(join(tmpdir(), 'lvnd-d1-'));
  proxy = await getPlatformProxy<{ DB: D1Database }>({
    configPath: new URL('wrangler.jsonc', new URL('admin/', RACINE)).pathname,
    persist: { path: dossier }
  });
  db = proxy.env.DB;
  const migrations = new URL('admin/migrations/', RACINE);
  for (const f of readdirSync(migrations).sort()) {
    const schema = readFileSync(new URL(f, migrations), 'utf8')
      .replace(/--.*$/gm, '')
      .split(';')
      .map((s) => s.trim())
      .filter(Boolean);
    for (const s of schema) await db.prepare(s).run();
  }
  await db.batch([
    db.prepare(`INSERT INTO scrutins (id, texte_id, legislature, numero, date, positions)
                VALUES ('VTANR5L17V1', 'DLR5L17N1', 17, 1, '2025-01-01', '[]')`)
  ]);
}, 60_000);

afterAll(async () => {
  await proxy?.dispose();
  rmSync(dossier, { recursive: true, force: true });
});

describe('publication', () => {
  it('publie les textes validés, puis ne republie que ce qui change', async () => {
    const { etat, f } = faux();
    let le = await enregistrer(
      db,
      { doc: texte(), statut: 'valide', motif_ecart: null, commentaire: null },
      'a@x',
      null
    );
    await enregistrer(
      db,
      {
        doc: texte({ id: 'brouillon', dossier_an: 'DLR5L17N2' }),
        statut: 'brouillon',
        motif_ecart: null,
        commentaire: null
      },
      'a@x',
      null
    );

    let prep = await preparer(db, GRILLE);
    expect(prep.bloquant).toBe(false);
    expect(prep.textes.find((t) => t.id === 'essai')?.changement).toBe('nouveau');

    const r1 = await publier(db, GRILLE, CFG, 'a@x', f);
    expect(r1.commit?.sha).toBe('c1');
    expect(etat.commits[0]).toMatch(/^Publication éditoriale : 1 ajouté\n\nAjoutés : essai\n/);
    const publie = JSON.parse(etat.contenu!);
    expect(publie.textes.map((t: Qualification) => t.id)).toEqual(['essai']); // pas le brouillon
    expect((await preparer(db, GRILLE)).textes.every((t) => !t.changement)).toBe(true);

    // Rien n'a changé : aucun commit.
    expect((await publier(db, GRILLE, CFG, 'a@x', f)).commit).toBeNull();

    // Modification, puis texte écarté avec motif.
    le = await enregistrer(
      db,
      {
        doc: texte({ resume: 'Nouveau résumé.' }),
        statut: 'valide',
        motif_ecart: null,
        commentaire: null
      },
      'b@x',
      le
    );
    await enregistrer(
      db,
      {
        doc: texte({ id: '', dossier_an: 'DLR5L17N2' }),
        statut: 'ecarte',
        motif_ecart: 'organisationnel',
        commentaire: null
      },
      'b@x',
      (await db
        .prepare("SELECT modifie_le FROM qualifications WHERE dossier_an = 'DLR5L17N2'")
        .first<{ modifie_le: string }>())!.modifie_le
    );
    prep = await preparer(db, GRILLE);
    expect(prep.textes.map((t) => t.changement).sort()).toEqual(['modifie', 'nouveau']);
    await publier(db, GRILLE, CFG, 'b@x', f);
    expect(etat.commits[1]).toMatch(/^Publication éditoriale : 1 modifié, 1 écarté/);
    expect(JSON.parse(etat.contenu!).ecartes).toEqual([
      { dossier_an: 'DLR5L17N2', legislature: 17, titre: 'Loi essai', motif: 'organisationnel' }
    ]);

    // Un texte publié repassé « à relire » garde sa version publiée : le fichier ne bouge pas.
    const enLigne = etat.contenu;
    const nCommits = etat.commits.length;
    le = await enregistrer(
      db,
      {
        doc: texte({ resume: 'Requalification en cours.' }),
        statut: 'a-relire',
        motif_ecart: null,
        commentaire: null
      },
      'b@x',
      le
    );
    prep = await preparer(db, GRILLE);
    const requalifie = prep.textes.find((t) => t.dossier_an === 'DLR5L17N1');
    expect(requalifie?.changement).toBeNull();
    expect(requalifie?.en_ligne).toBe(true);
    expect(prep.contenu).toBe(enLigne);
    expect((await publier(db, GRILLE, CFG, 'b@x', f)).commit).toBeNull();
    expect(etat.commits).toHaveLength(nCommits);
    const { n_textes } = (await db
      .prepare('SELECT n_textes FROM publications ORDER BY id DESC LIMIT 1')
      .first<{ n_textes: number }>())!;
    expect(n_textes).toBe(1);

    // Sa validation publie la nouvelle version, comme une modification.
    le = await enregistrer(
      db,
      {
        doc: texte({ resume: 'Requalification en cours.' }),
        statut: 'valide',
        motif_ecart: null,
        commentaire: null
      },
      'b@x',
      le
    );
    expect((await preparer(db, GRILLE)).textes.find((t) => t.id === 'essai')?.changement).toBe(
      'modifie'
    );
    await publier(db, GRILLE, CFG, 'b@x', f);
    expect(JSON.parse(etat.contenu!).textes[0].resume).toBe('Requalification en cours.');
    expect(etat.commits.at(-1)).toMatch(/Modifiés : essai/);

    // Un texte écarté repassé « à relire » reste dans la liste des écartés, avec son motif.
    const ecartes = JSON.parse(etat.contenu!).ecartes;
    await enregistrer(
      db,
      {
        doc: texte({ id: 'requalif', dossier_an: 'DLR5L17N2' }),
        statut: 'a-relire',
        motif_ecart: null,
        commentaire: null
      },
      'b@x',
      (await db
        .prepare("SELECT modifie_le FROM qualifications WHERE dossier_an = 'DLR5L17N2'")
        .first<{ modifie_le: string }>())!.modifie_le
    );
    prep = await preparer(db, GRILLE);
    expect(JSON.parse(prep.contenu).ecartes).toEqual(ecartes);
    expect(JSON.parse(prep.contenu).textes.map((t: Qualification) => t.id)).toEqual(['essai']);
  });

  it('refuse de publier si la version en ligne est introuvable, plutôt que de retirer le texte', async () => {
    const { etat, f } = faux();
    const doc = JSON.stringify(texte({ id: 'perdu', dossier_an: 'DLR5L17N3' }));
    await db
      .prepare(
        `INSERT INTO qualifications (dossier_an, statut, doc, modifie_par, modifie_le, publie_empreinte)
         VALUES ('DLR5L17N3', 'a-relire', ?, 'x', '2026-01-01', 'empreinte-sans-revision')`
      )
      .bind(doc)
      .run();
    const prep = await preparer(db, GRILLE);
    expect(prep.bloquant).toBe(true);
    expect(prep.textes.find((t) => t.dossier_an === 'DLR5L17N3')?.erreurs[0]).toMatch(
      /version publiée introuvable/
    );
    await expect(publier(db, GRILLE, CFG, 'x', f)).rejects.toThrow('erreurs bloquantes');
    expect(etat.commits).toEqual([]);
    await db.prepare("DELETE FROM qualifications WHERE dossier_an = 'DLR5L17N3'").run();
  });

  it('publie une fiche de suivi à part, sans sens ni scrutin, sans toucher aux qualifications', async () => {
    const { f, etat } = faux();
    const doc = normaliser({
      id: 'suivi-essai',
      dossier_an: 'DLR5L17N70',
      legislature: 17,
      titre: 'Proposition de loi suivie',
      droits: [{ code: 'vie-privee', sources: ['s'], justification: 'j' }] as never,
      sources: { s: { auteur: 'CNIL', titre: 'Avis', date: '2024-01-01', url: 'https://cnil.fr' } }
    });
    const le = await enregistrer(
      db,
      { doc, statut: 'a-suivre', motif_ecart: null, commentaire: null },
      'a@x',
      null
    );
    const prep = await preparer(db, GRILLE);
    const ligne = prep.textes.find((t) => t.id === 'suivi-essai')!;
    expect(ligne.changement).toBe('nouveau');
    expect(ligne.erreurs).toEqual([]);
    await publier(db, GRILLE, CFG, 'a@x', f);
    expect(etat.commits[0]).toContain('1 à suivre');
    expect(etat.commits[0]).toContain('À suivre : suivi-essai');
    const fichier = JSON.parse(etat.contenu!);
    expect(fichier.suivis).toEqual([
      {
        id: 'suivi-essai',
        dossier_an: 'DLR5L17N70',
        legislature: 17,
        titre: 'Proposition de loi suivie',
        resume: '',
        droits: [{ code: 'vie-privee', sources: ['s'], justification: 'j' }],
        note: '',
        sources: doc.sources
      }
    ]);
    expect(fichier.textes.some((t: Qualification) => t.id === 'suivi-essai')).toBe(false);

    // Une fiche qui porte un sens ou un scrutin bloque la publication.
    await enregistrer(
      db,
      {
        doc: normaliser({
          ...doc,
          scrutins: [{ id: 'V', role: 'motion', pour: 'texte', objet: 'o' }]
        }),
        statut: 'a-suivre',
        motif_ecart: null,
        commentaire: null
      },
      'a@x',
      le
    );
    const bloque = await preparer(db, GRILLE);
    expect(bloque.bloquant).toBe(true);
    expect(bloque.textes.find((t) => t.id === 'suivi-essai')?.erreurs).toContain(
      'aucun scrutin retenu avant le vote'
    );
    // Retour à une fiche correcte, pour les tests suivants.
    await db.prepare("DELETE FROM qualifications WHERE dossier_an = 'DLR5L17N70'").run();
  });

  it('refuse une édition concurrente', async () => {
    await expect(
      enregistrer(
        db,
        { doc: texte(), statut: 'brouillon', motif_ecart: null, commentaire: null },
        'c@x',
        '1999-01-01'
      )
    ).rejects.toBeInstanceOf(ConflitEdition);
  });

  it('bloque la publication si un texte validé a une erreur', async () => {
    const le = (await db
      .prepare("SELECT modifie_le FROM qualifications WHERE dossier_an = 'DLR5L17N1'")
      .first<{ modifie_le: string }>())!.modifie_le;
    await enregistrer(
      db,
      { doc: texte({ scrutins: [] }), statut: 'valide', motif_ecart: null, commentaire: null },
      'c@x',
      le
    );
    const prep = await preparer(db, GRILLE);
    expect(prep.bloquant).toBe(true);
    await expect(publier(db, GRILLE, CFG, 'c@x', faux().f)).rejects.toThrow('erreurs bloquantes');
  });

  it("calcule le sha git d'un fichier (comparaison avec le dépôt sans le télécharger)", async () => {
    // `printf 'a\n' | git hash-object --stdin`
    expect(await shaBlob('a\n')).toBe('78981922613b2afb6025042ff6bd878ac1994e85');
  });
});
