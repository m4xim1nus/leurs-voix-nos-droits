import { describe, expect, it } from 'vitest';
import { phraseOrigine, pointsFrise, resumeFrise } from './frise';
import type { EtapeParcours, EtatTexte, OrigineTexte, Parcours } from './types';

const SANS_LOI = { numero: null, dateLoi: null, ccUrl: null, ccNumero: null };
const etat = (e: Partial<EtatTexte>): EtatTexte => ({
  etat: 'loi',
  attente: null,
  attente_chambre: null,
  date_derniere_lecture: null,
  date_derniere_activite: null,
  seance_inscrite: null,
  ...e
});
const etape = (e: Partial<EtapeParcours>): EtapeParcours => ({
  etape: 'lecture',
  chambre: 'AN',
  lecture: 'premiere',
  date: '2023-02-01',
  issue: 'adopte',
  detail: null,
  ...e
});
const gouv: OrigineTexte = {
  type: 'gouvernement',
  auteur: null,
  groupe: null,
  cosignataires: null,
  chambre: 'AN',
  date: '2023-01-02'
};
const groupe = { id: 'PO1', sigle: 'ABC', nom: 'Groupe Abc', couleur: '#123456' };

describe('origine', () => {
  it('un projet de loi vient du gouvernement', () => {
    expect(phraseOrigine(gouv)).toBe('Texte déposé par le gouvernement à l’Assemblée nationale');
  });
  it('une proposition dit l’auteur·ice et son groupe', () => {
    const p = pointsFrise(
      {
        origine: {
          type: 'parlementaire',
          auteur: { nom: 'Jeanne Martin', slug: 'jeanne-martin' },
          groupe,
          cosignataires: 3,
          chambre: 'AN',
          date: '2024-09-10'
        },
        etapes: []
      },
      null,
      SANS_LOI
    )[0];
    expect(p.precision).toContain('Jeanne Martin');
    expect(p.precision).toContain('du groupe Groupe Abc');
    expect(p.precision).toContain('3 cosignataires');
    expect(p.groupe?.sigle).toBe('ABC');
    expect(p.lien?.href).toBe('/deputes/jeanne-martin');
  });
  it('sans groupe connu (Sénat), reste sobre', () => {
    const p = pointsFrise(
      {
        origine: { ...gouv, type: 'parlementaire', chambre: 'SN', cosignataires: 0 },
        etapes: []
      },
      null,
      SANS_LOI
    )[0];
    expect(p.precision).toBe('Texte déposé au Sénat par des parlementaires.');
    expect(p.groupe).toBeNull();
  });
});

describe('pointsFrise', () => {
  it('rend rien sans données : pas de frise inventée', () => {
    expect(pointsFrise(null, etat({}), SANS_LOI)).toEqual([]);
    expect(pointsFrise({ origine: null, etapes: [] }, etat({}), SANS_LOI)).toEqual([]);
  });

  it('une loi : dépôt, lectures, CMP, Conseil constitutionnel, promulgation', () => {
    const parcours: Parcours = {
      origine: gouv,
      etapes: [
        etape({}),
        etape({ chambre: 'SN', date: '2023-03-01' }),
        etape({ etape: 'cmp', chambre: null, lecture: null, issue: 'accord', date: '2023-04-01' }),
        etape({
          etape: 'cc',
          chambre: null,
          lecture: null,
          issue: null,
          detail: 'Partiellement conforme',
          date: '2023-05-01'
        }),
        etape({
          etape: 'promulgation',
          chambre: null,
          lecture: null,
          issue: null,
          detail: '2023-100',
          date: '2023-05-10'
        })
      ]
    };
    const pts = pointsFrise(parcours, etat({ etat: 'loi' }), {
      numero: '2023-100',
      dateLoi: '2023-05-10',
      ccUrl: 'https://cc.example/decision',
      ccNumero: '2023-1 DC'
    });
    expect(pts.map((p) => p.titre)).toEqual([
      'Dépôt',
      '1re lecture à l’Assemblée nationale',
      '1re lecture au Sénat',
      'Commission mixte paritaire',
      'Conseil constitutionnel',
      'Promulgation'
    ]);
    expect(pts[4].resultat).toBe('Partiellement conforme');
    expect(pts[4].lien).toEqual({
      href: 'https://cc.example/decision',
      texte: 'Décision n° 2023-1 DC'
    });
    expect(pts[5].resultat).toBe('Loi n° 2023-100');
    expect(pts.some((p) => p.statut !== 'fait')).toBe(false);
  });

  it('une promulgation absente du fichier est reprise du catalogue', () => {
    const pts = pointsFrise({ origine: gouv, etapes: [] }, etat({ etat: 'loi' }), {
      ...SANS_LOI,
      numero: '2019-744',
      dateLoi: '2019-07-19'
    });
    expect(pts.at(-1)?.resultat).toBe('Loi n° 2019-744');
  });

  it('un rejet et un désaccord sont marqués, sans couleur seule', () => {
    const pts = pointsFrise(
      {
        origine: gouv,
        etapes: [
          etape({ issue: 'rejete' }),
          etape({ etape: 'cmp', chambre: null, lecture: null, issue: 'desaccord' })
        ]
      },
      etat({ etat: 'rejete' }),
      SANS_LOI
    );
    expect(pts[1]).toMatchObject({ statut: 'bloque', resultat: 'Rejeté' });
    expect(pts[2].statut).toBe('bloque');
    expect(pts.at(-1)).toMatchObject({ titre: 'Rejeté', statut: 'bloque' });
  });

  it('un texte en navette finit sur ce qu’il attend, sans date', () => {
    const pts = pointsFrise(
      { origine: gouv, etapes: [etape({})] },
      etat({ etat: 'en_navette', attente: 'lecture', attente_chambre: 'SN' }),
      SANS_LOI
    );
    expect(pts.at(-1)).toMatchObject({
      titre: 'En cours d’examen',
      resultat: 'Attendu au Sénat',
      statut: 'attente',
      date: null
    });
  });

  it('un texte à l’arrêt dit depuis quand', () => {
    const pts = pointsFrise(
      { origine: gouv, etapes: [] },
      etat({ etat: 'a_l_arret', date_derniere_activite: '2025-01-15' }),
      SANS_LOI
    );
    expect(pts.at(-1)?.precision).toBe('Aucun acte depuis le 15 janvier 2025.');
  });

  it('une loi n’a pas de point d’issue en plus', () => {
    const pts = pointsFrise(
      { origine: gouv, etapes: [] },
      etat({ etat: 'hors_navette' }),
      SANS_LOI
    );
    expect(pts).toHaveLength(1);
  });

  it('le résumé pour lecteur d’écran nomme la dernière étape', () => {
    const pts = pointsFrise({ origine: gouv, etapes: [etape({})] }, null, SANS_LOI);
    expect(resumeFrise(pts)).toBe(
      '2 étapes. Dernière étape : 1re lecture à l’Assemblée nationale, le 1er février 2023.'
    );
    expect(resumeFrise([])).toBe('');
  });
});
