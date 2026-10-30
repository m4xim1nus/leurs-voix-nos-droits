// Courriel prérempli de la section « Prochains votes » d'une fiche député : des faits et une question,
// jamais de consigne de vote.

import { date, inscription, POSITION_GROUPE, voteDeLecture } from './format';
import type { Position, PositionGroupe } from './types';

export interface VoteProchain {
  date: string;
  etape: string | null;
  /** Null : pas encore député·e à cette date. */
  position: Position | 'absent' | null;
  groupe: { sigle: string; position: PositionGroupe } | null;
}

function sonVote(position: VoteProchain['position'], feminin: boolean): string {
  if (position === null) return `Vous n’étiez pas encore ${feminin ? 'députée' : 'député'}`;
  if (position === 'pour' || position === 'contre') return `Vous avez voté ${position}`;
  if (position === 'abstention') return `Vous vous êtes ${feminin ? 'abstenue' : 'abstenu'}`;
  return 'Vous n’avez pas pris part à ce vote';
}

export function courrielProchainVote(t: {
  titre: string;
  url: string;
  feminin: boolean;
  /** Dates de séance à l'Assemblée, vides si le texte n'est pas encore inscrit. */
  seances: string[];
  vote: VoteProchain | null;
}): { sujet: string; corps: string } {
  const ou = t.seances.length
    ? `${inscription('AN', t.seances).replace('Inscrit', 'est inscrit')}`
    : 'est attendu à l’Assemblée';
  const lignes = [
    `Bonjour ${t.feminin ? 'Madame la Députée' : 'Monsieur le Député'},`,
    '',
    `Le texte « ${t.titre} » ${ou}.`
  ];
  if (t.vote) {
    const lecture = voteDeLecture(t.vote.etape);
    const quand = `le ${date(t.vote.date)}${lecture ? ` (${lecture})` : ''}`;
    lignes.push(
      '',
      `Dernier vote public de l’Assemblée sur ce texte, ${quand} : ${sonVote(t.vote.position, t.feminin).replace(/^V/, 'v')}.`
    );
    if (t.vote.groupe)
      lignes.push(
        `Position de votre groupe ce jour-là (${t.vote.groupe.sigle}) : ${POSITION_GROUPE[t.vote.groupe.position]}.`
      );
  }
  lignes.push(
    '',
    `Fiche du texte : ${t.url}`,
    '',
    'Je souhaiterais connaître votre position sur ce texte.',
    '',
    'Cordialement,',
    ''
  );
  return { sujet: `Votre position sur : ${t.titre}`, corps: lignes.join('\n') };
}
