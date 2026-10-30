-- Statut « a-suivre » : fiche de suivi d'un texte sans vote qualifié, droits touchés et sources, sans
-- sens ni scrutin. SQLite ne modifie pas une contrainte CHECK : on recrée la table, lignes comprises.
CREATE TABLE qualifications_nouvelle (
  dossier_an TEXT PRIMARY KEY,
  statut TEXT NOT NULL DEFAULT 'brouillon'
    CHECK (statut IN ('brouillon', 'a-relire', 'valide', 'ecarte', 'a-suivre')),
  doc TEXT NOT NULL,
  motif_ecart TEXT,
  modifie_par TEXT NOT NULL,
  modifie_le TEXT NOT NULL,
  publie_empreinte TEXT
);
INSERT INTO qualifications_nouvelle (dossier_an, statut, doc, motif_ecart, modifie_par, modifie_le, publie_empreinte)
  SELECT dossier_an, statut, doc, motif_ecart, modifie_par, modifie_le, publie_empreinte FROM qualifications;
DROP TABLE qualifications;
ALTER TABLE qualifications_nouvelle RENAME TO qualifications;
