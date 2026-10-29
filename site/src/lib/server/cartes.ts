// Cartes partageables (docs/CONCEPTION.md, Site public) : une image 1200 × 630 par député et par
// groupe, pour l'aperçu des liens (og:image) et le bouton « Télécharger l'image ». SVG construit
// ici, rendu en PNG par resvg au prérendu, avec les polices du site en TTF statique
// (scripts/polices/ : resvg ne lit ni le WOFF2 ni les axes variables).

import { resolve } from 'node:path';
import { Resvg } from '@resvg/resvg-js';
import { pluriel, pourcent } from '$lib/format';
import { URL_SITE } from '$lib/site';

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
  chemin: string;
}

/** La règle graduée de 0 à 100 %, un curseur par repère, et la légende des repères dessous. */
function regle(reperes: Repere[], y: number): string {
  const x0 = MARGE;
  const x1 = L - MARGE;
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

export function svgCarte(c: Carte): string {
  const taille = c.titre.length > 26 ? 60 : 84;
  const chiffre = c.score === null ? '' : pourcent(c.score).replace('\u202f', ' ');
  const xd = MARGE + largeurScore(chiffre, 160) + 28;
  const score =
    c.score === null
      ? `<text x="${MARGE}" y="380" font-size="44" font-weight="500" fill="${ENCRE}">Aucun vote compté</text>`
      : `<text x="${MARGE}" y="410" font-weight="800" font-stretch="condensed" font-size="160" fill="${ENCRE}">${chiffre}</text>
  <text x="${xd}" y="356" font-size="30" font-weight="500" fill="${ENCRE}">de votes favorables aux droits</text>
  <text x="${xd}" y="398" font-size="30" font-weight="500" fill="${ARDOISE}">sur ${pluriel(c.nTextes, 'texte qualifié', 'textes qualifiés')}</text>`;
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

export function png(svg: string): Uint8Array {
  return new Resvg(svg, {
    font: { fontFiles: POLICES, loadSystemFonts: false, defaultFontFamily: 'Archivo' },
    fitTo: { mode: 'original' }
  })
    .render()
    .asPng();
}
