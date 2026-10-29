import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import {
  compact,
  differences,
  documentEditorial,
  empreinte,
  normaliser,
  serialiser,
  slug,
  valider
} from './qualification';
import type { Editorial, Grille, Qualification } from './types';

const RACINE = new URL('../../../', import.meta.url);
const brut = readFileSync(new URL('data/editorial.json', RACINE), 'utf8');
const editorial: Editorial = JSON.parse(brut);

// Grille v0 (pipeline/referentiels/droits.yaml), codes seulement.
const GRILLE: Grille = {
  version: 0,
  droits: [
    'libertes',
    'police-justice',
    'vie-privee',
    'etrangers',
    'discriminations',
    'femmes-lgbti',
    'enfants',
    'logement',
    'travail-protection-sociale',
    'environnement',
    'sante'
  ].map((code) => ({ code, libelle: code })),
  etiquettes: ['outre-mer', 'regime-exception'].map((code) => ({ code, libelle: code })),
  sens: []
};

function texte(p: Partial<Qualification> = {}): Qualification {
  return normaliser({
    id: 't',
    dossier_an: 'DLR5L17N1',
    legislature: 17,
    titre: 'Loi',
    droits: [
      {
        code: 'vie-privee',
        role: 'principal',
        sens: 'restreint',
        sources: ['s1'],
        justification: ''
      }
    ],
    sources: { s1: { auteur: 'CNIL', titre: 'Avis', date: '2024-01-01', url: 'https://cnil.fr' } },
    scrutins: [{ id: 'D', role: 'decisif', pour: 'texte', objet: 'ensemble' }],
    ...p
  });
}

describe('qualification', () => {
  it("réécrit data/editorial.json à l'octet près (même sérialisation que le pipeline)", () => {
    const melange = [...editorial.textes].reverse();
    expect(serialiser(documentEditorial(editorial.grille, melange, editorial.ecartes))).toBe(brut);
  });

  it('valide les textes témoins', () => {
    for (const t of editorial.textes) expect(valider(t, GRILLE).erreurs, t.id).toEqual([]);
    const am = editorial.textes.find((t) => t.id === 'aide-a-mourir')!;
    expect(valider(am, GRILLE).avertissements).toEqual([]);
    const nt = editorial.textes.find((t) => t.id === 'narcotrafic')!;
    expect(valider(nt, GRILLE).avertissements).toEqual([
      'source lqdn-2025-06 définie mais citée nulle part'
    ]);
  });

  it('signale les erreurs bloquantes, avec les messages du pipeline', () => {
    expect(valider(texte(), GRILLE)).toEqual({ erreurs: [], avertissements: [] });
    expect(valider(texte({ droits: [] }), GRILLE).erreurs).toContain(
      'il faut exactement un droit principal'
    );
    expect(
      valider(
        texte({
          droits: [
            { code: 'inconnu', role: 'principal', sens: 'etend', sources: [], justification: '' }
          ]
        }),
        GRILLE
      ).erreurs
    ).toEqual(expect.arrayContaining(['droit inconnu : inconnu', 'inconnu : aucune source']));
    expect(valider(texte({ scrutins: [] }), GRILLE).erreurs).toContain(
      'il faut exactement un scrutin décisif (ou, pour un texte adopté par 49.3 sans vote final, au moins une motion de censure)'
    );
    expect(valider(texte({ sources: {} }), GRILLE).erreurs).toContain(
      'source citée mais non définie : s1'
    );
  });

  it('contrôle les scrutins sur le catalogue', () => {
    const infos = new Map([
      ['D', { dossier_id: 'DLR5L17N1', etape: 'AN1', division: null }],
      ['A1', { dossier_id: 'DLR5L17N1', etape: 'AN1', division: 'Article 7' }],
      ['A2', { dossier_id: 'DLR5L17N1', etape: 'AN1', division: 'Article 7' }],
      ['X', { dossier_id: 'DLR5L17N2', etape: 'AN1', division: null }]
    ]);
    const { erreurs } = valider(
      texte({
        scrutins: [
          { id: 'D', role: 'decisif', pour: 'texte', objet: '' },
          { id: 'A1', role: 'amendement', pour: 'contre-texte', objet: '' },
          { id: 'A2', role: 'amendement', pour: 'contre-texte', objet: '' },
          { id: 'X', role: 'motion', pour: 'texte', objet: '' }
        ]
      }),
      GRILLE,
      infos
    );
    expect(erreurs).toContain('X : scrutin absent du dossier DLR5L17N1');
    expect(erreurs.some((e) => e.startsWith('plusieurs amendements clés sur « Article 7 »'))).toBe(
      true
    );
  });

  it("refuse un amendement clé unanime ou la suppression d'un article unique (règle 11)", () => {
    const infos = new Map([
      [
        'D',
        {
          dossier_id: 'DLR5L17N1',
          etape: 'AN1',
          division: null,
          objet: 'ensemble',
          pour: 10,
          contre: 5
        }
      ],
      [
        'U',
        {
          dossier_id: 'DLR5L17N1',
          etape: 'AN1',
          division: 'Article 2',
          objet: 'amendement',
          pour: 0,
          contre: 46
        }
      ],
      [
        'S',
        {
          dossier_id: 'DLR5L17N1',
          etape: 'AN1',
          division: null,
          objet: 'suppression_article_unique',
          pour: 65,
          contre: 95
        }
      ]
    ]);
    const { erreurs } = valider(
      texte({
        scrutins: [
          { id: 'D', role: 'decisif', pour: 'texte', objet: '' },
          { id: 'U', role: 'amendement', pour: 'texte', objet: '' },
          { id: 'S', role: 'amendement', pour: 'contre-texte', objet: '' }
        ]
      }),
      GRILLE,
      infos
    );
    expect(erreurs).toContain('U : amendement unanime (0-46), pas un amendement clé (règle 11)');
    expect(erreurs).toContain(
      "S : suppression d'un article unique, pas un amendement clé (règle 11)"
    );
    expect(erreurs.some((e) => e.startsWith('D : décisif unanime'))).toBe(false);
  });

  it('refuse un décisif unanime (règle 9)', () => {
    const infos = new Map([
      [
        'D',
        {
          dossier_id: 'DLR5L17N1',
          etape: 'AN1',
          division: null,
          objet: 'ensemble',
          pour: 503,
          contre: 0
        }
      ]
    ]);
    const { erreurs } = valider(
      texte({ scrutins: [{ id: 'D', role: 'decisif', pour: 'texte', objet: '' }] }),
      GRILLE,
      infos
    );
    expect(erreurs).toContain('D : décisif unanime (503-0), texte à écarter (règle 9)');
  });

  it('garde les espaces insécables', () => {
    expect(texte({ conseil_constitutionnel: ' a :  b\n c ' }).conseil_constitutionnel).toBe(
      'a : b c'
    );
  });

  it('calcule la même empreinte que le pipeline', async () => {
    // pipeline : sync_admin.empreinte(compact(t), "valide", None), cf. test_editorial.py
    const t = editorial.textes.find((t) => t.id === 'jo-2024')!;
    expect(compact(t)).toBe(JSON.stringify(t));
    expect(await empreinte('{"a":1}', 'valide', null)).toBe(
      '47affe62feef3e7cc41411f95c1efd488addec899c19b772ea6f46e8de174490'
    );
  });

  it('tire un identifiant lisible du titre', () => {
    expect(slug("Loi visant à protéger les logements contre l'occupation illicite")).toBe(
      'proteger-logements-contre-occupation-illicite'
    );
  });

  it('accepte un texte adopté par 49.3 : motions de censure sans décisif (règle 9)', () => {
    const censure = [
      { id: 'C', role: 'censure' as const, pour: 'contre-texte' as const, objet: 'censure' }
    ];
    const infos = new Map([
      [
        'C',
        {
          dossier_id: null,
          etape: null,
          division: null,
          objet: 'motion_censure',
          pour: 1,
          contre: 0
        }
      ],
      [
        'X',
        {
          dossier_id: 'DLR5L17N1',
          etape: null,
          division: null,
          objet: 'ensemble',
          pour: 1,
          contre: 1
        }
      ]
    ]);
    expect(valider(texte({ scrutins: censure }), GRILLE, infos as never).erreurs).toEqual([]);
    expect(
      valider(texte({ scrutins: [{ ...censure[0], id: 'X' }] }), GRILLE, infos as never).erreurs
    ).toEqual(['X : pas une motion de censure']);
  });
});

describe('differences', () => {
  it('liste les changements depuis la version publiée', () => {
    const avant = texte();
    const apres = texte({
      droits: [{ ...avant.droits[0], sens: 'etend' }],
      scrutins: [...avant.scrutins, { id: 'A', role: 'amendement', pour: 'a-trancher', objet: 'x' }]
    });
    expect(differences(avant, apres)).toEqual([
      `droit ${avant.droits[0].code} : restreint → etend`,
      'scrutin A retenu (amendement, a-trancher)'
    ]);
    expect(differences(avant, avant)).toEqual([]);
  });
});
