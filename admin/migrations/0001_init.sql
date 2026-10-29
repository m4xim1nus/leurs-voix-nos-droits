-- Schéma D1 de l'admin (docs/CONCEPTION.md, Admin).
--
-- Catalogue : écrit par `lvnd sync-admin` depuis data/export/, en lecture seule pour l'admin.
-- Éditorial : écrit par l'admin (qualifications, révisions, publications).

-- Catalogue -----------------------------------------------------------------------------------

CREATE TABLE textes (
  id TEXT PRIMARY KEY,               -- dossier AN (DLR5L17N…)
  legislature INTEGER NOT NULL,
  titre TEXT NOT NULL,
  procedure TEXT,
  initiative TEXT,
  nature TEXT,                       -- ordinaire, organique, budget, convention, resolution, constitutionnelle
  url_an TEXT,
  loi TEXT,
  date_loi TEXT,
  nor TEXT,
  url_loi TEXT,
  cc_decision TEXT,
  cc_sens TEXT,
  cc_url TEXT,
  n_scrutins INTEGER,
  n_amendements INTEGER,
  n_ensemble INTEGER,
  decisif_propose TEXT,
  premier_scrutin TEXT,
  dernier_scrutin TEXT,
  droits_candidats TEXT,             -- codes séparés par « ; »
  etiquettes_candidates TEXT,
  motifs TEXT
);

CREATE TABLE scrutins (
  id TEXT PRIMARY KEY,
  texte_id TEXT NOT NULL,            -- dossier de rattachement
  legislature INTEGER NOT NULL,
  numero INTEGER NOT NULL,
  date TEXT NOT NULL,
  type_vote TEXT,
  titre TEXT,
  objet TEXT,                        -- ensemble, amendement, article, motion_rejet…
  etape TEXT,                        -- AN1, AN2, CMP, ANLDEF…
  sort TEXT,
  pour INTEGER,
  contre INTEGER,
  abstention INTEGER,
  non_votants INTEGER,
  amendement_id TEXT,
  amendement_numero TEXT,
  amendement_division TEXT,          -- article visé (« Article 7 »)
  amendement_auteur TEXT,            -- groupe de l'auteur (identifiant d'organe) ou type d'auteur
  amendement_sort TEXT,
  positions TEXT NOT NULL            -- JSON : [[groupe, pour, contre, abstention, non_votants, position, cohésion]]
);
CREATE INDEX scrutins_texte ON scrutins(texte_id);

CREATE TABLE groupes (
  id TEXT PRIMARY KEY,
  lignee TEXT NOT NULL,              -- organe le plus récent de la lignée (règle 19)
  legislature INTEGER,
  sigle TEXT,
  nom TEXT,
  couleur TEXT,
  date_debut TEXT,
  date_fin TEXT
);

-- Clé → valeur JSON : grille des droits, date du sync, sources de l'instantané.
CREATE TABLE catalogue_meta (
  cle TEXT PRIMARY KEY,
  valeur TEXT NOT NULL
);

-- Éditorial -----------------------------------------------------------------------------------

-- Une qualification par texte. `doc` suit exactement une entrée d'editorial.json (format 1).
CREATE TABLE qualifications (
  dossier_an TEXT PRIMARY KEY,
  statut TEXT NOT NULL DEFAULT 'brouillon'
    CHECK (statut IN ('brouillon', 'a-relire', 'valide', 'ecarte')),
  doc TEXT NOT NULL,
  motif_ecart TEXT,                  -- statut « ecarte » : pourquoi le texte n'est pas qualifié
  modifie_par TEXT NOT NULL,
  modifie_le TEXT NOT NULL,
  publie_empreinte TEXT              -- empreinte (doc, statut, motif) à la dernière publication
);

-- Chaque enregistrement : document complet, auteur, date.
CREATE TABLE revisions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  dossier_an TEXT NOT NULL,
  statut TEXT NOT NULL,
  doc TEXT NOT NULL,
  motif_ecart TEXT,
  auteur TEXT NOT NULL,
  date TEXT NOT NULL,
  commentaire TEXT
);
CREATE INDEX revisions_dossier ON revisions(dossier_an, id);

CREATE TABLE publications (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  auteur TEXT NOT NULL,
  date TEXT NOT NULL,
  commit_sha TEXT,
  commit_url TEXT,
  n_textes INTEGER NOT NULL,
  n_ecartes INTEGER NOT NULL,
  resume TEXT NOT NULL               -- textes ajoutés, modifiés, retirés
);
