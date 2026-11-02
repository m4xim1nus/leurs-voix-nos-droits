-- Demandes de proposition au LLM (cycle Pré-qualification) : faites depuis « À traiter » pour une alerte que l'Action
-- ne traite pas d'elle-même (texte inscrit, vote du Sénat). La passe suivante de l'Action la traite (`lvnd proposer
-- --alertes`), puis la proposition, comme les autres, n'est jamais recalculée. D1 seule.
CREATE TABLE demandes_llm (
  alerte_id TEXT PRIMARY KEY,
  dossier_an TEXT NOT NULL,
  demande_par TEXT NOT NULL,
  demande_le TEXT NOT NULL
);
