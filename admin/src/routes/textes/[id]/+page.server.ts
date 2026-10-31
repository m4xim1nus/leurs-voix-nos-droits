import { error, fail } from '@sveltejs/kit';
import type { Actions, PageServerLoad } from './$types';
import * as db from '$lib/server/db';
import { versionPubliee } from '$lib/server/publication';
import {
  differences,
  normaliser,
  nouvelle,
  STATUTS,
  valider,
  validerSuivi
} from '$lib/qualification';
import type { Qualification, Source, Statut } from '$lib/types';

const plusJours = (date: string, n: number) =>
  new Date(Date.parse(`${date.slice(0, 10)}T00:00:00Z`) + n * 864e5).toISOString().slice(0, 10);

export const load: PageServerLoad = async ({ params, platform }) => {
  const base = platform!.env.DB;
  const texte = await db.texte(base, params.id);
  if (!texte) error(404, `texte ${params.id} absent du catalogue`);
  const [duDossier, censures, groupes, grille, qualif, revisions, toutes, senat, groupesSenat] =
    await Promise.all([
      db.scrutinsDuTexte(base, params.id),
      // Motions de censure votées pendant l'examen du texte et dans les 4 mois qui suivent ses
      // derniers votes : à retenir (rôle « censure ») s'il a été adopté par 49.3 sans vote final.
      texte.premier_scrutin && texte.dernier_scrutin
        ? db.censures(base, texte.premier_scrutin, plusJours(texte.dernier_scrutin, 120))
        : Promise.resolve([]),
      db.groupes(base),
      db.grille(base),
      db.qualification(base, params.id),
      db.revisions(base, params.id),
      db.qualifications(base),
      db.scrutinsSenatDuTexte(base, params.id),
      db.groupesSenat(base)
    ]);
  // Sources des autres textes, pour les reprendre sans ressaisie (docs/CONCEPTION.md, choix C).
  const bibliotheque: { cle: string; texte: string; source: Source }[] = [];
  for (const q of toutes)
    if (q.dossier_an !== params.id)
      for (const [cle, source] of Object.entries(q.doc.sources ?? {}))
        bibliotheque.push({ cle, texte: q.doc.id, source });
  bibliotheque.sort((a, b) => a.cle.localeCompare(b.cle));
  const ids = new Set(duDossier.map((s) => s.id));
  const scrutins = [...duDossier, ...censures.filter((s) => !ids.has(s.id))];
  let publie: { date: string; changements: string[] } | null = null;
  if (qualif?.publie_empreinte) {
    const v = await versionPubliee(base, params.id, qualif.publie_empreinte);
    if (v) publie = { date: v.date, changements: differences(v.doc, qualif.doc) };
  }
  return {
    texte,
    publie,
    scrutins,
    senat,
    groupesSenat,
    groupes,
    grille,
    qualif: qualif ?? {
      dossier_an: texte.id,
      statut: 'brouillon' as Statut,
      doc: nouvelle(texte),
      motif_ecart: null,
      modifie_par: '',
      modifie_le: '',
      publie_empreinte: null
    },
    existe: qualif !== null,
    revisions,
    bibliotheque,
    autresIds: toutes.filter((q) => q.dossier_an !== params.id && q.doc.id).map((q) => q.doc.id)
  };
};

export const actions: Actions = {
  enregistrer: async ({ request, params, platform, locals }) => {
    const base = platform!.env.DB;
    const f = await request.formData();
    const statut = String(f.get('statut')) as Statut;
    const motif = String(f.get('motif_ecart') ?? '').trim() || null;
    const commentaire = String(f.get('commentaire') ?? '').trim() || null;
    const attendu = String(f.get('attendu') ?? '') || null;
    if (!STATUTS.includes(statut)) return fail(400, { erreurs: [`statut inconnu : ${statut}`] });
    let doc: Qualification;
    try {
      doc = normaliser(JSON.parse(String(f.get('doc'))));
    } catch {
      return fail(400, { erreurs: ['document illisible'] });
    }
    const texte = await db.texte(base, params.id);
    if (!texte || doc.dossier_an !== params.id)
      return fail(400, { erreurs: ['le document ne correspond pas à ce texte'] });
    doc.legislature = texte.legislature;

    const erreurs: string[] = [];
    if (statut === 'ecarte' && !motif) erreurs.push('un texte écarté doit avoir un motif');
    if (statut !== 'ecarte') {
      if (!/^[a-z0-9]+(-[a-z0-9]+)*$/.test(doc.id))
        erreurs.push('identifiant : minuscules, chiffres et tirets seulement');
      const autres = (await db.qualifications(base)).filter((q) => q.dossier_an !== params.id);
      if (autres.some((q) => q.doc.id === doc.id))
        erreurs.push(`identifiant ${doc.id} déjà pris par un autre texte`);
    }
    // Un texte validé passe tous les contrôles ; un brouillon s'enregistre tel quel.
    if (statut === 'valide') {
      const infos = db.infos(
        await db.scrutins(
          base,
          doc.scrutins.map((s) => s.id)
        )
      );
      const infosSenat = db.infosSenat(
        await db.scrutinsSenat(
          base,
          (doc.senat?.scrutins ?? []).map((s) => s.id)
        )
      );
      erreurs.push(...valider(doc, await db.grille(base), infos, infosSenat).erreurs);
    }
    if (statut === 'a-suivre') {
      erreurs.push(...validerSuivi(doc, await db.grille(base)).erreurs);
      // Un texte déjà qualifié garde son sens : il ne revient pas à une fiche sans sens.
      const avant = await db.qualification(base, params.id);
      const publiee = avant?.publie_empreinte
        ? await versionPubliee(base, params.id, avant.publie_empreinte)
        : null;
      if (publiee?.statut === 'valide')
        erreurs.push('texte déjà qualifié et publié : il ne peut pas repasser à suivre');
    }
    if (erreurs.length) return fail(400, { erreurs });
    try {
      const modifie_le = await db.enregistrer(
        base,
        { doc, statut, motif_ecart: statut === 'ecarte' ? motif : null, commentaire },
        locals.email,
        attendu
      );
      return { ok: true, modifie_le };
    } catch (e) {
      if (e instanceof db.ConflitEdition) return fail(409, { erreurs: [e.message] });
      throw e;
    }
  }
};
