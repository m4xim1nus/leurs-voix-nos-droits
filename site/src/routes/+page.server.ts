import { vueAccueil } from '$lib/server/vues';
import { vueSenat } from '$lib/server/vues-senat';

// L'accueil montre les deux chambres, chacune à part : les groupes de l'Assemblée (législature en
// cours) et ceux du Sénat (période en cours), jamais sur une même règle (règle 28).
export const load = () => {
  const p = vueSenat().periodes[0] ?? null;
  return {
    ...vueAccueil(),
    senat: p && {
      libelle: p.court,
      n_textes: p.n_textes,
      groupes: p.groupes.map((g) => ({
        id: g.groupe.id,
        sigle: g.groupe.sigle,
        couleur: g.groupe.couleur,
        score: g.global?.score ?? null,
        n_textes: g.global?.n_textes ?? 0
      }))
    }
  };
};
