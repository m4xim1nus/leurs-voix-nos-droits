// Carte partageable d'un député (lib/server/cartes.ts).
import { circonscription, depute } from '$lib/format';
import { png, svgCarte } from '$lib/server/cartes';
import { donnees } from '$lib/server/donnees';
import { vueDepute } from '$lib/server/vues';

export const prerender = true;
export const entries = () => donnees().deputes.map((d) => ({ slug: d.slug }));

export const GET = ({ params }) => {
  const v = vueDepute(params.slug);
  const d = v.depute;
  const ou = v.mandat ? `${v.mandat.departement}, ${circonscription(v.mandat.num_circo)}` : '';
  const qui = v.actuel
    ? depute(d.civ, true)
    : d.civ === 'Mme'
      ? 'Ancienne députée'
      : 'Ancien député';
  const reperes = [];
  if (v.global?.score != null)
    reperes.push({
      libelle: d.nom,
      couleur: v.groupe?.couleur ?? '#15171c',
      score: v.global.score
    });
  if (v.lignee && v.scoreGroupe?.score != null)
    reperes.push({
      libelle: `groupe ${v.lignee.sigle}`,
      couleur: v.lignee.couleur,
      score: v.scoreGroupe.score
    });
  const svg = svgCarte({
    titre: `${d.prenom} ${d.nom}`,
    sousTitre: `${qui}${v.groupe ? ` ${v.groupe.sigle}` : ''}${ou ? `, ${ou}` : ''}`,
    score: v.global?.score ?? null,
    nTextes: v.global?.n_textes ?? 0,
    reperes,
    chemin: `/deputes/${d.slug}`
  });
  return new Response(Buffer.from(png(svg)), { headers: { 'content-type': 'image/png' } });
};
