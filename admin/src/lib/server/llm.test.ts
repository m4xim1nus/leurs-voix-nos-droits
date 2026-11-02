// Réglages et consommation du LLM : D1 émulée par wrangler, API simulée pour le test d'une clé.
import { mkdtempSync, readdirSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { afterAll, beforeAll, describe, expect, it } from 'vitest';
import { getPlatformProxy } from 'wrangler';
import {
  chiffrer,
  consommation,
  dechiffrer,
  ecrireReglage,
  etat,
  formeCle,
  reglages,
  retirerCle,
  testerCle
} from './llm';

const RACINE = new URL('../../../../', import.meta.url);

/** Vecteur partagé avec le pipeline (pipeline/tests/test_llm.py) : même secret, même nonce. */
const VECTEUR = {
  secret: 'secret-de-test',
  clair: 'sk-ant-api03-essai',
  nonce: new Uint8Array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11])
};

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

describe('chiffrement de la clé', () => {
  it('déchiffre ce qu’il chiffre, et pas avec un autre secret', async () => {
    const c = await chiffrer('s1', 'sk-ant-api03-abc');
    expect(c).toMatch(/^v1:/);
    expect(await dechiffrer('s1', c)).toBe('sk-ant-api03-abc');
    await expect(dechiffrer('s2', c)).rejects.toThrow();
  });

  it('produit le vecteur attendu par le pipeline', async () => {
    const c = await chiffrer(VECTEUR.secret, VECTEUR.clair, VECTEUR.nonce);
    const attendu = readFileSync(
      new URL('pipeline/tests/fixtures/llm_vecteur.txt', RACINE),
      'utf8'
    ).trim();
    expect(c).toBe(attendu);
  });
});

describe('clé saisie', () => {
  it('refuse une forme manifestement fausse', () => {
    expect(formeCle('')).toBeTruthy();
    expect(formeCle('sk-ant-admin01-x')).toMatch(/administration/);
    expect(formeCle('abc')).toMatch(/sk-ant-/);
    expect(formeCle('sk-ant-api03-a b')).toMatch(/espace/);
    expect(formeCle('sk-ant-api03-abc')).toBeNull();
  });

  it('teste la clé par la liste des modèles', async () => {
    const urls: string[] = [];
    const ok = (async (url: string | URL | Request) => {
      urls.push(String(url));
      return Response.json({ data: [], has_more: false, first_id: null, last_id: null });
    }) as typeof fetch;
    expect(await testerCle('sk-ant-api03-abc', ok)).toBeNull();
    expect(urls[0]).toMatch(/\/v1\/models/);
    const refus = (async () =>
      Response.json(
        { type: 'error', error: { type: 'authentication_error', message: 'invalid x-api-key' } },
        { status: 401 }
      )) as typeof fetch;
    expect(await testerCle('sk-ant-api03-abc', refus)).toMatch(/401/);
  });
});

describe('réglages et consommation', () => {
  it('sans réglage : coupé, plafond et modèle par défaut', async () => {
    const r = await reglages(db);
    expect(r).toMatchObject({
      actif: false,
      plafond_usd: 20,
      modele: 'claude-opus-5-5',
      cle: null
    });
    expect(etat(r, 0, true)).toBe('coupe');
  });

  it('suit l’interrupteur, la clé et le plafond', async () => {
    await ecrireReglage(db, 'actif', true, 'max@exemple.fr', '2026-11-02T10:00:00Z');
    expect(etat(await reglages(db), 0, true)).toBe('sans-cle');
    await ecrireReglage(
      db,
      'cle_api',
      { chiffre: await chiffrer('s', 'sk-ant-x-1234'), fin: '1234' },
      'max@exemple.fr'
    );
    await ecrireReglage(db, 'plafond_usd', 5, 'max@exemple.fr');
    const r = await reglages(db);
    expect(r.cle?.fin).toBe('1234');
    expect(r.bascule?.modifie_le).toBe('2026-11-02T10:00:00Z');
    expect(etat(r, 4.99, true)).toBe('en-service');
    expect(etat(r, 4.99, false)).toBe('sans-secret');
    expect(etat(r, 5, true)).toBe('plafond');
    await retirerCle(db);
    expect((await reglages(db)).cle).toBeNull();
  });

  it('ignore un réglage illisible ou un modèle inconnu', async () => {
    await db
      .prepare(
        "INSERT OR REPLACE INTO llm_reglages VALUES ('plafond_usd', 'pas du json', 'x', 'x')"
      )
      .run();
    await ecrireReglage(db, 'modele', 'gpt-quelque-chose', 'x');
    const r = await reglages(db);
    expect(r.plafond_usd).toBe(20);
    expect(r.modele).toBe('claude-opus-5-5');
  });

  it('additionne la dépense du mois en cours seulement', async () => {
    const ajout = (date: string, tache: string, cout: number) =>
      db
        .prepare(
          `INSERT INTO llm_appels (date, tache, modele, cout_usd, resultat)
           VALUES (?, ?, 'claude-opus-5-5', ?, 'ok')`
        )
        .bind(date, tache, cout);
    await db.batch([
      ajout('2026-10-31T23:59:00Z', 'proposition', 3),
      ajout('2026-11-01T00:01:00Z', 'proposition', 1.25),
      ajout('2026-11-02T05:00:00Z', 'veille', 0.5),
      ajout('2026-11-02T06:00:00Z', 'proposition', 0.25)
    ]);
    const c = await consommation(db, '2026-11-02T12:00:00Z');
    expect(c.mois_usd).toBeCloseTo(2);
    expect(c.mois_appels).toBe(3);
    expect(c.par_tache[0]).toMatchObject({ tache: 'proposition', appels: 2 });
    expect(c.par_mois.map((m) => m.mois)).toEqual(['2026-11', '2026-10']);
    expect(c.derniers[0].date).toBe('2026-11-02T06:00:00Z');
  });
});
