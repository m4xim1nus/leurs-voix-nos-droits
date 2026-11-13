// Étapes de la fiche et liste « Avant de valider » : une lecture en clair de ce qui manque.
// Elles ne remplacent pas les contrôles (`valider`, `validerSuivi`), dont les messages sont
// partagés avec `lvnd check` : ce sont eux qui bloquent. Ici, on ne fait que guider.

import { libelleCourt } from './format';
import type { Grille, Qualification, Statut } from './types';

export interface Point {
  ok: boolean;
  texte: string;
}

export interface Etape {
  /** Ancre du titre de la section sur la fiche. */
  ancre: string;
  titre: string;
  points: Point[];
}

export const ANCRES = {
  texte: 'etape-texte',
  droits: 'etape-droits',
  sources: 'etape-sources',
  scrutins: 'etape-scrutins',
  ecart: 'etape-ecart'
} as const;

export const aFaire = (e: Etape) => e.points.filter((p) => !p.ok).length;

export function etapes(t: Qualification, grille: Grille, statut: Statut, motif: string): Etape[] {
  if (statut === 'ecarte')
    return [
      {
        ancre: ANCRES.ecart,
        titre: 'Motif de l’écart',
        points: [{ ok: Boolean(motif.trim()), texte: 'Dire pourquoi ce texte n’est pas qualifié' }]
      }
    ];

  const suivi = statut === 'a-suivre';
  const libelles = new Map(grille.droits.map((d) => [d.code, libelleCourt(d.libelle)]));
  const nom = (code: string) => libelles.get(code) ?? 'droit à choisir';
  const droits = t.droits ?? [];
  const seul = t.senat?.version === 'seul';

  // 1. Le texte
  const texte: Etape = {
    ancre: ANCRES.texte,
    titre: 'Le texte',
    points: [
      { ok: Boolean(t.id), texte: 'Donner un identifiant public' },
      { ok: Boolean((t.titre ?? '').trim()), texte: 'Donner un titre affiché' }
    ]
  };

  // 2. Droits touchés
  const pointsDroits: Point[] = [];
  if (!(seul && !suivi && !droits.length)) {
    pointsDroits.push({ ok: droits.length > 0, texte: 'Ajouter au moins un droit touché' });
    const sansCode = droits.filter((d) => !libelles.has(d.code)).length;
    if (sansCode)
      pointsDroits.push({
        ok: false,
        texte:
          sansCode > 1
            ? `Choisir le droit dans ${sansCode} lignes`
            : 'Choisir le droit dans la liste'
      });
    if (!suivi && droits.length) {
      const n = droits.filter((d) => d.role === 'principal').length;
      pointsDroits.push({
        ok: n === 1,
        texte:
          n > 1 ? `Garder un seul droit principal (${n} aujourd’hui)` : 'Choisir le droit principal'
      });
    }
  }
  const droitsEtape: Etape = {
    ancre: ANCRES.droits,
    titre: 'Droits touchés',
    points: pointsDroits
  };

  // 3. Sources
  const pointsSources: Point[] = droits.map((d) => ({
    ok: (d.sources ?? []).length > 0,
    texte: `Citer une source pour « ${nom(d.code)} »`
  }));
  for (const [cle, s] of Object.entries(t.sources ?? {})) {
    const manque = [
      !(s.url ?? '').startsWith('http') && 'le lien',
      !s.auteur && 'l’auteur',
      !s.titre && 'le titre'
    ].filter(Boolean);
    if (manque.length)
      pointsSources.push({ ok: false, texte: `Source « ${cle} » : ajouter ${manque.join(', ')}` });
  }
  const sourcesEtape: Etape = { ancre: ANCRES.sources, titre: 'Sources', points: pointsSources };

  if (suivi) return [texte, droitsEtape, sourcesEtape];

  // 4. Le vote qui compte
  const scrutins = t.scrutins ?? [];
  const nDecisifs = scrutins.filter((s) => s.role === 'decisif').length;
  const censure = scrutins.some((s) => s.role === 'censure');
  const pointsVote: Point[] = seul
    ? [
        {
          ok: nDecisifs === 0,
          texte: 'Pas de vote décisif à l’Assemblée (texte voté au seul Sénat)'
        }
      ]
    : [
        {
          ok: nDecisifs === 1 || (nDecisifs === 0 && censure),
          texte:
            nDecisifs > 1
              ? `Garder un seul vote décisif (${nDecisifs} aujourd’hui)`
              : 'Choisir le vote qui compte : le dernier vote de l’Assemblée sur l’ensemble du texte'
        }
      ];
  const n = scrutins.filter((s) => s.pour === 'a-trancher').length;
  if (n)
    pointsVote.push({
      ok: false,
      texte: `Fixer le sens de ${n > 1 ? `${n} votes retenus` : 'un vote retenu'} (sinon il ne compte pas)`
    });
  const vote: Etape = { ancre: ANCRES.scrutins, titre: 'Le vote qui compte', points: pointsVote };

  return [texte, droitsEtape, sourcesEtape, vote];
}
