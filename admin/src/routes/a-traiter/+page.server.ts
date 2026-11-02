import { fail, redirect } from '@sveltejs/kit';
import type { Actions, PageServerLoad } from './$types';
import { alertes, ConflitEdition, notesInternes, qualifications } from '$lib/server/db';
import { consommation, etat, reglages } from '$lib/server/llm';
import {
  casNonPrevu,
  charger,
  demander,
  demandes,
  ecarter,
  jugement,
  propositionsOuvertes,
  RefusProposition,
  trancher,
  type Demande,
  type Proposition
} from '$lib/server/propositions';
import { differences, normaliser } from '$lib/qualification';
import type { Alerte } from '$lib/alertes';
import type { LigneQualification, Qualification } from '$lib/types';

/**
 * Sections de la file, par une règle fixe (décision de Max du 02/11/2026) :
 * - `pret` : un vote a eu lieu, la proposition passe les contrôles sans question de méthode ;
 * - `methode` : la proposition signale un « CAS NON PRÉVU » ;
 * - `main` : un vote a eu lieu, sans proposition utilisable (LLM coupé, échec, Sénat non traité d'office) ;
 * - `a-venir` : textes seulement inscrits en séance, rien à qualifier avant le vote.
 */
export type Section = 'pret' | 'methode' | 'main' | 'a-venir';

export interface PropositionAffichee extends Proposition {
  jugement: string;
  ecarts: string[] | null;
  /** Requalification qui ne change ni statut, ni droit principal, ni sens, ni décisif. */
  mineure: boolean;
  methode: boolean;
}

export interface Groupe {
  dossier: string;
  titre: string;
  alertes: Alerte[];
  note: string | null;
  propositions: PropositionAffichee[];
  demande: Demande | null;
  section: Section;
  /** Date qui ordonne la file : échéance à venir (séance), sinon l'alerte la plus récente. */
  echeance: string | null;
  recent: string;
}

function brouillon(p: Proposition): Qualification | null {
  if (!p.doc || !p.doc.titre || p.doc.statut === 'sans-source') return null;
  try {
    return normaliser({ ...p.doc, droits: p.doc.droits ?? [], scrutins: p.doc.scrutins ?? [] });
  } catch {
    return null;
  }
}

const essentiel = (q: Qualification, statut: string) => {
  const p = q.droits.find((d) => d.role === 'principal');
  return JSON.stringify([
    statut === 'ecarte' ? 'ecarte' : 'qualifie',
    p?.code,
    p?.sens,
    q.scrutins.find((s) => s.role === 'decisif')?.id ?? null
  ]);
};

function afficher(p: Proposition, actuelle: LigneQualification | undefined): PropositionAffichee {
  const b = brouillon(p);
  const ecarts = actuelle && b ? differences(actuelle.doc, b) : null;
  const mineure = Boolean(
    actuelle &&
    b &&
    ecarts?.length &&
    p.mode !== 'complet' &&
    essentiel(actuelle.doc, actuelle.statut) ===
      essentiel(b, p.doc?.statut === 'ecarte' ? 'ecarte' : 'qualifie')
  );
  return { ...p, jugement: jugement(p.doc), ecarts, mineure, methode: casNonPrevu(p) };
}

function section(g: Omit<Groupe, 'section'>): Section {
  if (g.alertes.length && g.alertes.every((a) => a.type === 'inscrit')) return 'a-venir';
  const utiles = g.propositions.filter((p) => p.statut === 'proposee');
  if (!utiles.length) return 'main';
  return utiles.some((p) => p.methode) ? 'methode' : 'pret';
}

export const load: PageServerLoad = async ({ platform }) => {
  const env = platform!.env;
  const [a, notes, props, quals, dem, r, conso] = await Promise.all([
    alertes(env.DB),
    notesInternes(env.DB),
    propositionsOuvertes(env.DB),
    qualifications(env.DB),
    demandes(env.DB),
    reglages(env.DB),
    consommation(env.DB)
  ]);
  const actuelles = new Map(quals.map((q) => [q.dossier_an, q]));
  const parNote = new Map(notes.map((n) => [n.dossier_an, n.texte]));
  const parDemande = new Map(dem.map((d) => [d.dossier_an, d]));
  const aujourdhui = new Date().toISOString().slice(0, 10);

  const brouillons = new Map<string, Omit<Groupe, 'section'>>();
  for (const x of a) {
    const g = brouillons.get(x.dossier_id) ?? {
      dossier: x.dossier_id,
      titre: x.titre ?? x.dossier_id,
      alertes: [],
      note: parNote.get(x.dossier_id) ?? null,
      propositions: [],
      demande: null,
      echeance: null,
      recent: x.date
    };
    g.alertes.push(x);
    if (x.type === 'inscrit' && x.date >= aujourdhui && (!g.echeance || x.date < g.echeance))
      g.echeance = x.date;
    if (x.date > g.recent) g.recent = x.date;
    brouillons.set(x.dossier_id, g);
  }
  // Une proposition n'apparaît que si son texte a encore une alerte à traiter : traité à la main
  // entre-temps, il sort de la file avec elle.
  for (const p of props) {
    let g = brouillons.get(p.dossier_an);
    // Veille des sources : la proposition vient d'une publication, pas d'une alerte.
    if (!g && p.alerte_id.startsWith('veille:')) {
      g = {
        dossier: p.dossier_an,
        titre: actuelles.get(p.dossier_an)?.doc.titre || p.doc?.titre || p.dossier_an,
        alertes: [],
        note: parNote.get(p.dossier_an) ?? null,
        propositions: [],
        demande: null,
        echeance: null,
        recent: p.date.slice(0, 10)
      };
      brouillons.set(p.dossier_an, g);
    }
    if (g) g.propositions.push(afficher(p, actuelles.get(p.dossier_an)));
  }
  for (const g of brouillons.values()) {
    const d = parDemande.get(g.dossier);
    if (d && !g.propositions.length) g.demande = d;
  }
  const groupes: Groupe[] = [...brouillons.values()].map((g) => ({ ...g, section: section(g) }));
  const ordre = (x: Groupe, y: Groupe) => {
    if (x.section === 'pret' && y.section === 'pret') {
      const mx = x.propositions.some((p) => p.mineure);
      const my = y.propositions.some((p) => p.mineure);
      if (mx !== my) return mx ? -1 : 1; // gains rapides d'abord
    }
    if (x.echeance && y.echeance) return x.echeance.localeCompare(y.echeance);
    if (x.echeance) return -1;
    if (y.echeance) return 1;
    return y.recent.localeCompare(x.recent);
  };
  const sections = (['pret', 'methode', 'main', 'a-venir'] as const).map((s) => ({
    cle: s,
    groupes: groupes.filter((g) => g.section === s).sort(ordre)
  }));
  return {
    sections,
    nAlertes: a.length,
    nMineures: groupes.filter((g) => g.section === 'pret' && g.propositions.some((p) => p.mineure))
      .length,
    notes,
    llm: { etat: etat(r, conso.mois_usd, Boolean(env.LLM_CHIFFREMENT)), actif: r.actif }
  };
};

export const actions: Actions = {
  charger: async ({ request, platform, locals }) => {
    const id = Number((await request.formData()).get('id'));
    let dossier: string;
    try {
      dossier = await charger(platform!.env.DB, id, locals.email);
    } catch (e) {
      if (e instanceof RefusProposition || e instanceof ConflitEdition)
        return fail(400, { erreur: e.message, id });
      throw e;
    }
    redirect(303, `/textes/${dossier}`);
  },

  ecarter: async ({ request, platform, locals }) => {
    const f = await request.formData();
    const id = Number(f.get('id'));
    try {
      await ecarter(platform!.env.DB, id, String(f.get('motif') ?? ''), locals.email);
      return { ok: 'Proposition écartée.' };
    } catch (e) {
      if (e instanceof RefusProposition) return fail(400, { erreur: e.message, id });
      throw e;
    }
  },

  trancher: async ({ request, platform, locals }) => {
    const id = Number((await request.formData()).get('id'));
    try {
      await trancher(platform!.env.DB, id, locals.email);
      return { ok: 'Question de méthode marquée comme tranchée.' };
    } catch (e) {
      if (e instanceof RefusProposition) return fail(400, { erreur: e.message, id });
      throw e;
    }
  },

  demander: async ({ request, platform, locals }) => {
    const f = await request.formData();
    const alerte = {
      id: String(f.get('alerte') ?? ''),
      dossier_id: String(f.get('dossier') ?? '')
    };
    if (!alerte.id || !alerte.dossier_id) return fail(400, { erreur: 'alerte manquante' });
    try {
      await demander(platform!.env.DB, alerte, locals.email);
      return { ok: 'Proposition demandée : elle arrivera après la prochaine passe de données.' };
    } catch (e) {
      if (e instanceof RefusProposition) return fail(400, { erreur: e.message });
      throw e;
    }
  }
};
