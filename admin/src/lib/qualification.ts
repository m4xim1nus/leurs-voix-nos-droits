// Qualification d'un texte : normalisation, contrôles, export d'editorial.json.
//
// Miroir de pipeline/lvnd/editorial.py (mêmes contrôles, mêmes messages, mêmes octets en
// sortie) : qualification.test.ts compare les deux sur data/editorial.json.

import type {
  Ecarte,
  Editorial,
  Grille,
  Qualification,
  ScrutinRetenu,
  Statut,
  TexteCatalogue
} from './types';

export const FORMAT = 1;
export const ROLES_DROIT = ['principal', 'secondaire'] as const;
export const SENS = ['etend', 'restreint'] as const;
export const ROLES_SCRUTIN = ['decisif', 'ensemble', 'motion', 'article', 'amendement'] as const;
export const POUR = ['texte', 'contre-texte', 'a-trancher'] as const;
export const STATUTS: Statut[] = ['brouillon', 'a-relire', 'valide', 'ecarte'];

/** Ordre des clés dans editorial.json (le même que dans le pipeline). */
const CLES_TEXTE = [
  'id',
  'dossier_an',
  'legislature',
  'titre',
  'resume',
  'droits',
  'etiquettes',
  'vigilance',
  'conseil_constitutionnel',
  'note',
  'sources',
  'scrutins'
] as const;
const CLES_DROIT = ['code', 'role', 'sens', 'sources', 'justification'] as const;
const CLES_SOURCE = ['auteur', 'titre', 'date', 'url'] as const;
const CLES_SCRUTIN = ['id', 'role', 'pour', 'objet'] as const;
const CLES_VIGILANCE = ['texte', 'sources'] as const;
const CLES_ECARTE = ['dossier_an', 'legislature', 'titre', 'motif'] as const;

function ordonner<T extends object>(d: Record<string, unknown>, cles: readonly string[]): T {
  const out: Record<string, unknown> = {};
  for (const k of cles) if (k in d && d[k] !== undefined) out[k] = d[k];
  return out as T;
}

const espaces = (s: unknown) => String(s ?? '').trim();
const parCle = (a: string, b: string) => (a < b ? -1 : a > b ? 1 : 0);

/** Une qualification au format 1, clés dans l'ordre du fichier. */
export function normaliser(t: Partial<Qualification>): Qualification {
  const sources: Record<string, unknown> = {};
  for (const k of Object.keys(t.sources ?? {}).sort(parCle)) {
    const s = (t.sources ?? {})[k];
    sources[k] = ordonner({ ...s, date: String(s.date ?? '') }, CLES_SOURCE);
  }
  return ordonner<Qualification>(
    {
      id: espaces(t.id),
      dossier_an: t.dossier_an,
      legislature: Number(t.legislature),
      titre: t.titre,
      resume: espaces(t.resume),
      droits: (t.droits ?? []).map((d) =>
        ordonner(
          { ...d, sources: [...(d.sources ?? [])], justification: espaces(d.justification) },
          CLES_DROIT
        )
      ),
      etiquettes: [...(t.etiquettes ?? [])],
      vigilance: (t.vigilance ?? []).map((v) =>
        ordonner({ texte: espaces(v.texte), sources: [...(v.sources ?? [])] }, CLES_VIGILANCE)
      ),
      // espaces ASCII seulement : les espaces insécables de la typographie française restent
      conseil_constitutionnel: String(t.conseil_constitutionnel ?? '')
        .replace(/[ \t\n\r]+/g, ' ')
        .trim(),
      note: espaces(t.note),
      sources,
      scrutins: (t.scrutins ?? []).map((s) => ordonner<ScrutinRetenu>({ ...s }, CLES_SCRUTIN))
    },
    CLES_TEXTE
  );
}

/** Document minimal d'un texte écarté. */
export function ecarte(e: {
  dossier_an: string;
  legislature: number;
  titre: string;
}): Qualification {
  return normaliser({
    id: '',
    dossier_an: e.dossier_an,
    legislature: e.legislature,
    titre: e.titre
  });
}

/** Qualification vide d'un texte du catalogue : rien n'est prérempli, sauf l'identité du texte. */
export function nouvelle(t: TexteCatalogue): Qualification {
  return normaliser({
    id: slug(t.titre),
    dossier_an: t.id,
    legislature: t.legislature,
    titre: t.titre,
    conseil_constitutionnel: ''
  });
}

/** Identifiant public lisible, tiré du titre (modifiable dans la fiche). */
export function slug(titre: string): string {
  const mots = titre
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, ' ')
    .trim()
    .split(' ')
    .filter((m) => m.length > 2 && !VIDES.has(m));
  return mots.slice(0, 5).join('-');
}
const VIDES = new Set([
  'loi',
  'les',
  'des',
  'aux',
  'une',
  'pour',
  'par',
  'sur',
  'dans',
  'visant',
  'relative',
  'relatif',
  'portant',
  'projet',
  'proposition'
]);

export interface InfoScrutin {
  dossier_id: string;
  etape: string | null;
  division: string | null;
  objet?: string | null;
  pour?: number;
  contre?: number;
}

/** Erreurs bloquantes et avertissements d'une qualification (docs/CONCEPTION.md, contrôles). */
export function valider(
  t: Qualification,
  grille: Grille,
  scrutinsDossier?: Map<string, InfoScrutin>
): { erreurs: string[]; avertissements: string[] } {
  const codes = new Set(grille.droits.map((d) => d.code));
  const etiquettes = new Set(grille.etiquettes.map((e) => e.code));
  const sources = t.sources ?? {};
  const err: string[] = [];
  const avert: string[] = [];

  if (!t.id) err.push('identifiant manquant');
  if (!(t.titre ?? '').trim()) err.push('titre manquant');
  const droits = t.droits ?? [];
  if (droits.filter((d) => d.role === 'principal').length !== 1)
    err.push('il faut exactement un droit principal');
  const vus = new Set<string>();
  for (const d of droits) {
    const c = d.code;
    if (!codes.has(c)) err.push(`droit inconnu : ${c}`);
    if (vus.has(c)) err.push(`droit en double : ${c}`);
    vus.add(c);
    if (!(ROLES_DROIT as readonly string[]).includes(d.role))
      err.push(`${c} : rôle inconnu (${d.role})`);
    if (!(SENS as readonly string[]).includes(d.sens)) err.push(`${c} : sens inconnu (${d.sens})`);
    if (!d.sources?.length) err.push(`${c} : aucune source`);
  }
  for (const e of t.etiquettes ?? []) if (!etiquettes.has(e)) err.push(`étiquette inconnue : ${e}`);
  const citees = new Set<string>([
    ...droits.flatMap((d) => d.sources ?? []),
    ...(t.vigilance ?? []).flatMap((v) => v.sources ?? [])
  ]);
  for (const s of [...citees].filter((s) => !(s in sources)).sort(parCle))
    err.push(`source citée mais non définie : ${s}`);
  for (const [k, s] of Object.entries(sources)) {
    if (!(s.url ?? '').startsWith('http')) err.push(`source ${k} : URL manquante`);
    if (!s.auteur || !s.titre) err.push(`source ${k} : auteur ou titre manquant`);
    if (!/^\d{4}(-\d{2}(-\d{2})?)?$/.test(String(s.date ?? '')))
      err.push(`source ${k} : date attendue au format AAAA-MM-JJ (ou AAAA-MM)`);
  }
  for (const k of Object.keys(sources)
    .filter((k) => !citees.has(k))
    .sort(parCle))
    avert.push(`source ${k} définie mais citée nulle part`);

  const scrutins = t.scrutins ?? [];
  if (scrutins.filter((s) => s.role === 'decisif').length !== 1)
    err.push('il faut exactement un scrutin décisif');
  const ids = scrutins.map((s) => s.id);
  for (const i of [...new Set(ids.filter((i, n) => ids.indexOf(i) !== n))].sort(parCle))
    err.push(`scrutin en double : ${i}`);
  for (const s of scrutins) {
    if (!(ROLES_SCRUTIN as readonly string[]).includes(s.role))
      err.push(`${s.id} : rôle inconnu (${s.role})`);
    if (!(POUR as readonly string[]).includes(s.pour))
      err.push(`${s.id} : sens inconnu (${s.pour})`);
    else if (s.pour === 'a-trancher') avert.push(`${s.id} : sens à trancher, scrutin non compté`);
  }
  const principal = droits.find((d) => d.role === 'principal');
  if (principal?.sens === 'etend' && !(t.vigilance ?? []).some((v) => v.sources?.length))
    avert.push(
      'le texte étend son droit principal : la règle 7 demande une source critique en vigilance'
    );

  if (scrutinsDossier) {
    const parArticle = new Map<string, { division: string; ids: string[] }>();
    for (const s of scrutins) {
      const info = scrutinsDossier.get(s.id);
      if (!info || info.dossier_id !== t.dossier_an) {
        err.push(`${s.id} : scrutin absent du dossier ${t.dossier_an}`);
        continue;
      }
      if (s.role === 'amendement' && s.pour !== 'a-trancher') {
        if (info.objet === 'suppression_article_unique')
          err.push(`${s.id} : suppression d'un article unique, pas un amendement clé (règle 11)`);
        if (info.pour === 0 || info.contre === 0)
          err.push(
            `${s.id} : amendement unanime (${info.pour}-${info.contre}), pas un amendement clé (règle 11)`
          );
        if (info.division) {
          const cle = `${info.etape}|${info.division}`;
          if (!parArticle.has(cle)) parArticle.set(cle, { division: info.division, ids: [] });
          parArticle.get(cle)!.ids.push(s.id);
        }
      }
    }
    for (const cle of [...parArticle.keys()].sort(parCle)) {
      const { division, ids } = parArticle.get(cle)!;
      if (ids.length > 1)
        err.push(
          `plusieurs amendements clés sur « ${division} » dans la même lecture : ${ids.join(', ')}`
        );
    }
  }
  return { erreurs: err, avertissements: avert };
}

/** Contenu d'editorial.json : textes validés et textes écartés, triés. */
export function documentEditorial(
  grille: number,
  textes: Qualification[],
  ecartes: Ecarte[]
): Editorial {
  return {
    format: FORMAT,
    grille,
    textes: textes.map((t) => normaliser(t)).sort((a, b) => parCle(a.id, b.id)),
    ecartes: ecartes
      .map((e) => ordonner<Ecarte>({ ...e }, CLES_ECARTE))
      .sort((a, b) => parCle(a.dossier_an, b.dossier_an))
  };
}

/** Sérialisation d'editorial.json : identique à `editorial.serialiser` du pipeline. */
export function serialiser(doc: Editorial): string {
  return JSON.stringify(doc, null, 2) + '\n';
}

/** Document tel que D1 le stocke : JSON compact (comme `sync_admin.compact`). */
export function compact(t: Qualification): string {
  return JSON.stringify(normaliser(t));
}

/** Empreinte (doc, statut, motif) : sert à repérer ce qui a changé depuis la dernière publication. */
export async function empreinte(
  doc: string,
  statut: Statut,
  motif: string | null
): Promise<string> {
  const octets = new TextEncoder().encode(`${doc}\n${statut}\n${motif ?? ''}`);
  const h = await crypto.subtle.digest('SHA-256', octets);
  return [...new Uint8Array(h)].map((b) => b.toString(16).padStart(2, '0')).join('');
}
