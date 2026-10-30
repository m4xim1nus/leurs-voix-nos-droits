// Ce que reçoit chaque page : des extraits de `donnees()`, sérialisables et sans calcul de score.

import { error } from '@sveltejs/kit';
import { donnees, type Donnees } from './donnees';
import type {
  Depute,
  EntreeIndex,
  EtatTexte,
  GroupeCourt,
  Lignee,
  Position,
  Score,
  ScrutinRetenu,
  Sens,
  Texte,
  TexteEnCours,
  Ventilation
} from '$lib/types';

export interface TexteCourt {
  id: string;
  titre: string;
  date: string;
  legislature: number;
  principal: { code: string; sens: Sens };
  droits: { code: string; role: string; sens: Sens }[];
  etiquettes: string[];
  n_comptes: number;
  sans_vote: boolean;
  etat: EtatTexte | null;
  /** Lecture du vote décisif. */
  etape: string | null;
}

export const court = (t: Texte): TexteCourt => ({
  id: t.id,
  titre: t.titre,
  date: t.date,
  legislature: t.legislature,
  principal: { code: t.principal.code, sens: t.principal.sens },
  droits: t.droits.map((d) => ({ code: d.code, role: d.role, sens: d.sens })),
  etiquettes: t.etiquettes,
  n_comptes: t.scrutins.filter((s) => s.compte).length,
  sans_vote: t.sans_vote,
  etat: t.etat,
  etape: t.scrutins.find((s) => s.role === 'decisif')?.etape ?? null
});

export interface ScoreGroupe {
  groupe: Lignee;
  score: Score;
}

/** Scores des groupes d'une législature sur un droit (ou `global`), du plus haut au plus bas. */
export function scoresGroupes(d: Donnees, legislature: number, droit: string): ScoreGroupe[] {
  return d.lignees
    .filter((l) => l.legislature === legislature)
    .flatMap((l) => {
      const s = d.scoresGroupes.get(l.id)?.get(droit);
      return s ? [{ groupe: l, score: s }] : [];
    })
    .sort((a, b) => (b.score.score ?? -1) - (a.score.score ?? -1));
}

/** Mandat en cours (ou le dernier) et groupe actuel (ou le dernier). */
export function situation(dep: Depute) {
  const mandat = dep.mandats[0] ?? null;
  const groupe = dep.groupes[0]?.groupe ?? null;
  return {
    mandat,
    groupe,
    actuel: mandat !== null && mandat.fin === null && mandat.legislature === 17
  };
}

export function entree(d: Donnees, dep: Depute): EntreeIndex {
  const { mandat, groupe, actuel } = situation(dep);
  const lignee = groupe ? d.ligneeDe.get(groupe.id) : undefined;
  return {
    slug: dep.slug,
    nom: `${dep.prenom} ${dep.nom}`,
    feminin: dep.civ === 'Mme',
    tri: dep.nom_tri,
    circo: mandat?.circo ?? '',
    departement: mandat?.departement ?? '',
    sigle: lignee?.sigle ?? groupe?.sigle ?? '',
    couleur: lignee?.couleur ?? groupe?.couleur ?? '',
    actuel
  };
}

// --- Accueil ----------------------------------------------------------------------------------

export function vueAccueil() {
  const d = donnees();
  return {
    groupes: { 17: scoresGroupes(d, 17, 'global'), 16: scoresGroupes(d, 16, 'global') },
    droits: d.droits.map((dr) => ({
      ...dr,
      n_textes: d.textes.filter((t) => t.droits.some((x) => x.code === dr.code)).length
    })),
    derniers: d.textes.slice(0, 6).map(court),
    enCours: {
      total: d.enCours.length,
      inscrits: d.enCours.filter((t) => t.echeance === 'inscrit').length
    }
  };
}

export function vueEnCours() {
  const d = donnees();
  return { textes: d.enCours, dateEtat: d.dateEtat };
}

// --- Droits et textes -------------------------------------------------------------------------

export function vueDroit(code: string) {
  const d = donnees();
  const droit = d.droits.find((x) => x.code === code);
  if (!droit) error(404, 'Droit inconnu');
  const textes = d.textes.flatMap((t) => {
    const dt = t.droits.find((x) => x.code === code);
    return dt ? [{ texte: court(t), droit: dt, sources: dt.sources.map((s) => t.sources[s]) }] : [];
  });
  return {
    droit,
    textes,
    groupes: { 17: scoresGroupes(d, 17, code), 16: scoresGroupes(d, 16, code) }
  };
}

export function vueTextes() {
  const d = donnees();
  return { textes: d.textes.map(court), ecartes: d.ecartes, droits: d.droits };
}

export function vueTexte(id: string) {
  const d = donnees();
  const texte = d.textes.find((t) => t.id === id);
  if (!texte) error(404, 'Texte inconnu');
  const groupes = d.lignees
    .filter((l) => l.legislature === texte.legislature || d.scoresGroupesTextes.get(l.id)?.has(id))
    .flatMap((l) => {
      const s = d.scoresGroupesTextes.get(l.id)?.get(id);
      return s ? [{ groupe: l, score: { ...s, n_textes: 1 } }] : [];
    })
    .sort((a, b) => (b.score.score ?? -1) - (a.score.score ?? -1));
  return { texte, groupes, dateEtat: d.dateEtat };
}

// --- Députés ----------------------------------------------------------------------------------

export interface VoteDepute {
  scrutin: Pick<
    ScrutinRetenu,
    'id' | 'role' | 'objet' | 'date' | 'etape' | 'url' | 'compte' | 'favorable'
  >;
  /** Position du député ; `absent` s'il était député sans figurer au scrutin. */
  position: Position | 'absent';
  /** Son groupe ce jour-là, et la position de ce groupe. */
  groupe: GroupeCourt | null;
  ventilation: Pick<Ventilation, 'position' | 'cohesion'> | null;
}

function enMandat(dep: Depute, date: string) {
  return dep.mandats.some((m) => m.debut <= date && (m.fin === null || date <= m.fin));
}

function groupeDuJour(dep: Depute, date: string): GroupeCourt | null {
  return (
    dep.groupes.find((a) => a.debut <= date && (a.fin === null || date <= a.fin))?.groupe ?? null
  );
}

/** Textes retenus attendus à l'AN et, à la lecture précédente, le vote du député et de son groupe. */
function prochains(d: Donnees, dep: Depute) {
  return d.enCours
    .filter((t) => t.echeance === 'AN' || (t.echeance === 'inscrit' && estInscritAN(t)))
    .map((t) => {
      const v = t.dernier_vote;
      const groupe = v ? groupeDuJour(dep, v.date) : null;
      const ventilation = groupe ? v?.ventilations.find((x) => x.groupe.id === groupe.id) : null;
      return {
        id: t.id,
        titre: t.titre,
        href: t.href,
        seances: t.seances.map((s) => s.date),
        date_inscrite: t.etat.seance_inscrite,
        vote: v
          ? {
              date: v.date,
              etape: v.etape,
              url: v.url,
              position: enMandat(dep, v.date)
                ? (d.votes.get(v.id)?.get(dep.id) ?? ('absent' as const))
                : null,
              groupe: groupe && ventilation ? { ...groupe, position: ventilation.position } : null
            }
          : null
      };
    });
}

/** Inscrit à l'AN : l'agenda de l'AN le porte, ou la chambre attendue est l'AN. */
const estInscritAN = (t: TexteEnCours) => t.seances.length > 0 || t.chambre === 'AN';

export function vueDepute(slug: string) {
  const d = donnees();
  const dep = d.deputes.find((x) => x.slug === slug);
  if (!dep) error(404, 'Député·e inconnu·e');
  const textes = d.textes.flatMap((t) => {
    // Seuls les scrutins comptés : les autres (motions, autres lectures) sont sur la fiche texte.
    const enCours = t.scrutins.filter((s) => enMandat(dep, s.date));
    const votes: VoteDepute[] = enCours
      .filter((s) => s.compte)
      .map((s) => {
        const groupe = groupeDuJour(dep, s.date);
        const v = groupe ? s.ventilations.find((x) => x.groupe.id === groupe.id) : undefined;
        const { id, role, objet, date, etape, url, compte, favorable } = s;
        return {
          scrutin: { id, role, objet, date, etape, url, compte, favorable },
          position: d.votes.get(s.id)?.get(dep.id) ?? 'absent',
          groupe,
          ventilation: v ? { position: v.position, cohesion: v.cohesion } : null
        };
      });
    if (!votes.length) return [];
    return [
      {
        texte: court(t),
        score: d.scoresDeputesTextes.get(dep.id)?.get(t.id) ?? null,
        votes,
        autres: enCours.length - votes.length
      }
    ];
  });
  const unanimes = d.unanimes
    .filter((u) => enMandat(dep, u.scrutin.date))
    .map((u) => ({
      titre: u.titre,
      etat: u.etat,
      date: u.scrutin.date,
      url: u.scrutin.url,
      position: (d.votes.get(u.scrutin.id)?.get(dep.id) ?? 'absent') as Position | 'absent'
    }));
  const scores = d.scoresDeputes.get(dep.id) ?? new Map<string, Score>();
  const { mandat, groupe, actuel } = situation(dep);
  const lignee = groupe ? (d.ligneeDe.get(groupe.id) ?? null) : null;
  return {
    prochains: actuel ? prochains(d, dep) : [],
    depute: dep,
    mandat,
    groupe,
    lignee,
    actuel,
    global: scores.get('global') ?? null,
    droits: d.droits.flatMap((dr) => {
      const s = scores.get(dr.code);
      return s ? [{ droit: dr, score: s }] : [];
    }),
    participation: d.participation.get(dep.id) ?? null,
    textes,
    unanimes,
    // Pour situer le député : son groupe actuel sur la même règle.
    scoreGroupe: lignee ? (d.scoresGroupes.get(lignee.id)?.get('global') ?? null) : null
  };
}

// --- Groupes ----------------------------------------------------------------------------------

export function vueGroupes() {
  const d = donnees();
  const parLeg = (leg: number) =>
    d.lignees
      .filter((l) => l.legislature === leg && d.scoresGroupes.has(l.id))
      .map((l) => ({
        groupe: l,
        global: d.scoresGroupes.get(l.id)!.get('global') ?? null,
        droits: Object.fromEntries(
          d.droits.map((dr) => [dr.code, d.scoresGroupes.get(l.id)!.get(dr.code) ?? null])
        )
      }))
      .sort((a, b) => (b.global?.score ?? -1) - (a.global?.score ?? -1));
  return { droits: d.droits, legislatures: { 17: parLeg(17), 16: parLeg(16) } };
}

export function vueGroupe(slug: string) {
  const d = donnees();
  const groupe = d.lignees.find((l) => l.slug === slug);
  if (!groupe) error(404, 'Groupe inconnu');
  const scores = d.scoresGroupes.get(groupe.id) ?? new Map<string, Score>();
  // Membres : députés passés par un organe de la lignée, les membres actuels d'abord.
  const membres = d.deputes
    .flatMap((dep) => {
      const a = dep.groupes.filter((x) => groupe.organes.includes(x.groupe.id));
      if (!a.length) return [];
      return [
        {
          ...entree(d, dep),
          dans_le_groupe: a.some((x) => x.fin === null),
          qualite: a[0].qualite,
          score: d.scoresDeputes.get(dep.id)?.get('global') ?? null
        }
      ];
    })
    .sort(
      (a, b) =>
        Number(b.dans_le_groupe) - Number(a.dans_le_groupe) || a.tri.localeCompare(b.tri, 'fr')
    );
  return {
    groupe,
    global: scores.get('global') ?? null,
    droits: d.droits.flatMap((dr) => {
      const s = scores.get(dr.code);
      return s ? [{ droit: dr, score: s }] : [];
    }),
    textes: d.textes.flatMap((t) => {
      const s = d.scoresGroupesTextes.get(groupe.id)?.get(t.id);
      return s ? [{ texte: court(t), score: s }] : [];
    }),
    membres,
    unanimes: d.unanimes.flatMap((u) => {
      const v = u.ventilations.find((x) => groupe.organes.includes(x.groupe.id));
      return v
        ? [
            {
              titre: u.titre,
              etat: u.etat,
              date: u.scrutin.date,
              url: u.scrutin.url,
              position: v.position
            }
          ]
        : [];
    })
  };
}

// --- Circonscriptions et recherche ------------------------------------------------------------

export function circos(d: Donnees) {
  const out = new Map<string, { departement: string; num: number; deputes: Depute[] }>();
  for (const dep of d.deputes)
    for (const m of dep.mandats) {
      const c = out.get(m.circo) ?? { departement: m.departement, num: m.num_circo, deputes: [] };
      if (!c.deputes.includes(dep)) c.deputes.push(dep);
      out.set(m.circo, c);
    }
  return out;
}

export function vueCirco(id: string) {
  const d = donnees();
  const c = circos(d).get(id);
  if (!c) error(404, 'Circonscription inconnue');
  const mandats = c.deputes
    .flatMap((dep) =>
      dep.mandats
        .filter((m) => m.circo === id)
        .map((m) => ({
          ...m,
          depute: entree(d, dep),
          score: d.scoresDeputes.get(dep.id)?.get('global') ?? null
        }))
    )
    .sort((a, b) => b.debut.localeCompare(a.debut));
  const actuel = mandats.find((m) => m.legislature === 17 && m.fin === null) ?? null;
  return { id, departement: c.departement, num: c.num, mandats, actuel };
}

export function indexDeputes(): EntreeIndex[] {
  const d = donnees();
  return d.deputes.map((dep) => entree(d, dep)).sort((a, b) => a.tri.localeCompare(b.tri, 'fr'));
}
