-- Votes du Sénat dans le catalogue de l'admin (règles 23 à 28) : écrits par `lvnd sync-admin` depuis
-- data/export/senat/, en lecture seule pour l'admin. Les amendements n'y sont pas : aucun n'est retenu.
CREATE TABLE senat_scrutins (
  id TEXT PRIMARY KEY,               -- SN<session>-<numéro>
  texte_id TEXT NOT NULL,            -- dossier AN de rattachement
  session INTEGER NOT NULL,
  numero INTEGER NOT NULL,
  date TEXT NOT NULL,
  titre TEXT,
  objet TEXT,                        -- ensemble, article_unique, motion_rejet…
  lecture TEXT,
  sort TEXT,
  pour INTEGER,
  contre INTEGER,
  abstention INTEGER,
  non_votants INTEGER,
  note TEXT,
  url TEXT,
  positions TEXT NOT NULL            -- JSON : [[groupe, pour, contre, abstention, non_votants, position, cohésion]]
);
CREATE INDEX senat_scrutins_texte ON senat_scrutins(texte_id);

CREATE TABLE senat_groupes (
  id TEXT PRIMARY KEY,
  sigle TEXT,
  nom TEXT
);
