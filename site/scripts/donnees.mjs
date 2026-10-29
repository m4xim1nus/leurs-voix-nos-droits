// Copie l'instantané versionné (data/export/, data/editorial.json, data/annuaire/) dans
// static/donnees/, servi tel quel par la page « Données ». Lancé avant `dev` et `build`
// (package.json), après `lvnd scores` dans build.sh.
import { cpSync, mkdirSync, readdirSync, rmSync } from 'node:fs';
import { resolve } from 'node:path';

const racine = resolve(import.meta.dirname, '../..');
const cible = resolve(import.meta.dirname, '../static/donnees');
rmSync(cible, { recursive: true, force: true });
mkdirSync(cible, { recursive: true });
cpSync(resolve(racine, 'data/export'), cible, { recursive: true });
cpSync(resolve(racine, 'data/editorial.json'), resolve(cible, 'editorial.json'));
cpSync(resolve(racine, 'data/annuaire'), resolve(cible, 'annuaire'), { recursive: true });
console.log(
  `donnees : ${readdirSync(cible, { recursive: true }).length} fichiers copiés dans static/donnees/`
);
