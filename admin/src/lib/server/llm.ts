// Usage du LLM (ROADMAP, cycle Pré-qualification, item 1) : réglages et consommation, dans D1.
//
// L'admin ne fait aucun appel de qualification : l'Action des propositions lit ces réglages avant
// tout appel et journalise chacun dans `llm_appels`. Le seul appel direct de l'admin est le test
// d'une clé saisie (liste des modèles, sans coût). Tout ce qui suit tolère l'absence de réglages :
// l'admin marche sans LLM.

import Anthropic from '@anthropic-ai/sdk';
import { MODELE_DEFAUT, MODELES, PLAFOND_DEFAUT, type Etat } from '../llm';

export { MODELES };

export interface Reglages {
  actif: boolean;
  plafond_usd: number;
  modele: string;
  /** Clé enregistrée : jamais en clair, seulement ses derniers caractères. */
  cle: { fin: string; modifie_par: string; modifie_le: string } | null;
  /** Dernier changement de l'interrupteur. */
  bascule: { modifie_par: string; modifie_le: string } | null;
}

interface LigneReglage {
  cle: string;
  valeur: string;
  modifie_par: string;
  modifie_le: string;
}

function lire<T>(l: LigneReglage | undefined): T | undefined {
  if (!l) return undefined;
  try {
    return JSON.parse(l.valeur) as T;
  } catch {
    return undefined;
  }
}

export async function reglages(db: D1Database): Promise<Reglages> {
  const { results } = await db.prepare('SELECT * FROM llm_reglages').all<LigneReglage>();
  const par = new Map(results.map((l) => [l.cle, l]));
  const plafond = lire<number>(par.get('plafond_usd'));
  const modele = lire<string>(par.get('modele'));
  const cle = lire<{ chiffre: string; fin: string }>(par.get('cle_api'));
  const actif = par.get('actif');
  return {
    actif: lire<boolean>(actif) === true,
    plafond_usd: typeof plafond === 'number' && plafond >= 0 ? plafond : PLAFOND_DEFAUT,
    modele: MODELES.some((m) => m.id === modele) ? modele! : MODELE_DEFAUT,
    cle:
      cle?.chiffre && par.get('cle_api')
        ? {
            fin: cle.fin,
            modifie_par: par.get('cle_api')!.modifie_par,
            modifie_le: par.get('cle_api')!.modifie_le
          }
        : null,
    bascule: actif ? { modifie_par: actif.modifie_par, modifie_le: actif.modifie_le } : null
  };
}

export async function ecrireReglage(
  db: D1Database,
  cle: 'actif' | 'plafond_usd' | 'modele' | 'cle_api',
  valeur: unknown,
  auteur: string,
  maintenant = new Date().toISOString()
): Promise<void> {
  await db
    .prepare(
      `INSERT INTO llm_reglages (cle, valeur, modifie_par, modifie_le) VALUES (?, ?, ?, ?)
       ON CONFLICT (cle) DO UPDATE SET valeur = excluded.valeur, modifie_par = excluded.modifie_par,
         modifie_le = excluded.modifie_le`
    )
    .bind(cle, JSON.stringify(valeur), auteur, maintenant)
    .run();
}

export async function retirerCle(db: D1Database): Promise<void> {
  await db.prepare("DELETE FROM llm_reglages WHERE cle = 'cle_api'").run();
}

// Chiffrement de la clé -------------------------------------------------------------------------
// AES-GCM 256, clé de chiffrement = SHA-256 du secret LLM_CHIFFREMENT (Worker et dépôt). Format :
// « v1: » + base64(nonce de 12 octets ‖ chiffré ‖ étiquette). Le pipeline déchiffre à l'identique
// (pipeline/lvnd/llm.py), un test croisé le vérifie.

const DONNEES_ASSOCIEES = new TextEncoder().encode('lvnd-llm-cle');

async function cleAes(secret: string): Promise<CryptoKey> {
  const empreinte = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(secret));
  return crypto.subtle.importKey('raw', empreinte, 'AES-GCM', false, ['encrypt', 'decrypt']);
}

const versBase64 = (o: Uint8Array) => btoa(String.fromCharCode(...o));
const depuisBase64 = (s: string) => Uint8Array.from(atob(s), (c) => c.charCodeAt(0));

export async function chiffrer(
  secret: string,
  clair: string,
  nonce = crypto.getRandomValues(new Uint8Array(12))
): Promise<string> {
  const chiffre = new Uint8Array(
    await crypto.subtle.encrypt(
      { name: 'AES-GCM', iv: nonce, additionalData: DONNEES_ASSOCIEES },
      await cleAes(secret),
      new TextEncoder().encode(clair)
    )
  );
  const tout = new Uint8Array(nonce.length + chiffre.length);
  tout.set(nonce);
  tout.set(chiffre, nonce.length);
  return `v1:${versBase64(tout)}`;
}

export async function dechiffrer(secret: string, valeur: string): Promise<string> {
  if (!valeur.startsWith('v1:')) throw new Error('format de clé chiffrée inconnu');
  const tout = depuisBase64(valeur.slice(3));
  const clair = await crypto.subtle.decrypt(
    { name: 'AES-GCM', iv: tout.slice(0, 12), additionalData: DONNEES_ASSOCIEES },
    await cleAes(secret),
    tout.slice(12)
  );
  return new TextDecoder().decode(clair);
}

/** Forme attendue d'une clé d'API : refuse d'emblée un collage manifestement faux. */
export function formeCle(cle: string): string | null {
  if (!cle) return 'clé vide';
  if (/\s/.test(cle)) return 'la clé contient un espace ou un retour à la ligne';
  if (cle.startsWith('sk-ant-admin'))
    return 'clé d’administration : il faut une clé d’API ordinaire';
  if (!cle.startsWith('sk-ant-')) return 'une clé d’API Anthropic commence par « sk-ant- »';
  return null;
}

/** Teste une clé par la liste des modèles (aucun jeton facturé). Renvoie null si elle est acceptée. */
export async function testerCle(cle: string, f: typeof fetch = fetch): Promise<string | null> {
  const client = new Anthropic({ apiKey: cle, fetch: f, maxRetries: 1, timeout: 15_000 });
  try {
    await client.models.list({ limit: 1 });
    return null;
  } catch (e) {
    if (e instanceof Anthropic.AuthenticationError) return 'clé refusée par l’API (401)';
    if (e instanceof Anthropic.PermissionDeniedError) return 'clé sans droit d’accès (403)';
    if (e instanceof Anthropic.RateLimitError) return 'API saturée (429), réessayer plus tard';
    if (e instanceof Anthropic.APIConnectionError) return 'API injoignable';
    if (e instanceof Anthropic.APIError) return `erreur de l’API (${e.status ?? '?'})`;
    throw e;
  }
}

// Consommation ----------------------------------------------------------------------------------

export interface Appel {
  id: number;
  date: string;
  tache: string;
  dossier_an: string | null;
  modele: string;
  jetons_entree: number;
  jetons_sortie: number;
  jetons_cache_lus: number;
  jetons_cache_ecrits: number;
  recherches_web: number;
  cout_usd: number;
  resultat: string;
  detail: string | null;
}

export interface Consommation {
  mois: string;
  mois_usd: number;
  mois_appels: number;
  par_tache: { tache: string; appels: number; cout_usd: number }[];
  par_mois: { mois: string; appels: number; cout_usd: number }[];
  derniers: Appel[];
}

export async function consommation(
  db: D1Database,
  maintenant = new Date().toISOString()
): Promise<Consommation> {
  const mois = maintenant.slice(0, 7);
  const [taches, moisListe, derniers] = await db.batch([
    db
      .prepare(
        `SELECT tache, COUNT(*) AS appels, COALESCE(SUM(cout_usd), 0) AS cout_usd FROM llm_appels
         WHERE substr(date, 1, 7) = ? GROUP BY tache ORDER BY cout_usd DESC`
      )
      .bind(mois),
    db.prepare(
      `SELECT substr(date, 1, 7) AS mois, COUNT(*) AS appels, COALESCE(SUM(cout_usd), 0) AS cout_usd
       FROM llm_appels GROUP BY 1 ORDER BY 1 DESC LIMIT 12`
    ),
    db.prepare('SELECT * FROM llm_appels ORDER BY date DESC, id DESC LIMIT 50')
  ]);
  const parTache = taches.results as Consommation['par_tache'];
  return {
    mois,
    mois_usd: parTache.reduce((s, t) => s + t.cout_usd, 0),
    mois_appels: parTache.reduce((s, t) => s + t.appels, 0),
    par_tache: parTache,
    par_mois: moisListe.results as Consommation['par_mois'],
    derniers: derniers.results as Appel[]
  };
}

/** Ce que fera l'Action à son prochain passage. Même règle que le pipeline (lvnd/llm.py). */
export function etat(r: Reglages, moisUsd: number, secretPresent: boolean): Etat {
  if (!r.actif) return 'coupe';
  if (!secretPresent) return 'sans-secret';
  if (!r.cle) return 'sans-cle';
  if (moisUsd >= r.plafond_usd) return 'plafond';
  return 'en-service';
}
