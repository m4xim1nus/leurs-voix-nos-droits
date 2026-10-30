import { donnees } from '$lib/server/donnees';
import { agendaIcal } from '$lib/server/flux';

export const prerender = true;

export const GET = () => {
  const d = donnees();
  return new Response(agendaIcal(d.enCours, d.dateEtat), {
    headers: { 'Content-Type': 'text/calendar; charset=utf-8' }
  });
};
