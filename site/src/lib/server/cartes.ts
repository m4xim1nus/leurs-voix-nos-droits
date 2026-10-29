// Cartes partageables (docs/CONCEPTION.md, Site public) : deux images par député et par groupe,
// 1200 × 630 pour l'aperçu des liens (og:image), 1080 × 1350 (4:5) pour les réseaux. SVG construit
// ici, rendu en PNG par resvg au prérendu, avec les polices du site en TTF statique
// (scripts/polices/ : resvg ne lit ni le WOFF2 ni les axes variables).

import { resolve } from 'node:path';
import { Resvg } from '@resvg/resvg-js';
import { circonscription, depute, legislature, pluriel, pourcent } from '$lib/format';
import { URL_SITE } from '$lib/site';
import { vueDepute, vueGroupe } from './vues';

const POLICES = ['archivo-etroit-800.ttf', 'archivo-500.ttf'].map((f) =>
  resolve(process.cwd(), 'scripts/polices', f)
);

const L = 1200;
const H = 630;
const MARGE = 72;
const ENCRE = '#15171c';
const ARDOISE = '#5b606b';
const FAVORABLE = '#0b6e78';
const DEFAVORABLE = '#b0325f';

const echapper = (s: string) =>
  s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

export interface Repere {
  libelle: string;
  couleur: string;
  score: number;
}

export interface Carte {
  titre: string;
  sousTitre: string;
  score: number | null;
  nTextes: number;
  /** Repères sur la règle : l'entité elle-même d'abord, puis éventuellement son groupe. */
  reperes: Repere[];
  /** Droits le plus et le moins favorables, s'ils diffèrent. */
  extremes?: { haut: Repere; bas: Repere } | null;
  chemin: string;
}

/** La règle graduée de 0 à 100 %, un curseur par repère, et la légende des repères dessous. */
function regle(reperes: Repere[], y: number, largeur = L): string {
  const x0 = MARGE;
  const x1 = largeur - MARGE;
  const x = (s: number) => x0 + ((x1 - x0) * s) / 100;
  const parts = [
    `<line x1="${x0}" y1="${y}" x2="${x1}" y2="${y}" stroke="${ENCRE}" stroke-width="3"/>`
  ];
  for (let g = 0; g <= 100; g += 10) {
    const h = g % 50 === 0 ? 18 : 9;
    parts.push(
      `<line x1="${x(g)}" y1="${y - h}" x2="${x(g)}" y2="${y}" stroke="${g % 50 ? ARDOISE : ENCRE}" stroke-width="2"/>`
    );
  }
  parts.push(
    `<text x="${x0}" y="${y + 36}" font-size="22" fill="${DEFAVORABLE}" font-weight="500">0 %</text>`,
    `<text x="${x(50)}" y="${y + 36}" font-size="22" fill="${ARDOISE}" text-anchor="middle" font-weight="500">50 %</text>`,
    `<text x="${x1}" y="${y + 36}" font-size="22" fill="${FAVORABLE}" text-anchor="end" font-weight="500">100 %</text>`
  );
  // Le premier repère (l'entité) est plein et haut, les suivants (son groupe) creux et plus bas ;
  // on dessine l'entité en dernier pour qu'elle reste visible si les deux se superposent.
  let lx = x0;
  reperes.forEach((r, i) => {
    const marque = (cx: number, cy: number) =>
      i === 0
        ? `<rect x="${cx - 8}" y="${cy - 30}" width="16" height="48" rx="2" fill="${echapper(r.couleur)}" stroke="${ENCRE}" stroke-width="3"/>`
        : `<rect x="${cx - 7}" y="${cy - 20}" width="14" height="32" rx="2" fill="#ffffff" stroke="${echapper(r.couleur)}" stroke-width="4"/>`;
    parts.splice(i === 0 ? parts.length : 1, 0, marque(x(r.score), y));
    parts.push(
      marque(lx + 8, y + 110)
        .replace(/height="48"/, 'height="30"')
        .replace(/height="32"/, 'height="24"'),
      `<text x="${lx + 26}" y="${y + 104}" font-size="24" fill="${i ? ARDOISE : ENCRE}" font-weight="500">${echapper(`${r.libelle} : ${pourcent(r.score).replace('\u202f', ' ')}`)}</text>`
    );
    lx += 60 + 13 * (r.libelle.length + 7);
  });
  return parts.join('');
}

/** Largeur approchée du chiffre clé en Archivo étroit gras (chiffres, espace, %). */
const largeurScore = (texte: string, taille: number) =>
  taille * [...texte].reduce((n, c) => n + (c === '%' ? 0.66 : c === ' ' ? 0.2 : 0.5), 0);

const ligneExtreme = (titre: string, r: Repere, x: number, y: number) =>
  ligne(
    /^\d+ droits$/.test(r.libelle) ? titre.replace(/^Le (\w+) (\w+)$/, 'Les $1 $2s') : titre,
    r,
    x,
    y
  );
const ligne = (titre: string, r: Repere, x: number, y: number) =>
  `<text x="${x}" y="${y}" font-size="23" font-weight="500" fill="${ARDOISE}">${titre} : <tspan fill="${ENCRE}">${echapper(r.libelle)}, ${pourcent(r.score).replace('\u202f', ' ')}</tspan></text>`;

export function svgCarte(c: Carte): string {
  const taille = c.titre.length > 26 ? 60 : 84;
  const chiffre = c.score === null ? '' : pourcent(c.score).replace('\u202f', ' ');
  const xd = MARGE + largeurScore(chiffre, 160) + 28;
  const score =
    c.score === null
      ? `<text x="${MARGE}" y="380" font-size="44" font-weight="500" fill="${ENCRE}">Aucun vote compté</text>`
      : `<text x="${MARGE}" y="410" font-weight="800" font-stretch="condensed" font-size="160" fill="${ENCRE}">${chiffre}</text>
  <text x="${xd}" y="${c.extremes ? 316 : 356}" font-size="30" font-weight="500" fill="${ENCRE}">de votes favorables aux droits</text>
  <text x="${xd}" y="${c.extremes ? 354 : 398}" font-size="30" font-weight="500" fill="${ARDOISE}">sur ${pluriel(c.nTextes, 'texte qualifié', 'textes qualifiés')}</text>${c.extremes ? ligneExtreme('Le plus favorable', c.extremes.haut, xd, 398) + ligneExtreme('Le moins favorable', c.extremes.bas, xd, 430) : ''}`;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${L}" height="${H}" viewBox="0 0 ${L} ${H}" font-family="Archivo">
  <rect width="${L}" height="${H}" fill="#ffffff"/>
  <rect width="${L}" height="14" fill="${ENCRE}"/>
  <text x="${MARGE}" y="78" font-weight="800" font-stretch="condensed" font-size="30" fill="${ENCRE}">Leurs voix, nos droits</text>
  <text x="${L - MARGE}" y="78" font-size="22" font-weight="500" fill="${ARDOISE}" text-anchor="end">${echapper(URL_SITE.replace('https://', '') + c.chemin)}</text>
  <text x="${MARGE}" y="${taille > 60 ? 178 : 168}" font-weight="800" font-stretch="condensed" font-size="${taille}" fill="${ENCRE}">${echapper(c.titre)}</text>
  <text x="${MARGE}" y="226" font-size="28" font-weight="500" fill="${ARDOISE}">${echapper(c.sousTitre)}</text>
  ${score}
  ${c.score === null ? '' : regle(c.reperes, 486)}
</svg>`;
}

/** Coupe un titre en lignes d'au plus `n` caractères, aux espaces. */
export function lignes(titre: string, n: number): string[] {
  const out: string[] = [];
  for (const mot of titre.split(' ')) {
    const der = out.at(-1);
    if (der !== undefined && `${der} ${mot}`.length <= n) out[out.length - 1] = `${der} ${mot}`;
    else out.push(mot);
  }
  return out;
}

/** Format portrait 1080 × 1350 (4:5), pour les réseaux sociaux. */
export function svgPortrait(c: Carte): string {
  const W = 1080;
  const HP = 1350;
  let taille = 96;
  let titre = lignes(c.titre, 20);
  if (titre.length > 2) [taille, titre] = [68, lignes(c.titre, 28)];
  const yTitre = 250;
  const ySous = yTitre + (titre.length - 1) * taille * 1.02 + 62;
  const chiffre = c.score === null ? '' : pourcent(c.score).replace('\u202f', ' ');
  const corps =
    c.score === null
      ? `<text x="${MARGE}" y="${ySous + 200}" font-size="48" font-weight="500" fill="${ENCRE}">Aucun vote compté</text>`
      : `<text x="${MARGE}" y="${ySous + 300}" font-weight="800" font-stretch="condensed" font-size="260" fill="${ENCRE}">${chiffre}</text>
  <text x="${MARGE}" y="${ySous + 372}" font-size="40" font-weight="500" fill="${ENCRE}">de votes favorables aux droits</text>
  <text x="${MARGE}" y="${ySous + 424}" font-size="40" font-weight="500" fill="${ARDOISE}">sur ${pluriel(c.nTextes, 'texte qualifié', 'textes qualifiés')}</text>${c.extremes ? ligneExtreme('Le plus favorable', c.extremes.haut, MARGE, ySous + 492).replace('font-size="23"', 'font-size="30"') + ligneExtreme('Le moins favorable', c.extremes.bas, MARGE, ySous + 534).replace('font-size="23"', 'font-size="30"') : ''}
  ${regle(c.reperes, 1110, W)}`;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${HP}" viewBox="0 0 ${W} ${HP}" font-family="Archivo">
  <rect width="${W}" height="${HP}" fill="#ffffff"/>
  <rect width="${W}" height="16" fill="${ENCRE}"/>
  <text x="${MARGE}" y="104" font-weight="800" font-stretch="condensed" font-size="38" fill="${ENCRE}">Leurs voix, nos droits</text>
  ${titre.map((l, i) => `<text x="${MARGE}" y="${yTitre + i * taille * 1.02}" font-weight="800" font-stretch="condensed" font-size="${taille}" fill="${ENCRE}">${echapper(l)}</text>`).join('')}
  <text x="${MARGE}" y="${ySous}" font-size="32" font-weight="500" fill="${ARDOISE}">${echapper(c.sousTitre)}</text>
  ${corps}
  <text x="${MARGE}" y="${HP - 48}" font-size="26" font-weight="500" fill="${ARDOISE}">${echapper(URL_SITE.replace('https://', '') + c.chemin)}</text>
</svg>`;
}

/** Carte d'un député : nom, situation, score, droits extrêmes, son groupe sur la règle. */
export function carteDepute(slug: string): Carte {
  const v = vueDepute(slug);
  const d = v.depute;
  const ou = v.mandat ? `${v.mandat.departement}, ${circonscription(v.mandat.num_circo)}` : '';
  const qui = v.actuel
    ? depute(d.civ, true)
    : d.civ === 'Mme'
      ? 'Ancienne députée'
      : 'Ancien député';
  const reperes: Repere[] = [];
  if (v.global?.score != null)
    reperes.push({ libelle: d.nom, couleur: v.groupe?.couleur ?? ENCRE, score: v.global.score });
  if (v.lignee && v.scoreGroupe?.score != null)
    reperes.push({
      libelle: `groupe ${v.lignee.sigle}`,
      couleur: v.lignee.couleur,
      score: v.scoreGroupe.score
    });
  return {
    titre: `${d.prenom} ${d.nom}`,
    sousTitre: `${qui}${v.groupe ? ` ${v.groupe.sigle}` : ''}${ou ? `, ${ou}` : ''}`,
    score: v.global?.score ?? null,
    nTextes: v.global?.n_textes ?? 0,
    reperes,
    extremes: extremes(v.droits.map((x) => ({ libelle: x.droit.court, score: x.score.score }))),
    chemin: `/deputes/${d.slug}`
  };
}

/** Carte d'un groupe. */
export function carteGroupe(slug: string): Carte {
  const v = vueGroupe(slug);
  const g = v.groupe;
  return {
    titre: g.nom,
    sousTitre: `Groupe ${g.sigle}, ${legislature(g.legislature)} législature`,
    score: v.global?.score ?? null,
    nTextes: v.global?.n_textes ?? 0,
    extremes: extremes(v.droits.map((x) => ({ libelle: x.droit.court, score: x.score.score }))),
    reperes:
      v.global?.score != null
        ? [{ libelle: g.sigle, couleur: g.couleur, score: v.global.score }]
        : [],
    chemin: `/groupes/${g.slug}`
  };
}

/** Réponse PNG d'une route de carte. */
export const reponsePng = (svg: string) =>
  new Response(Buffer.from(png(svg)), { headers: { 'content-type': 'image/png' } });

export function png(svg: string): Uint8Array {
  return new Resvg(svg, {
    font: { fontFiles: POLICES, loadSystemFonts: false, defaultFontFamily: 'Archivo' },
    fitTo: { mode: 'original' }
  })
    .render()
    .asPng();
}

/**
 * Droits le plus et le moins favorables parmi ceux qui ont un score ; à égalité, leur nombre
 * (« 4 droits ») plutôt qu'un nom pris au hasard. null si tous les scores sont égaux.
 */
export function extremes(droits: { libelle: string; score: number | null }[]) {
  const notes = droits.filter((d): d is { libelle: string; score: number } => d.score !== null);
  if (notes.length < 2) return null;
  const max = Math.max(...notes.map((d) => d.score));
  const min = Math.min(...notes.map((d) => d.score));
  if (max === min) return null;
  const repere = (score: number): Repere => {
    const ex = notes.filter((d) => d.score === score);
    return { libelle: ex.length === 1 ? ex[0].libelle : `${ex.length} droits`, score, couleur: '' };
  };
  return { haut: repere(max), bas: repere(min) };
}
