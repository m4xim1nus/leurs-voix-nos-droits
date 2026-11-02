import { fail, redirect } from '@sveltejs/kit';
import type { Actions, PageServerLoad } from './$types';
import { alertes, notesInternes, qualifications } from '$lib/server/db';
import { consommation, etat, reglages } from '$lib/server/llm';
import {
  charger,
  ecarter,
  jugement,
  propositionsOuvertes,
  RefusProposition,
  type Proposition
} from '$lib/server/propositions';
import { ConflitEdition } from '$lib/server/db';
import { differences, normaliser } from '$lib/qualification';
import type { Alerte } from '$lib/alertes';
import type { Qualification } from '$lib/types';

export interface PropositionAffichee extends Proposition {
  jugement: string;
  ecarts: string[] | null;
}

export interface Groupe {
  dossier: string;
  titre: string;
  alertes: Alerte[];
  note: string | null;
  propositions: PropositionAffichee[];
  /** Date qui ordonne la file : échéance à venir (séance), sinon l'alerte la plus récente. */
  echeance: string | null;
  recent: string;
}

function ecarts(p: Proposition, actuelle: Qualification | undefined): string[] | null {
  if (!actuelle || !p.doc || !p.doc.titre || p.doc.statut === 'sans-source') return null;
  try {
    return differences(
      actuelle,
      normaliser({ ...p.doc, droits: p.doc.droits ?? [], scrutins: p.doc.scrutins ?? [] })
    );
  } catch {
    return null;
  }
}

export const load: PageServerLoad = async ({ platform }) => {
  const env = platform!.env;
  const [a, notes, props, quals, r, conso] = await Promise.all([
    alertes(env.DB),
    notesInternes(env.DB),
    propositionsOuvertes(env.DB),
    qualifications(env.DB),
    reglages(env.DB),
    consommation(env.DB)
  ]);
  const actuelles = new Map(quals.map((q) => [q.dossier_an, q.doc]));
  const parNote = new Map(notes.map((n) => [n.dossier_an, n.texte]));
  const aujourdhui = new Date().toISOString().slice(0, 10);

  const groupes = new Map<string, Groupe>();
  for (const x of a) {
    const g = groupes.get(x.dossier_id) ?? {
      dossier: x.dossier_id,
      titre: x.titre ?? x.dossier_id,
      alertes: [],
      note: parNote.get(x.dossier_id) ?? null,
      propositions: [],
      echeance: null,
      recent: x.date
    };
    g.alertes.push(x);
    if (x.type === 'inscrit' && x.date >= aujourdhui && (!g.echeance || x.date < g.echeance))
      g.echeance = x.date;
    if (x.date > g.recent) g.recent = x.date;
    groupes.set(x.dossier_id, g);
  }
  // Une proposition n'apparaît que si son texte a encore une alerte à traiter : traité à la main
  // entre-temps, il sort de la file avec elle.
  for (const p of props) {
    const g = groupes.get(p.dossier_an);
    if (g)
      g.propositions.push({
        ...p,
        jugement: jugement(p.doc),
        ecarts: ecarts(p, actuelles.get(p.dossier_an))
      });
  }
  const file = [...groupes.values()].sort((x, y) => {
    if (x.echeance && y.echeance) return x.echeance.localeCompare(y.echeance);
    if (x.echeance) return -1;
    if (y.echeance) return 1;
    return y.recent.localeCompare(x.recent);
  });
  return {
    file,
    nAlertes: a.length,
    notes,
    llm: { etat: etat(r, conso.mois_usd, Boolean(env.LLM_CHIFFREMENT)), actif: r.actif }
  };
};

export const actions: Actions = {
  charger: async ({ request, platform, locals }) => {
    const id = Number((await request.formData()).get('id'));
    try {
      const dossier = await charger(platform!.env.DB, id, locals.email);
      redirect(303, `/textes/${dossier}`);
    } catch (e) {
      if (e instanceof RefusProposition || e instanceof ConflitEdition)
        return fail(400, { erreur: e.message, id });
      throw e;
    }
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
  }
};
