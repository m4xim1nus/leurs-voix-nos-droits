import { beforeAll, describe, expect, it } from 'vitest';
import { verifier } from './access';

const CONFIG = { equipe: 'https://equipe.cloudflareaccess.com', audience: 'aud-admin' };
const MAINTENANT = 1_800_000_000;

let cles: CryptoKeyPair;
let jwk: JsonWebKey;

const b64url = (b: Uint8Array) =>
  btoa(String.fromCharCode(...b))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '');
const enc = (o: object) => b64url(new TextEncoder().encode(JSON.stringify(o)));

async function jeton(charge: object, entete: object = { alg: 'RS256', kid: 'k1' }) {
  const corps = `${enc(entete)}.${enc(charge)}`;
  const sig = await crypto.subtle.sign(
    'RSASSA-PKCS1-v1_5',
    cles.privateKey,
    new TextEncoder().encode(corps)
  );
  return `${corps}.${b64url(new Uint8Array(sig))}`;
}

const valide = {
  aud: ['aud-admin'],
  iss: CONFIG.equipe,
  exp: MAINTENANT + 600,
  nbf: MAINTENANT - 10,
  email: 'Max@Exemple.fr'
};
const charger = async () => [{ ...(jwk as { n: string; e: string; kty: string }), kid: 'k1' }];

beforeAll(async () => {
  cles = (await crypto.subtle.generateKey(
    {
      name: 'RSASSA-PKCS1-v1_5',
      modulusLength: 2048,
      publicExponent: new Uint8Array([1, 0, 1]),
      hash: 'SHA-256'
    },
    true,
    ['sign', 'verify']
  )) as CryptoKeyPair;
  jwk = await crypto.subtle.exportKey('jwk', cles.publicKey);
});

describe('jeton Access', () => {
  it('accepte un jeton valide et rend le courriel', async () => {
    expect(await verifier(await jeton(valide), CONFIG, charger, MAINTENANT)).toBe('max@exemple.fr');
  });

  it.each([
    ['audience', { ...valide, aud: ['autre'] }, 'audience'],
    ['émetteur', { ...valide, iss: 'https://pirate.cloudflareaccess.com' }, 'émetteur'],
    ['expiration', { ...valide, exp: MAINTENANT - 1 }, 'expiré'],
    ['courriel', { ...valide, email: undefined }, 'courriel']
  ])('refuse un jeton dont le champ %s est invalide', async (_, charge, motif) => {
    await expect(verifier(await jeton(charge), CONFIG, charger, MAINTENANT)).rejects.toThrow(motif);
  });

  it('refuse une signature falsifiée, un autre algorithme, une clé inconnue', async () => {
    const t = await jeton(valide);
    const falsifie = t.slice(0, t.lastIndexOf('.') + 1) + 'AAAA' + t.slice(t.lastIndexOf('.') + 5);
    await expect(verifier(falsifie, CONFIG, charger, MAINTENANT)).rejects.toThrow();
    const autre = await jeton(valide, { alg: 'none', kid: 'k1' });
    await expect(verifier(autre, CONFIG, charger, MAINTENANT)).rejects.toThrow('algorithme');
    const inconnue = await jeton(valide, { alg: 'RS256', kid: 'k2' });
    await expect(verifier(inconnue, CONFIG, charger, MAINTENANT)).rejects.toThrow('inconnue');
    await expect(verifier(null, CONFIG, charger, MAINTENANT)).rejects.toThrow('absent');
  });
});
