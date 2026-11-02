// Propositions du LLM : chargement « à relire » et écart, sur D1 émulée (schéma de migrations/).
import { mkdtempSync, readdirSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { afterAll, beforeAll, describe, expect, it } from 'vitest';
import { getPlatformProxy } from 'wrangler';
import { normaliser } from '../qualification';
import { enregistrer, qualification, revisions } from './db';
import {
  casNonPrevu,
  charger,
  demander,
  demandes,
  ecarter,
  jugement,
  trancher,
  propositionsOuvertes,
  RefusProposition,
  type DocPropose
} from './propositions';

const RACINE = new URL('../../../../', import.meta.url);
let dossier: string;
let proxy: Awaited<ReturnType<typeof getPlatformProxy<{ DB: D1Database }>>>;
let db: D1Database;

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
}, 60_000);

afterAll(async () => {
  await proxy?.dispose();
  rmSync(dossier, { recursive: true, force: true });
});

const BROUILLON: DocPropose = {
  id: 'essai-2026',
  dossier_an: 'DLR5L17N1',
  legislature: 17,
  titre: 'Loi essai',
  statut: 'a-relire',
  resume: 'Un texte.',
  droits: [
    {
      code: 'vie-privee',
      role: 'principal',
      sens: 'restreint',
      sources: ['cnil'],
      justification: 'j'
    }
  ],
  sources: { cnil: { auteur: 'CNIL', titre: 'Avis', date: '2026-01-01', url: 'https://cnil.fr' } },
  scrutins: [{ id: 'VTANR5L17V1', role: 'decisif', pour: 'texte', objet: 'ensemble (10-5)' }]
};

async function proposer(alerte: string, doc: DocPropose | null, statut = 'proposee') {
  await db
    .prepare(
      `INSERT INTO propositions (alerte_id, dossier_an, mode, date, modele, cout_usd, doc, relecture, statut)
       VALUES (?, ?, 'complet', '2026-11-02T10:00:00Z', 'claude-opus-5-5', 1.2, ?, ?, ?)`
    )
    .bind(
      alerte,
      doc?.dossier_an ?? 'DLR5L17N1',
      doc ? JSON.stringify(doc) : null,
      JSON.stringify({ origine: 'proposition LLM (essai)', extraits: ['cnil : « x »'] }),
      statut
    )
    .run();
  const r = await db
    .prepare('SELECT id FROM propositions WHERE alerte_id = ?')
    .bind(alerte)
    .first<{ id: number }>();
  return r!.id;
}

describe('propositions', () => {
  it('charge une proposition « à relire », une seule fois', async () => {
    const id = await proposer('premier_decisif:DLR5L17N1:VTANR5L17V1', BROUILLON);
    expect((await propositionsOuvertes(db)).map((p) => p.id)).toContain(id);
    expect(await charger(db, id, 'max@exemple.fr')).toBe('DLR5L17N1');
    const q = await qualification(db, 'DLR5L17N1');
    expect(q?.statut).toBe('a-relire');
    expect(q?.doc.droits[0].sens).toBe('restreint');
    expect((await revisions(db, 'DLR5L17N1'))[0].commentaire).toMatch(/proposition LLM n° \d+/);
    expect((await propositionsOuvertes(db)).map((p) => p.id)).not.toContain(id);
    await expect(charger(db, id, 'max@exemple.fr')).rejects.toThrow(RefusProposition);
  });

  it('un bloc du Sénat complète la qualification sans toucher au reste', async () => {
    const id = await proposer('senat_premier_vote:DLR5L17N1:SN1', {
      id: 'essai-2026',
      dossier_an: 'DLR5L17N1',
      senat: {
        version: 'meme',
        scrutins: [{ id: 'SN1', role: 'decisif', pour: 'texte', objet: 'ensemble (200-100)' }],
        droits: [],
        etiquettes: [],
        vigilance: [],
        sources: {},
        note: ''
      }
    } as unknown as DocPropose);
    await charger(db, id, 'max@exemple.fr');
    const q = await qualification(db, 'DLR5L17N1');
    expect(q?.doc.senat?.scrutins[0].id).toBe('SN1');
    expect(q?.doc.droits[0].code).toBe('vie-privee');
  });

  it('une proposition d’écart garde son motif ; sans source, rien à charger', async () => {
    const id = await proposer('premier_decisif:DLR5L17N2:V2', {
      id: '',
      dossier_an: 'DLR5L17N2',
      legislature: 17,
      titre: 'Loi organisationnelle',
      statut: 'ecarte',
      motif_ecart: 'Texte purement organisationnel (règle 8).'
    });
    await charger(db, id, 'max@exemple.fr');
    const q = await qualification(db, 'DLR5L17N2');
    expect(q).toMatchObject({
      statut: 'a-relire',
      motif_ecart: 'Texte purement organisationnel (règle 8).'
    });

    const vide = await proposer('inscrit:DLR5L17N3', {
      dossier_an: 'DLR5L17N3',
      statut: 'sans-source'
    });
    await expect(charger(db, vide, 'max@exemple.fr')).rejects.toThrow(/aucune source/);
    await ecarter(db, vide, '', 'max@exemple.fr');
    expect((await propositionsOuvertes(db)).map((p) => p.id)).not.toContain(vide);
  });

  it('refuse de charger par-dessus une saisie concurrente ou une proposition en échec', async () => {
    await enregistrer(
      db,
      {
        doc: normaliser({ ...BROUILLON, dossier_an: 'DLR5L17N4' } as never),
        statut: 'brouillon',
        motif_ecart: null,
        commentaire: null
      },
      'autre@exemple.fr',
      null
    );
    const echec = await proposer(
      'premier_decisif:DLR5L17N4:V4',
      { ...BROUILLON, dossier_an: 'DLR5L17N4' },
      'echec'
    );
    await expect(charger(db, echec, 'max@exemple.fr')).rejects.toThrow(/échec/);
    await ecarter(db, echec, 'vu', 'max@exemple.fr');
    await expect(ecarter(db, echec, 'vu', 'max@exemple.fr')).rejects.toThrow(/déjà traitée/);
  });

  it('résume le jugement proposé', () => {
    expect(jugement(BROUILLON)).toBe('vie-privee, restreint · décisif VTANR5L17V1');
    expect(jugement({ dossier_an: 'D', statut: 'sans-source' })).toMatch(/aucune source/);
    expect(jugement({ ...BROUILLON, statut: 'ecarte', motif_ecart: 'm' })).toBe('écarter : m');
  });

  it('demande une proposition une fois, et jamais pour une alerte déjà proposée', async () => {
    await demander(db, { id: 'senat_premier_vote:DLR5L17N9:SN9', dossier_id: 'DLR5L17N9' }, 'max');
    await demander(db, { id: 'senat_premier_vote:DLR5L17N9:SN9', dossier_id: 'DLR5L17N9' }, 'max');
    expect((await demandes(db)).filter((d) => d.dossier_an === 'DLR5L17N9')).toHaveLength(1);
    await expect(
      demander(db, { id: 'premier_decisif:DLR5L17N1:VTANR5L17V1', dossier_id: 'DLR5L17N1' }, 'max')
    ).rejects.toThrow(/existe déjà/);
  });

  it('repère une question de méthode', () => {
    const p = (points: string[]) =>
      ({ relecture: { points_attention: points } }) as unknown as Parameters<typeof casNonPrevu>[0];
    expect(casNonPrevu(p(['CAS NON PRÉVU : x']))).toBe(true);
    expect(casNonPrevu(p(['autre']))).toBe(false);
  });

  it('une question de méthode tranchée ne classe plus la carte en « question de méthode »', async () => {
    const id = await proposer('premier_decisif:DLR5L17N7:V7', {
      ...BROUILLON,
      dossier_an: 'DLR5L17N7'
    });
    await db
      .prepare(
        `UPDATE propositions SET relecture = json_set(relecture, '$.points_attention', json('["CAS NON PRÉVU : x"]')) WHERE id = ?`
      )
      .bind(id)
      .run();
    const avant = (await propositionsOuvertes(db)).find((p) => p.id === id)!;
    expect(casNonPrevu(avant)).toBe(true);
    await trancher(db, id, 'max');
    const apres = (await propositionsOuvertes(db)).find((p) => p.id === id)!;
    expect(casNonPrevu(apres)).toBe(false);
    expect(apres.relecture.methode_tranchee?.par).toBe('max');
    expect(apres.relecture.points_attention).toEqual(['CAS NON PRÉVU : x']);
  });
});
