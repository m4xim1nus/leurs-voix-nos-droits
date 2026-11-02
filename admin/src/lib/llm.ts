// Usage du LLM : constantes partagées par le serveur et les pages (lib/server/llm.ts).

export const MODELES = [
  { id: 'claude-opus-5-5', libelle: 'Claude Opus 5.5 (par défaut)' },
  { id: 'claude-sonnet-5-5', libelle: 'Claude Sonnet 5.5 (deux fois moins cher)' }
] as const;
export const MODELE_DEFAUT = MODELES[0].id;
export const PLAFOND_DEFAUT = 20;

export type Etat = 'en-service' | 'coupe' | 'sans-cle' | 'sans-secret' | 'plafond';

export const LIBELLES_ETAT: Record<Etat, string> = {
  'en-service': 'en service : les prochaines passes demanderont des propositions',
  coupe: 'coupé : aucun appel, l’admin fonctionne comme avant',
  'sans-cle': 'allumé, mais sans clé : aucun appel',
  'sans-secret': 'allumé, mais le secret LLM_CHIFFREMENT manque : aucun appel',
  plafond: 'plafond du mois atteint : plus aucun appel jusqu’au 1er du mois suivant'
};
