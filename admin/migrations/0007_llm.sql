-- Usage du LLM (cycle Pré-qualification, ROADMAP item 1). D1 seule : ni publié, ni exporté.
--
-- Réglages : écrits par l'admin (page « LLM »), lus par l'Action des propositions avant tout appel.
--   actif       JSON booléen : interrupteur général ; faux, absent ou illisible = aucun appel
--   plafond_usd JSON nombre : plafond de dépense du mois civil (UTC), en dollars
--   modele      JSON chaîne : identifiant du modèle
--   cle_api     JSON { chiffre, fin } : clé chiffrée (AES-GCM, secret LLM_CHIFFREMENT), 4 derniers caractères
CREATE TABLE llm_reglages (
  cle TEXT PRIMARY KEY,
  valeur TEXT NOT NULL,
  modifie_par TEXT NOT NULL,
  modifie_le TEXT NOT NULL
);

-- Journal des appels : un par requête à l'API, écrit par l'Action. Le coût est estimé par le pipeline
-- d'après `usage` et ses tarifs ; la facture fait foi.
CREATE TABLE llm_appels (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  date TEXT NOT NULL,
  tache TEXT NOT NULL,               -- proposition, veille, mesure…
  dossier_an TEXT,
  modele TEXT NOT NULL,
  jetons_entree INTEGER NOT NULL DEFAULT 0,
  jetons_sortie INTEGER NOT NULL DEFAULT 0,
  jetons_cache_lus INTEGER NOT NULL DEFAULT 0,
  jetons_cache_ecrits INTEGER NOT NULL DEFAULT 0,
  recherches_web INTEGER NOT NULL DEFAULT 0,
  cout_usd REAL NOT NULL DEFAULT 0,
  resultat TEXT NOT NULL,            -- ok, erreur, refus…
  detail TEXT
);
CREATE INDEX llm_appels_date ON llm_appels(date);
