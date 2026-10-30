-- Alertes de la file « À traiter » : écrites par `lvnd sync-admin` depuis data/export/, en lecture
-- seule pour l'admin (catalogue). Ce sont des avertissements (pipeline/lvnd/alertes.py).
CREATE TABLE alertes (
  id TEXT PRIMARY KEY,               -- type:dossier[:scrutin]
  type TEXT NOT NULL,                -- vote_posterieur, unanimite_contestee, premier_decisif, inscrit
  dossier_id TEXT NOT NULL,
  scrutin_id TEXT,
  date TEXT NOT NULL,
  titre TEXT,
  detail TEXT NOT NULL
);
CREATE INDEX alertes_dossier ON alertes(dossier_id);
