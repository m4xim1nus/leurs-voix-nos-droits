import { fail } from '@sveltejs/kit';
import type { Actions, PageServerLoad } from './$types';
import {
  chiffrer,
  consommation,
  ecrireReglage,
  etat,
  formeCle,
  MODELES,
  reglages,
  retirerCle,
  testerCle
} from '$lib/server/llm';

export const load: PageServerLoad = async ({ platform }) => {
  const env = platform!.env;
  const [r, conso] = await Promise.all([reglages(env.DB), consommation(env.DB)]);
  const secret = Boolean(env.LLM_CHIFFREMENT);
  return {
    reglages: r,
    conso,
    secret,
    etat: etat(r, conso.mois_usd, secret),
    modeles: MODELES
  };
};

export const actions: Actions = {
  basculer: async ({ request, platform, locals }) => {
    const actif = (await request.formData()).get('actif') === 'oui';
    await ecrireReglage(platform!.env.DB, 'actif', actif, locals.email);
    return { ok: actif ? 'Usage du LLM allumé.' : 'Usage du LLM coupé.' };
  },

  plafond: async ({ request, platform, locals }) => {
    const brut = String((await request.formData()).get('plafond') ?? '').replace(',', '.');
    const plafond = Number(brut);
    if (!brut.trim() || !Number.isFinite(plafond) || plafond < 0 || plafond > 1000)
      return fail(400, { erreur: 'plafond : un nombre de dollars entre 0 et 1 000' });
    await ecrireReglage(
      platform!.env.DB,
      'plafond_usd',
      Math.round(plafond * 100) / 100,
      locals.email
    );
    return { ok: 'Plafond enregistré.' };
  },

  modele: async ({ request, platform, locals }) => {
    const modele = String((await request.formData()).get('modele') ?? '');
    if (!MODELES.some((m) => m.id === modele)) return fail(400, { erreur: 'modèle inconnu' });
    await ecrireReglage(platform!.env.DB, 'modele', modele, locals.email);
    return { ok: 'Modèle enregistré.' };
  },

  cle: async ({ request, platform, locals }) => {
    const env = platform!.env;
    if (!env.LLM_CHIFFREMENT)
      return fail(500, {
        erreur: 'secret LLM_CHIFFREMENT absent du Worker : la clé ne peut pas être chiffrée'
      });
    const cle = String((await request.formData()).get('cle') ?? '').trim();
    const forme = formeCle(cle);
    if (forme) return fail(400, { erreur: forme });
    const refus = await testerCle(cle);
    if (refus) return fail(400, { erreur: `clé non enregistrée : ${refus}` });
    await ecrireReglage(
      env.DB,
      'cle_api',
      { chiffre: await chiffrer(env.LLM_CHIFFREMENT, cle), fin: cle.slice(-4) },
      locals.email
    );
    return { ok: 'Clé testée et enregistrée.' };
  },

  retirer: async ({ platform }) => {
    await retirerCle(platform!.env.DB);
    return { ok: 'Clé retirée : plus aucun appel tant qu’une autre n’est pas saisie.' };
  }
};
