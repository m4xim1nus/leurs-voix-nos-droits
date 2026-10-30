// Flux RSS et agenda iCal des textes en cours, générés au build : des textes et des dates, aucune
// donnée personnelle. Le mot est « inscrit », jamais « sera voté » (docs/QUALIFICATION.md).

import { date, etatTexte, inscription, voteDeLecture } from '$lib/format';
import { NOM, URL_SITE } from '$lib/site';
import type { TexteEnCours } from '$lib/types';

const xml = (s: string) =>
  s.replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]!);

const urlTexte = (t: TexteEnCours) => `${URL_SITE}${t.href}`;

/** Dates de séance d'un texte, et la chambre : l'agenda de l'AN, sinon la séance du dossier. */
function seances(t: TexteEnCours): { chambre: 'AN' | 'SN' | null; dates: string[] } {
  if (t.seances.length) return { chambre: 'AN', dates: t.seances.map((s) => s.date) };
  return { chambre: t.chambre, dates: t.etat.seance_inscrite ? [t.etat.seance_inscrite] : [] };
}

/** Où en est le texte, en une phrase. */
function etatEnClair(t: TexteEnCours): string {
  const { chambre, dates } = seances(t);
  return `${dates.length ? inscription(chambre, dates) : etatTexte(t.etat)}.`;
}

function dernierVote(t: TexteEnCours): string {
  const v = t.dernier_vote;
  if (!v) return 'Aucun vote public de l’Assemblée sur ce texte pour l’instant.';
  const lecture = voteDeLecture(v.etape);
  return `Dernier vote public de l’Assemblée, le ${date(v.date)}${lecture ? ` (${lecture})` : ''} : ${v.decompte.pour} pour, ${v.decompte.contre} contre, ${v.decompte.abstention} abstentions.`;
}

/** RSS 2.0. Le guid change avec l'échéance : un lecteur voit une entrée à chaque nouvelle étape. */
export function fluxRss(textes: TexteEnCours[], dateEtat: string): string {
  const pub = new Date(`${dateEtat}T12:00:00Z`).toUTCString();
  const items = textes.map((t) => {
    const { dates } = seances(t);
    const guid = `${t.dossier_an}-${t.echeance}-${dates[0] ?? t.etat.date_derniere_lecture ?? ''}`;
    return `    <item>
      <title>${xml(t.titre)}</title>
      <link>${urlTexte(t)}</link>
      <guid isPermaLink="false">${xml(guid)}</guid>
      <pubDate>${pub}</pubDate>
      <description>${xml(`${etatEnClair(t)} ${dernierVote(t)}`)}</description>
    </item>`;
  });
  return `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>${xml(`Textes en cours, ${NOM}`)}</title>
    <link>${URL_SITE}/en-cours</link>
    <atom:link href="${URL_SITE}/en-cours/flux.xml" rel="self" type="application/rss+xml" />
    <description>Les textes retenus sur ce site encore en navette : ordre du jour et dernier vote.</description>
    <language>fr</language>
    <lastBuildDate>${pub}</lastBuildDate>
${items.join('\n')}
  </channel>
</rss>
`;
}

const echappe = (s: string) =>
  s.replace(/\\/g, '\\\\').replace(/;/g, '\\;').replace(/,/g, '\\,').replace(/\n/g, '\\n');

/** Replie une ligne iCal à 75 octets (RFC 5545), sans couper un caractère. */
export function plier(ligne: string): string {
  const octets = new TextEncoder();
  const morceaux: string[] = [];
  let courant = '';
  let taille = 0;
  for (const c of ligne) {
    const n = octets.encode(c).length;
    if (taille + n > (morceaux.length ? 74 : 75)) {
      morceaux.push(courant);
      courant = '';
      taille = 0;
    }
    courant += c;
    taille += n;
  }
  morceaux.push(courant);
  return morceaux.join('\r\n ');
}

const compacte = (iso: string) => iso.replaceAll('-', '');
const lendemain = (iso: string) => {
  const d = new Date(`${iso}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + 1);
  return d.toISOString().slice(0, 10);
};

/** Un événement d'une journée par séance inscrite. Un texte sans date n'y figure pas. */
export function agendaIcal(textes: TexteEnCours[], dateEtat: string): string {
  const hote = new URL(URL_SITE).hostname;
  const lignes = [
    'BEGIN:VCALENDAR',
    'VERSION:2.0',
    `PRODID:-//${NOM}//Textes en cours//FR`,
    'CALSCALE:GREGORIAN',
    `X-WR-CALNAME:${echappe(`Textes inscrits, ${NOM}`)}`
  ];
  for (const t of textes) {
    const { chambre, dates } = seances(t);
    const ou = chambre === 'SN' ? 'au Sénat' : chambre === 'AN' ? 'à l’Assemblée' : '';
    for (const jour of [...new Set(dates)].sort())
      lignes.push(
        'BEGIN:VEVENT',
        `UID:${t.dossier_an}-${jour}@${hote}`,
        `DTSTAMP:${compacte(dateEtat)}T000000Z`,
        `DTSTART;VALUE=DATE:${compacte(jour)}`,
        `DTEND;VALUE=DATE:${compacte(lendemain(jour))}`,
        `SUMMARY:${echappe(`Inscrit en séance ${ou} : ${t.titre}`.replace(/ {2}/g, ' '))}`,
        `DESCRIPTION:${echappe(`État au ${date(dateEtat)}. Inscrit ne veut pas dire voté. ${dernierVote(t)}`)}`,
        `URL:${urlTexte(t)}`,
        'TRANSP:TRANSPARENT',
        'END:VEVENT'
      );
  }
  lignes.push('END:VCALENDAR');
  return lignes.map(plier).join('\r\n') + '\r\n';
}
