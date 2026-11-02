-- Propositions du LLM (cycle Pré-qualification, ROADMAP items 5 et 6). D1 seule : ni publiée, ni exportée.
--
-- Écrites par l'Action des propositions (`lvnd proposer --alertes`), une par alerte et jamais recalculée.
-- Une proposition ne touche jamais une qualification : seul un humain la charge (statut « chargee », la
-- qualification passe alors « à relire ») ou l'écarte (statut « ecartee », motif gardé pour la mesure).
CREATE TABLE propositions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  alerte_id TEXT NOT NULL,           -- type:dossier[:scrutin], comme la table alertes
  dossier_an TEXT NOT NULL,
  mode TEXT NOT NULL,                -- complet, ecart, requalification, suivi, senat
  date TEXT NOT NULL,
  modele TEXT NOT NULL,
  cout_usd REAL NOT NULL DEFAULT 0,
  doc TEXT,                          -- JSON : le brouillon, sans `relecture`
  relecture TEXT,                    -- JSON : points d'attention, extraits, incertitudes, signataires, contrôles
  statut TEXT NOT NULL CHECK (statut IN ('proposee', 'echec', 'chargee', 'ecartee')),
  motif TEXT,                        -- échec : pourquoi ; écartée : motif du relecteur
  traite_par TEXT,
  traite_le TEXT
);
CREATE UNIQUE INDEX propositions_alerte ON propositions(alerte_id);
CREATE INDEX propositions_dossier ON propositions(dossier_an);
