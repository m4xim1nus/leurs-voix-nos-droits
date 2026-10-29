// Vérification du jeton de Cloudflare Access (en-tête `Cf-Access-Jwt-Assertion`).
//
// Access protège le domaine de l'admin, mais l'app vérifie elle-même le jeton : une route laissée
// sans politique Access (adresse de prévisualisation, erreur de configuration) ne donne alors
// rien. RS256, clés publiques de l'équipe (`<équipe>/cdn-cgi/access/certs`), audience, émetteur
// et expiration contrôlés. Aucune dépendance : WebCrypto suffit.

interface Jwk {
  kid: string;
  kty: string;
  n: string;
  e: string;
  alg?: string;
}

export interface ConfigAccess {
  equipe: string; // https://<équipe>.cloudflareaccess.com
  audience: string; // AUD de l'application Access
}

type ChargerCles = (equipe: string) => Promise<Jwk[]>;

const DUREE_CACHE = 3600_000;
let cache: { equipe: string; cles: Jwk[]; le: number } | null = null;

async function clesAccess(equipe: string): Promise<Jwk[]> {
  if (cache && cache.equipe === equipe && Date.now() - cache.le < DUREE_CACHE) return cache.cles;
  const r = await fetch(`${equipe}/cdn-cgi/access/certs`);
  if (!r.ok) throw new Error(`clés Access indisponibles (${r.status})`);
  const { keys } = (await r.json()) as { keys: Jwk[] };
  cache = { equipe, cles: keys, le: Date.now() };
  return keys;
}

function base64url(s: string): Uint8Array<ArrayBuffer> {
  const b = atob(s.replace(/-/g, '+').replace(/_/g, '/') + '='.repeat((4 - (s.length % 4)) % 4));
  return Uint8Array.from(b, (c) => c.charCodeAt(0));
}

const json = (s: string) => JSON.parse(new TextDecoder().decode(base64url(s)));

/** Courriel de l'utilisateur si le jeton est valide ; lève une erreur sinon. */
export async function verifier(
  jeton: string | null,
  config: ConfigAccess,
  charger: ChargerCles = clesAccess,
  maintenant: number = Date.now() / 1000
): Promise<string> {
  if (!jeton) throw new Error('jeton Access absent');
  const parties = jeton.split('.');
  if (parties.length !== 3) throw new Error('jeton Access mal formé');
  const [h, p, sig] = parties;
  const entete = json(h);
  if (entete.alg !== 'RS256') throw new Error(`algorithme refusé : ${entete.alg}`);
  const jwk = (await charger(config.equipe)).find((k) => k.kid === entete.kid);
  if (!jwk) throw new Error('clé du jeton inconnue');
  const cle = await crypto.subtle.importKey(
    'jwk',
    { kty: jwk.kty, n: jwk.n, e: jwk.e, alg: 'RS256', ext: true },
    { name: 'RSASSA-PKCS1-v1_5', hash: 'SHA-256' },
    false,
    ['verify']
  );
  const ok = await crypto.subtle.verify(
    'RSASSA-PKCS1-v1_5',
    cle,
    base64url(sig),
    new TextEncoder().encode(`${h}.${p}`)
  );
  if (!ok) throw new Error('signature du jeton invalide');
  const charge = json(p);
  const aud: string[] = Array.isArray(charge.aud) ? charge.aud : [charge.aud];
  if (!aud.includes(config.audience)) throw new Error('audience du jeton invalide');
  if (charge.iss !== config.equipe) throw new Error('émetteur du jeton invalide');
  if (typeof charge.exp !== 'number' || charge.exp < maintenant) throw new Error('jeton expiré');
  if (typeof charge.nbf === 'number' && charge.nbf > maintenant + 60)
    throw new Error('jeton pas encore valide');
  if (!charge.email) throw new Error('jeton sans courriel');
  return String(charge.email).toLowerCase();
}
