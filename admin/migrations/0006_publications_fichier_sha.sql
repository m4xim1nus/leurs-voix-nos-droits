-- Empreinte git (blob) du fichier écrit par chaque publication. Si le fichier du dépôt a encore celle de la
-- dernière publication, personne ne l'a modifié hors de l'admin : la page « Publier » saute alors la
-- comparaison dossier par dossier, trop coûteuse en calcul pour un Worker (erreur 1102, 02/11/2026).
ALTER TABLE publications ADD COLUMN fichier_sha TEXT;
