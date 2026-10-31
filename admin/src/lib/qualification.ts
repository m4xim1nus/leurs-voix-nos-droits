// Qualification d'un texte : normalisation, contrôles, export d'editorial.json.
//
// Miroir de pipeline/lvnd/editorial.py (mêmes contrôles, mêmes messages, mêmes octets en
// sortie) : qualification.test.ts compare les deux sur data/editorial.json.

import type {
  BlocSenat,
  Ecarte,
  Editorial,
  Grille,
  Qualification,
  ScrutinRetenu,
  Source,
  Statut,
  Suivi,
  TexteCatalogue
} from './types';

export const FORMAT = 1;
export const ROLES_DROIT = ['principal', 'secondaire'] as const;
export const SENS = ['etend', 'restreint'] as const;
// `censure` : motion de censure sur un texte adopté par 49.3 sans vote final (règle 9), affichée seulement.
export const ROLES_SCRUTIN = [
  'decisif',
  'ensemble',
  'motion',
  'article',
  'amendement',
  'censure'
] as const;
export const POUR = ['texte', 'contre-texte', 'a-trancher'] as const;
export const STATUTS: Statut[] = ['brouillon', 'a-relire', 'valide', 'ecarte', 'a-suivre'];

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
  'scrutins',
  'senat'
] as const;
const CLES_DROIT = ['code', 'role', 'sens', 'sources', 'justification'] as const;
const CLES_SOURCE = ['auteur', 'titre', 'date', 'url'] as const;
const CLES_SCRUTIN = ['id', 'role', 'pour', 'objet'] as const;
const CLES_VIGILANCE = ['texte', 'sources'] as const;
const CLES_ECARTE = ['dossier_an', 'legislature', 'titre', 'motif'] as const;
const CLES_SUIVI = [
  'id',
  'dossier_an',
  'legislature',
  'titre',
  'resume',
  'droits',
  'note',
  'sources'
] as const;
const CLES_DROIT_SUIVI = ['code', 'sources', 'justification'] as const;
const CLES_SENAT = [
  'version',
  'scrutins',
  'droits',
  'etiquettes',
  'vigilance',
  'sources',
  'note'
] as const;
export const VERSIONS_SENAT = ['meme', 'autre', 'seul'] as const;
export const ROLES_SENAT = ['decisif', 'ensemble', 'motion'] as const;
const OBJETS_DECISIF_SENAT = ['ensemble', 'article_unique'];

function ordonner<T extends object>(d: Record<string, unknown>, cles: readonly string[]): T {
  const out: Record<string, unknown> = {};
  for (const k of cles) if (k in d && d[k] !== undefined) out[k] = d[k];
  return out as T;
}

const espaces = (s: unknown) => String(s ?? '').trim();
const parCle = (a: string, b: string) => (a < b ? -1 : a > b ? 1 : 0);

function droitsOrdonnes(droits: Qualification['droits'] | undefined) {
  return (droits ?? []).map((d) =>
    ordonner(
      { ...d, sources: [...(d.sources ?? [])], justification: espaces(d.justification) },
      CLES_DROIT
    )
  );
}

function vigilanceOrdonnee(vigilance: Qualification['vigilance'] | undefined) {
  return (vigilance ?? []).map((v) =>
    ordonner({ texte: espaces(v.texte), sources: [...(v.sources ?? [])] }, CLES_VIGILANCE)
  );
}

function sourcesOrdonnees(sources: Record<string, Source> | undefined) {
  const out: Record<string, unknown> = {};
  for (const k of Object.keys(sources ?? {}).sort(parCle)) {
    const s = (sources ?? {})[k];
    out[k] = ordonner({ ...s, date: String(s.date ?? '') }, CLES_SOURCE);
  }
  return out;
}

function senatOrdonne(s: Partial<BlocSenat>): BlocSenat {
  return ordonner<BlocSenat>(
    {
      version: s.version,
      scrutins: (s.scrutins ?? []).map((x) => ordonner<ScrutinRetenu>({ ...x }, CLES_SCRUTIN)),
      droits: droitsOrdonnes(s.droits),
      etiquettes: [...(s.etiquettes ?? [])],
      vigilance: vigilanceOrdonnee(s.vigilance),
      sources: sourcesOrdonnees(s.sources),
      note: espaces(s.note)
    },
    CLES_SENAT
  );
}

/**
 * Une qualification au format 1, clés dans l'ordre du fichier. `senat` n'apparaît que s'il n'est pas
 * vide : ajout compatible avec le format 1.
 */
export function normaliser(t: Partial<Qualification>): Qualification {
  const senat = senatOrdonne(t.senat ?? {});
  return ordonner<Qualification>(
    {
      id: espaces(t.id),
      dossier_an: t.dossier_an,
      legislature: Number(t.legislature),
      titre: t.titre,
      resume: espaces(t.resume),
      droits: droitsOrdonnes(t.droits),
      etiquettes: [...(t.etiquettes ?? [])],
      vigilance: vigilanceOrdonnee(t.vigilance),
      // espaces ASCII seulement : les espaces insécables de la typographie française restent
      conseil_constitutionnel: String(t.conseil_constitutionnel ?? '')
        .replace(/[ \t\n\r]+/g, ' ')
        .trim(),
      note: espaces(t.note),
      sources: sourcesOrdonnees(t.sources),
      scrutins: (t.scrutins ?? []).map((s) => ordonner<ScrutinRetenu>({ ...s }, CLES_SCRUTIN)),
      senat: senat.scrutins.length || senat.note ? senat : undefined
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

/** Entrée de `suivis` : d'une qualification, ne garde ni sens, ni rôle, ni scrutin. */
export function suivi(t: Qualification | Suivi): Suivi {
  const n = normaliser({ ...t, scrutins: [] } as Partial<Qualification>);
  return ordonner<Suivi>(
    { ...n, droits: n.droits.map((d) => ordonner({ ...d }, CLES_DROIT_SUIVI)) },
    CLES_SUIVI
  );
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

export interface InfoScrutinSenat {
  dossier_id: string;
  objet: string | null;
  pour: number;
  contre: number;
}

function controlerSources(
  sources: Record<string, Source>,
  citees: Set<string>,
  err: string[],
  avert: string[]
) {
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
}

/** Erreurs bloquantes et avertissements d'une fiche de suivi (mêmes messages que le pipeline). */
export function validerSuivi(
  t: Qualification,
  grille: Grille
): { erreurs: string[]; avertissements: string[] } {
  const codes = new Set(grille.droits.map((d) => d.code));
  const err: string[] = [];
  const avert: string[] = [];
  if (!t.id) err.push('identifiant manquant');
  if (!(t.titre ?? '').trim()) err.push('titre manquant');
  const droits = t.droits ?? [];
  if (!droits.length) err.push('il faut au moins un droit touché');
  const vus = new Set<string>();
  for (const d of droits) {
    const c = d.code;
    if (!codes.has(c)) err.push(`droit inconnu : ${c}`);
    if (vus.has(c)) err.push(`droit en double : ${c}`);
    vus.add(c);
    if (d.sens || d.role) err.push(`${c} : ni sens ni rôle avant le vote`);
    if (!d.sources?.length) err.push(`${c} : aucune source`);
  }
  if (t.scrutins?.length) err.push('aucun scrutin retenu avant le vote');
  controlerSources(t.sources ?? {}, new Set(droits.flatMap((d) => d.sources ?? [])), err, avert);
  return { erreurs: err, avertissements: avert };
}

/** Contrôles du bloc `senat` (règles 23 à 28), mêmes messages que le pipeline. */
function validerSenat(
  t: Qualification,
  grille: Grille,
  scrutinsSenat: Map<string, InfoScrutinSenat> | undefined,
  err: string[],
  avert: string[]
) {
  const s = t.senat!;
  const scrutins = s.scrutins ?? [];
  if (!(VERSIONS_SENAT as readonly string[]).includes(s.version))
    err.push(`Sénat : version inconnue (${s.version})`);
  if (!scrutins.length) err.push('Sénat : aucun scrutin retenu');
  const decisifs = scrutins.filter((x) => x.role === 'decisif');
  if (decisifs.length > 1) err.push('Sénat : plusieurs scrutins décisifs');
  const ids = scrutins.map((x) => x.id);
  for (const i of [...new Set(ids.filter((i, n) => ids.indexOf(i) !== n))].sort(parCle))
    err.push(`Sénat : scrutin en double : ${i}`);
  for (const x of scrutins) {
    if (!(ROLES_SENAT as readonly string[]).includes(x.role))
      err.push(`Sénat : ${x.id} : rôle inconnu (${x.role})`);
    if (!(POUR as readonly string[]).includes(x.pour))
      err.push(`Sénat : ${x.id} : sens inconnu (${x.pour})`);
    else if (x.pour === 'a-trancher')
      avert.push(`Sénat : ${x.id} : sens à trancher, scrutin non compté`);
  }

  const droits = s.droits ?? [];
  if (s.version !== 'autre' && droits.length)
    err.push('Sénat : droits propres réservés à une autre version');
  // Un texte adopté par 49.3 n'a pas de décisif, mais le Sénat peut voter le même texte (règle 26).
  if (
    s.version === 'meme' &&
    !t.scrutins?.some((x) => x.role === 'decisif' || x.role === 'censure')
  )
    err.push(
      "Sénat : même texte que l'Assemblée, mais aucun décisif ni motion de censure de l'Assemblée retenu"
    );
  if (s.version === 'seul' && !decisifs.length && t.droits?.length)
    err.push('Sénat : vote affiché, ni droits ni sens');
  if (s.version === 'seul' && decisifs.length && !t.droits?.length)
    err.push('Sénat : décisif sans droits');
  if (s.version === 'autre') {
    const codes = new Set(grille.droits.map((d) => d.code));
    const etiquettes = new Set(grille.etiquettes.map((e) => e.code));
    if (!decisifs.length && droits.length) err.push('Sénat : vote affiché, ni droits ni sens');
    if (decisifs.length && droits.filter((d) => d.role === 'principal').length !== 1)
      err.push('Sénat : il faut exactement un droit principal');
    const vus = new Set<string>();
    for (const d of droits) {
      const c = d.code;
      if (!codes.has(c)) err.push(`Sénat : droit inconnu : ${c}`);
      if (vus.has(c)) err.push(`Sénat : droit en double : ${c}`);
      vus.add(c);
      if (!(ROLES_DROIT as readonly string[]).includes(d.role))
        err.push(`Sénat : ${c} : rôle inconnu (${d.role})`);
      if (!(SENS as readonly string[]).includes(d.sens))
        err.push(`Sénat : ${c} : sens inconnu (${d.sens})`);
      if (!d.sources?.length) err.push(`Sénat : ${c} : aucune source`);
    }
    for (const e of s.etiquettes ?? [])
      if (!etiquettes.has(e)) err.push(`Sénat : étiquette inconnue : ${e}`);
    const e: string[] = [];
    const a: string[] = [];
    controlerSources(
      s.sources ?? {},
      new Set([
        ...droits.flatMap((d) => d.sources ?? []),
        ...(s.vigilance ?? []).flatMap((v) => v.sources ?? [])
      ]),
      e,
      a
    );
    err.push(...e.map((x) => `Sénat : ${x}`));
    avert.push(...a.map((x) => `Sénat : ${x}`));
    if (
      droits.find((d) => d.role === 'principal')?.sens === 'etend' &&
      !(s.vigilance ?? []).some((v) => v.sources?.length)
    )
      avert.push(
        'Sénat : le texte étend son droit principal : la règle 7 demande une source critique en vigilance'
      );
  }

  if (!scrutinsSenat) return;
  for (const x of scrutins) {
    const info = scrutinsSenat.get(x.id);
    if (!info || info.dossier_id !== t.dossier_an) {
      err.push(`Sénat : ${x.id} : scrutin absent du dossier ${t.dossier_an}`);
      continue;
    }
    if (x.role === 'decisif') {
      if (!OBJETS_DECISIF_SENAT.includes(info.objet ?? ''))
        err.push(`Sénat : ${x.id} : décisif sur ${info.objet}, pas sur l'ensemble (règle 23)`);
      if (info.pour === 0 || info.contre === 0)
        err.push(
          `Sénat : ${x.id} : décisif sans voix d'un côté (${info.pour}-${info.contre}), vote affiché (règle 23)`
        );
    }
    if (!(x.objet ?? '').includes(`(${info.pour}-${info.contre})`))
      avert.push(
        `Sénat : ${x.id} : l'objet ne reprend pas le décompte (${info.pour}-${info.contre})`
      );
  }
}

/** Erreurs bloquantes et avertissements d'une qualification (docs/CONCEPTION.md, contrôles). */
export function valider(
  t: Qualification,
  grille: Grille,
  scrutinsDossier?: Map<string, InfoScrutin>,
  scrutinsSenat?: Map<string, InfoScrutinSenat>
): { erreurs: string[]; avertissements: string[] } {
  const codes = new Set(grille.droits.map((d) => d.code));
  const etiquettes = new Set(grille.etiquettes.map((e) => e.code));
  const sources = t.sources ?? {};
  const err: string[] = [];
  const avert: string[] = [];

  if (!t.id) err.push('identifiant manquant');
  if (!(t.titre ?? '').trim()) err.push('titre manquant');
  const droits = t.droits ?? [];
  // Texte voté au seul Sénat : pas de décisif à l'AN, et pas de droits si son vote n'est qu'affiché.
  const seul = t.senat?.version === 'seul';
  if (droits.filter((d) => d.role === 'principal').length !== 1 && !(seul && !droits.length))
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
  controlerSources(sources, citees, err, avert);

  const scrutins = t.scrutins ?? [];
  const nDecisifs = scrutins.filter((s) => s.role === 'decisif').length;
  if (seul) {
    if (nDecisifs)
      err.push(
        "Sénat : texte sans décisif de l'Assemblée, mais un décisif de l'Assemblée est retenu"
      );
  } else if (nDecisifs > 1 || (nDecisifs === 0 && !scrutins.some((s) => s.role === 'censure')))
    err.push(
      'il faut exactement un scrutin décisif (ou, pour un texte adopté par 49.3 sans vote final, au moins une motion de censure)'
    );
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
      if (s.role === 'censure') {
        // Une motion de censure n'est pas toujours rattachée au dossier du texte.
        if (info?.objet !== 'motion_censure') err.push(`${s.id} : pas une motion de censure`);
        continue;
      }
      if (!info || info.dossier_id !== t.dossier_an) {
        err.push(`${s.id} : scrutin absent du dossier ${t.dossier_an}`);
        continue;
      }
      if (s.role === 'decisif' && (info.pour === 0 || info.contre === 0))
        err.push(
          `${s.id} : décisif unanime (${info.pour}-${info.contre}), texte à écarter (règle 9)`
        );
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
  if (t.senat) validerSenat(t, grille, scrutinsSenat, err, avert);
  return { erreurs: err, avertissements: avert };
}

/**
 * Contenu d'editorial.json : textes validés, textes écartés et fiches de suivi, triés. `suivis`
 * n'apparaît que s'il n'est pas vide : ajout compatible avec le format 1.
 */
export function documentEditorial(
  grille: number,
  textes: Qualification[],
  ecartes: Ecarte[],
  suivis: (Qualification | Suivi)[] = []
): Editorial {
  const doc: Editorial = {
    format: FORMAT,
    grille,
    textes: textes.map((t) => normaliser(t)).sort((a, b) => parCle(a.id, b.id)),
    ecartes: ecartes
      .map((e) => ordonner<Ecarte>({ ...e }, CLES_ECARTE))
      .sort((a, b) => parCle(a.dossier_an, b.dossier_an))
  };
  if (suivis.length) doc.suivis = suivis.map(suivi).sort((a, b) => parCle(a.id, b.id));
  return doc;
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

/**
 * Changements d'une qualification, champ par champ, de `avant` (version publiée) à `apres`
 * (version enregistrée), en phrases courtes pour la fiche de l'admin.
 */
export function differences(avant: Qualification, apres: Qualification): string[] {
  const a = normaliser(avant);
  const b = normaliser(apres);
  const out: string[] = [];
  const egal = (x: unknown, y: unknown) => JSON.stringify(x) === JSON.stringify(y);
  for (const k of ['titre', 'resume', 'conseil_constitutionnel', 'note'] as const)
    if (a[k] !== b[k]) out.push(`${k} modifié`);
  if (!egal(a.etiquettes, b.etiquettes))
    out.push(
      `étiquettes : ${a.etiquettes.join(', ') || 'aucune'} → ${b.etiquettes.join(', ') || 'aucune'}`
    );
  const droitsA = new Map(a.droits.map((d) => [d.code, d]));
  const droitsB = new Map(b.droits.map((d) => [d.code, d]));
  for (const [code, d] of droitsB) {
    const v = droitsA.get(code);
    if (!v) out.push(`droit ${code} ajouté (${d.role}, ${d.sens})`);
    else {
      if (v.role !== d.role) out.push(`droit ${code} : ${v.role} → ${d.role}`);
      if (v.sens !== d.sens) out.push(`droit ${code} : ${v.sens} → ${d.sens}`);
      if (!egal(v.sources, d.sources)) out.push(`droit ${code} : sources modifiées`);
      if (v.justification !== d.justification) out.push(`droit ${code} : justification modifiée`);
    }
  }
  for (const code of droitsA.keys()) if (!droitsB.has(code)) out.push(`droit ${code} retiré`);
  if (!egal(a.vigilance, b.vigilance)) out.push('points de vigilance modifiés');
  for (const k of Object.keys(b.sources))
    if (!(k in a.sources)) out.push(`source ${k} ajoutée`);
    else if (!egal(a.sources[k], b.sources[k])) out.push(`source ${k} modifiée`);
  for (const k of Object.keys(a.sources)) if (!(k in b.sources)) out.push(`source ${k} retirée`);
  const scrA = new Map(a.scrutins.map((s) => [s.id, s]));
  const scrB = new Map(b.scrutins.map((s) => [s.id, s]));
  for (const [id, s] of scrB) {
    const v = scrA.get(id);
    if (!v) out.push(`scrutin ${id} retenu (${s.role}, ${s.pour})`);
    else if (v.role !== s.role || v.pour !== s.pour)
      out.push(`scrutin ${id} : ${v.role}, ${v.pour} → ${s.role}, ${s.pour}`);
    else if (v.objet !== s.objet) out.push(`scrutin ${id} : objet modifié`);
  }
  for (const id of scrA.keys()) if (!scrB.has(id)) out.push(`scrutin ${id} retiré`);
  if (!egal(a.senat, b.senat)) out.push('vote du Sénat modifié');
  return out;
}
