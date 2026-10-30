import { describe, expect, it } from 'vitest';
import type { TexteEnCours } from '$lib/types';
import { agendaIcal, fluxRss, plier } from './flux';

const texte = (t: Partial<TexteEnCours>): TexteEnCours => ({
  dossier_an: 'DLR5L17N1',
  id: 'x',
  titre: 'Loi « A & B », sur le logement',
  etat: {
    etat: 'en_navette',
    attente: 'lecture',
    attente_chambre: 'AN',
    date_derniere_lecture: '2026-10-21',
    date_derniere_activite: null,
    seance_inscrite: '2026-11-18'
  },
  echeance: 'inscrit',
  chambre: 'AN',
  seances: [
    { date: '2026-11-18', etat: 'confirme' },
    { date: '2026-11-19', etat: 'confirme' },
    { date: '2026-11-19', etat: 'confirme' }
  ],
  commissions: [],
  qualification: null,
  dernier_vote: null,
  vote_qualifie: false,
  ...t
});

describe('flux RSS', () => {
  it('échappe les titres et dit « inscrit »', () => {
    const r = fluxRss([texte({})], '2026-10-29');
    expect(r).toContain('A &amp; B');
    expect(r).toContain('Inscrit en séance à l’Assemblée les 18 et 19 novembre 2026.');
    expect(r).toContain('Thu, 29 Oct 2026 12:00:00 GMT');
    expect(r).not.toMatch(/sera voté/);
  });
  it('change de guid quand l’échéance change', () => {
    const avant = fluxRss([texte({})], '2026-10-29').match(/<guid.*<\/guid>/)![0];
    const apres = fluxRss([texte({ echeance: 'AN', seances: [] })], '2026-11-30').match(
      /<guid.*<\/guid>/
    )![0];
    expect(apres).not.toBe(avant);
  });
});

describe('agenda iCal', () => {
  it('crée un événement d’une journée par date de séance', () => {
    const i = agendaIcal([texte({})], '2026-10-29');
    expect(i.match(/BEGIN:VEVENT/g)).toHaveLength(2);
    expect(i).toContain('DTSTART;VALUE=DATE:20261118');
    expect(i).toContain('DTEND;VALUE=DATE:20261120');
    expect(i).toContain('UID:DLR5L17N1-2026-11-18@');
    expect(i).toContain('\r\n');
    expect(i.endsWith('END:VCALENDAR\r\n')).toBe(true);
  });
  it('n’a aucune entrée pour un texte sans date', () => {
    const e = texte({}).etat;
    const i = agendaIcal(
      [texte({ seances: [], etat: { ...e, seance_inscrite: null }, echeance: 'AN' })],
      '2026-10-29'
    );
    expect(i).not.toContain('BEGIN:VEVENT');
  });
  it('replie à 75 octets sans couper un caractère', () => {
    const p = plier(`SUMMARY:${'é'.repeat(100)}`);
    const lignes = p.split('\r\n');
    expect(lignes.length).toBeGreaterThan(1);
    for (const l of lignes) expect(new TextEncoder().encode(l).length).toBeLessThanOrEqual(75);
    expect(p.replace(/\r\n /g, '')).toBe(`SUMMARY:${'é'.repeat(100)}`);
  });
});
