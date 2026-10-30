import { donnees } from '$lib/server/donnees';
import { fluxRss } from '$lib/server/flux';

export const prerender = true;

export const GET = () => {
  const d = donnees();
  return new Response(fluxRss(d.enCours, d.dateEtat), {
    headers: { 'Content-Type': 'application/rss+xml; charset=utf-8' }
  });
};
