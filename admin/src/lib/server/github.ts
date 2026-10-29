// Lecture et écriture d'editorial.json dans le dépôt, par l'API « contents » de GitHub.
//
// Le jeton (secret GITHUB_TOKEN) est un jeton « fine-grained » limité au dépôt, avec la seule
// permission « Contents: read and write ». L'écriture passe le `sha` lu juste avant : si le
// fichier a changé entre-temps, GitHub refuse (409) et rien n'est écrasé.

export interface ConfigGitHub {
  jeton: string;
  depot: string; // propriétaire/dépôt
  branche: string;
  chemin: string;
}

export interface FichierDistant {
  sha: string | null; // null : le fichier n'existe pas encore
  contenu: string | null;
}

type Fetch = typeof fetch;

const API = 'https://api.github.com';

function entetes(cfg: ConfigGitHub, accept = 'application/vnd.github+json'): HeadersInit {
  return {
    Accept: accept,
    Authorization: `Bearer ${cfg.jeton}`,
    'User-Agent': 'lvnd-admin',
    'X-GitHub-Api-Version': '2022-11-28'
  };
}

export function versBase64(texte: string): string {
  const octets = new TextEncoder().encode(texte);
  let bin = '';
  for (let i = 0; i < octets.length; i += 0x8000)
    bin += String.fromCharCode(...octets.subarray(i, i + 0x8000));
  return btoa(bin);
}

export function depuisBase64(b64: string): string {
  const bin = atob(b64.replace(/\s/g, ''));
  return new TextDecoder().decode(Uint8Array.from(bin, (c) => c.charCodeAt(0)));
}

/** Empreinte git d'un fichier (blob) : égale au `sha` de GitHub quand le contenu est identique. */
export async function shaBlob(texte: string): Promise<string> {
  const corps = new TextEncoder().encode(texte);
  const tete = new TextEncoder().encode(`blob ${corps.length}\0`);
  const tout = new Uint8Array(tete.length + corps.length);
  tout.set(tete);
  tout.set(corps, tete.length);
  const h = await crypto.subtle.digest('SHA-1', tout);
  return [...new Uint8Array(h)].map((b) => b.toString(16).padStart(2, '0')).join('');
}

export async function lireFichier(cfg: ConfigGitHub, f: Fetch = fetch): Promise<FichierDistant> {
  const url = `${API}/repos/${cfg.depot}/contents/${cfg.chemin}?ref=${encodeURIComponent(cfg.branche)}`;
  const r = await f(url, { headers: entetes(cfg) });
  if (r.status === 404) return { sha: null, contenu: null };
  if (!r.ok) throw new Error(`GitHub : lecture de ${cfg.chemin} impossible (${r.status})`);
  const meta = (await r.json()) as { sha: string; content?: string; encoding?: string };
  if (meta.encoding === 'base64' && meta.content)
    return { sha: meta.sha, contenu: depuisBase64(meta.content) };
  // au-delà de 1 Mo, l'API ne renvoie pas le contenu : on le demande brut
  const brut = await f(url, { headers: entetes(cfg, 'application/vnd.github.raw+json') });
  if (!brut.ok)
    throw new Error(`GitHub : lecture brute de ${cfg.chemin} impossible (${brut.status})`);
  return { sha: meta.sha, contenu: await brut.text() };
}

export class ConflitGitHub extends Error {}

/** Commit du fichier ; renvoie le sha et l'adresse du commit. */
export async function ecrireFichier(
  cfg: ConfigGitHub,
  contenu: string,
  shaPrecedent: string | null,
  message: string,
  f: Fetch = fetch
): Promise<{ sha: string; url: string }> {
  const r = await f(`${API}/repos/${cfg.depot}/contents/${cfg.chemin}`, {
    method: 'PUT',
    headers: { ...entetes(cfg), 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      content: versBase64(contenu),
      branch: cfg.branche,
      ...(shaPrecedent ? { sha: shaPrecedent } : {})
    })
  });
  if (r.status === 409 || r.status === 422)
    throw new ConflitGitHub(
      `${cfg.chemin} a changé dans le dépôt depuis sa lecture : relancer la publication`
    );
  if (!r.ok) throw new Error(`GitHub : écriture refusée (${r.status}) ${await r.text()}`);
  const { commit } = (await r.json()) as { commit: { sha: string; html_url: string } };
  return { sha: commit.sha, url: commit.html_url };
}
