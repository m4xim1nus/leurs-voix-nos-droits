import { describe, expect, it } from 'vitest';
import {
  date,
  etatEnListe,
  etatTexte,
  inscription,
  listeDates,
  mentionNavette,
  normaliser,
  pluriel,
  pourcent,
  slug,
  sensDuPour,
  typo
} from './format';
import type { EtatTexte } from './types';

describe('format', () => {
  it('écrit les scores arrondis, avec espace insécable', () => {
    expect([pourcent(36.9), pourcent(0), pourcent(null)]).toEqual(['37\u202f%', '0\u202f%', '–']);
  });
  it('écrit les dates en toutes lettres', () => {
    expect(date('2025-05-13')).toBe('13 mai 2025');
    expect(date('2024-07-01')).toBe('1er juillet 2024');
    expect(date('2026-02')).toBe('février 2026');
  });
  it('accorde le pluriel', () => {
    expect([pluriel(0, 'texte'), pluriel(1, 'texte'), pluriel(6, 'texte')]).toEqual([
      'aucun texte',
      '1 texte',
      '6 textes'
    ]);
  });
  it('normalise les noms pour la recherche et les slugs', () => {
    expect(normaliser('Éric  CIOTTI')).toBe('eric ciotti');
    expect(slug('Marie-Agnès Poussier-Winsback')).toBe('marie-agnes-poussier-winsback');
    expect(slug('Cœur')).toBe('coeur');
  });
  it('dit ce que signifie voter pour (règle 14)', () => {
    expect(sensDuPour('contre-texte')).toContain('s’opposer');
  });
});

describe('état d’un texte', () => {
  const etat = (e: Partial<EtatTexte>): EtatTexte => ({
    etat: 'en_navette',
    attente: 'lecture',
    attente_chambre: 'SN',
    date_derniere_lecture: null,
    date_derniere_activite: null,
    seance_inscrite: null,
    ...e
  });

  it('dit où un texte en navette est attendu', () => {
    expect(etatTexte(etat({}))).toBe('En navette, attendu au Sénat');
    expect(etatTexte(etat({ attente: 'transmis', attente_chambre: 'AN' }))).toBe(
      'En navette, attendu à l’Assemblée'
    );
    expect(etatTexte(etat({ attente: 'cmp', attente_chambre: 'CMP' }))).toBe(
      'En navette, en commission mixte paritaire'
    );
    expect(etatTexte(etat({ attente: 'navette', attente_chambre: null }))).toBe(
      'En navette, suite pas encore connue'
    );
  });

  it('date un texte à l’arrêt, et ne dit rien d’un texte sans lecture', () => {
    expect(etatTexte(etat({ etat: 'a_l_arret', date_derniere_activite: '2023-05-04' }))).toBe(
      'À l’arrêt, aucun acte depuis le 4 mai 2023'
    );
    expect(etatTexte(etat({ etat: 'hors_navette' }))).toBe('');
    expect(etatTexte(null)).toBe('');
  });

  it('nomme la lecture du vote, seulement pour un texte encore en navette', () => {
    expect(mentionNavette(etat({}), 'AN1')).toBe('vote de 1re lecture, texte encore en navette');
    expect(mentionNavette(etat({}), 'AN2')).toBe('vote de 2e lecture, texte encore en navette');
    expect(mentionNavette(etat({}), 'CMP')).toBe(
      'vote sur le texte de CMP, texte encore en navette'
    );
    expect(mentionNavette(etat({}), null)).toBe('texte encore en navette');
    expect(mentionNavette(etat({ etat: 'loi' }), 'AN1')).toBeNull();
    expect(mentionNavette(etat({ etat: 'a_l_arret' }), 'AN1')).toBeNull();
  });

  it('écrit les dates d’inscription sans répéter le mois, et jamais « sera voté »', () => {
    expect(listeDates(['2026-11-19', '2026-11-18', '2026-11-19'])).toBe('18 et 19 novembre 2026');
    expect(listeDates(['2026-11-30', '2026-12-01'])).toBe('30 novembre 2026 et 1er décembre 2026');
    expect(inscription('AN', ['2026-11-18', '2026-11-19'])).toBe(
      'Inscrit en séance à l’Assemblée les 18 et 19 novembre 2026'
    );
    expect(inscription('SN', ['2026-11-01'])).toBe(
      'Inscrit en séance au Sénat le 1er novembre 2026'
    );
  });

  it('réunit la mention et l’attente dans une liste', () => {
    expect(etatEnListe(etat({}), 'AN1')).toBe(
      'Vote de 1re lecture, texte encore en navette, attendu au Sénat'
    );
    expect(etatEnListe(etat({ etat: 'loi' }), 'AN1')).toBe('Loi promulguée');
  });
});

describe('typo', () => {
  it('pose les espaces insécables sans toucher au reste', () => {
    expect(typo('Censure : article 7 ; « VSA » validée ? Oui !')).toBe(
      'Censure : article 7 ; « VSA » validée ? Oui !'
    );
    expect(typo('https://x.fr/a:b')).toBe('https://x.fr/a:b');
  });
});
