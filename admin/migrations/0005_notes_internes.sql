-- Note interne par texte : pense-bête éditorial qu'aucune alerte ne porte (fiche prête avant l'inscription,
-- motif à actualiser au prochain passage). D1 seule : ni publiée, ni exportée, ni écrite par `lvnd sync-admin`.
-- Une note vide est supprimée. Clé : le dossier AN, qu'il soit qualifié ou non.
CREATE TABLE notes_internes (
  dossier_an TEXT PRIMARY KEY,
  texte TEXT NOT NULL,
  modifie_par TEXT NOT NULL,
  modifie_le TEXT NOT NULL
);
