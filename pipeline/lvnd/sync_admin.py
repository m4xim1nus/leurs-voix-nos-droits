"""Pousse le catalogue dans la base D1 de l'admin (docs/CONCEPTION.md, Admin).

On lit `data/export/` (versionné) plutôt que la base locale : le sync peut ainsi tourner sans
dump. Le script SQL remplace le catalogue (textes, scrutins rattachés, groupes, grille) et ne
touche jamais aux tables éditoriales, sauf `--editorial`, qui y ajoute les qualifications
publiées absentes de D1 (amorçage, ou reconstruction de D1 depuis git) sans écraser un brouillon.

Le script est exécuté par `wrangler d1 execute` depuis `admin/`. Par défaut, le sync est
**incrémental** : il lit le catalogue présent dans D1 (les lectures sont presque gratuites), le
compare à l'export, et n'écrit que les lignes ajoutées, modifiées ou disparues. Une semaine de
nouveaux scrutins écrit quelques centaines de lignes. `--complet` efface et réécrit tout (environ
80 000 lignes écrites, index compris, près de la limite gratuite de D1 : 100 000 par jour).
"""

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import polars as pl
import yaml

from . import editorial, referentiels

BASE = "lvnd-admin"
LOT = 50  # lignes par INSERT (D1 limite une instruction SQL à 100 Ko)

COLONNES_TEXTES = ("id", "legislature", "titre", "procedure", "initiative", "nature", "url_an", "loi", "date_loi",
                   "nor", "url_loi", "cc_decision", "cc_sens", "cc_url", "n_scrutins", "n_amendements", "n_ensemble",
                   "decisif_propose", "premier_scrutin", "dernier_scrutin", "droits_candidats",
                   "etiquettes_candidates", "motifs")
COLONNES_SCRUTINS = ("id", "texte_id", "legislature", "numero", "date", "type_vote", "titre", "objet", "etape", "sort",
                     "pour", "contre", "abstention", "non_votants", "amendement_id", "amendement_numero",
                     "amendement_division", "amendement_auteur", "amendement_sort", "positions")
COLONNES_GROUPES = ("id", "lignee", "legislature", "sigle", "nom", "couleur", "date_debut", "date_fin")


def sql_valeur(v) -> str:
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return str(int(v))
    if isinstance(v, (int, float)):
        return repr(v)
    return "'" + str(v).replace("'", "''") + "'"


TAILLE_MAX = 90_000  # octets par instruction (D1 refuse au-delà de 100 Ko : SQLITE_TOOBIG)


def inserts(table: str, colonnes: tuple[str, ...], lignes: list[dict], verbe: str = "INSERT") -> list[str]:
    """INSERT par lots d'au plus LOT lignes et TAILLE_MAX octets (une ligne seule peut dépasser)."""
    tete = f"{verbe} INTO {table} ({', '.join(colonnes)}) VALUES\n"
    out, lot, taille = [], [], len(tete)
    for r in lignes:
        v = "(" + ", ".join(sql_valeur(r.get(c)) for c in colonnes) + ")"
        n = len(v.encode()) + 2
        if lot and (len(lot) >= LOT or taille + n > TAILLE_MAX):
            out.append(tete + ",\n".join(lot) + ";")
            lot, taille = [], len(tete)
        lot.append(v)
        taille += n
    if lot:
        out.append(tete + ",\n".join(lot) + ";")
    return out


def _lire(export: Path, nom: str) -> pl.DataFrame:
    return pl.read_csv(export / f"{nom}.csv", infer_schema_length=None)


def _vide(v):
    return None if v == "" else v


def catalogue(export: Path) -> dict[str, list[dict]]:
    """Lignes des tables du catalogue, depuis data/export/."""
    textes = [{k: _vide(v) for k, v in r.items()} for r in _lire(export, "textes").iter_rows(named=True)]
    ids = {t["id"] for t in textes}

    pos: dict[str, list] = {}
    for r in _lire(export, "positions_groupes").iter_rows(named=True):
        if r["pour"] + r["contre"] + r["abstention"] + r["non_votants"] == 0:
            continue  # groupe sans aucun votant : rien à afficher
        pos.setdefault(r["scrutin_id"], []).append(
            [r["groupe_id"], r["pour"], r["contre"], r["abstention"], r["non_votants"], r["position"], r["cohesion"]])

    amdts = {}
    if (export / "amendements.csv").stat().st_size:
        amdts = {r["id"]: r for r in _lire(export, "amendements").iter_rows(named=True)}

    scrutins = []
    for r in _lire(export, "scrutins").iter_rows(named=True):
        # Les motions de censure vont toutes dans D1 (rattachement vide si leur dossier n'est pas au
        # catalogue) : la fiche d'un texte adopté par 49.3 propose celles qui suivent ses derniers votes.
        censure = r["objet"] == "motion_censure"
        if r["dossier_id"] not in ids and not censure:
            continue
        a = amdts.get(r["amendement_id"] or "", {})
        scrutins.append({
            **{k: r[k] for k in ("id", "legislature", "numero", "date", "type_vote", "titre", "objet", "sort", "pour",
                                 "contre", "abstention", "non_votants", "amendement_id")},
            "texte_id": r["dossier_id"] if r["dossier_id"] in ids else "",
            "etape": _vide(r["etape"]),
            "amendement_numero": _vide(str(a.get("numero") or "")),
            "amendement_division": _vide(a.get("division") or ""),
            "amendement_auteur": _vide(a.get("groupe_id") or a.get("type_auteur") or ""),
            "amendement_sort": _vide(a.get("sort") or ""),
            "positions": json.dumps(pos.get(r["id"], []), separators=(",", ":")),
        })

    groupes = [{k: _vide(v) for k, v in r.items()} for r in _lire(export, "groupes").iter_rows(named=True)]
    meta = json.loads((export / "meta.json").read_text())
    metas = [
        {"cle": "grille", "valeur": json.dumps(referentiels.droits(), ensure_ascii=False, default=str)},
        {"cle": "export", "valeur": json.dumps({"genere_le": meta["genere_le"], "sources": meta["sources"]},
                                               ensure_ascii=False)},
        {"cle": "sync", "valeur": json.dumps(datetime.now(timezone.utc).isoformat(timespec="seconds"))},
    ]
    return {"textes": textes, "scrutins": scrutins, "groupes": groupes, "catalogue_meta": metas}


def compact(t: dict) -> str:
    """Document d'une qualification tel que D1 le stocke : JSON compact, comme `JSON.stringify`."""
    return json.dumps(t, ensure_ascii=False, separators=(",", ":"))


def empreinte(doc: str, statut: str, motif: str | None) -> str:
    """Empreinte d'une qualification publiée (même calcul dans l'admin, src/lib/qualification.ts)."""
    return hashlib.sha256(f"{doc}\n{statut}\n{motif or ''}".encode()).hexdigest()


def qualifications(doc: dict) -> list[dict]:
    """Qualifications publiées, au format de la table `qualifications` (statut valide ou écarté)."""
    date = datetime.now(timezone.utc).isoformat(timespec="seconds")
    out = []
    for t in doc["textes"]:
        texte = compact(t)
        out.append({"dossier_an": t["dossier_an"], "statut": "valide", "doc": texte, "motif_ecart": None,
                    "modifie_par": "editorial.json", "modifie_le": date,
                    "publie_empreinte": empreinte(texte, "valide", None)})
    for e in doc.get("ecartes", []):
        texte = compact(editorial.ecarte(e))
        out.append({"dossier_an": e["dossier_an"], "statut": "ecarte", "doc": texte, "motif_ecart": e["motif"],
                    "modifie_par": "editorial.json", "modifie_le": date,
                    "publie_empreinte": empreinte(texte, "ecarte", e["motif"])})
    return out


AUTEUR_BROUILLONS = "claude (brouillon)"


def brouillons(dossier: Path) -> list[dict]:
    """Qualifications préparées hors de l'admin (un YAML par texte, format de temoins.yaml plus
    `statut` et `motif_ecart`), à charger au statut « à relire » (proposition d'écart comprise). Le champ
    `relecture` (notes pour le relecteur) n'est pas chargé."""
    date = datetime.now(timezone.utc).isoformat(timespec="seconds")
    out = []
    for f in sorted(dossier.glob("*.yaml")):
        t = yaml.safe_load(f.read_text())
        statut = t.get("statut", "a-relire")
        if statut not in ("a-relire", "ecarte", "brouillon"):
            raise SystemExit(f"{f} : statut {statut} refusé (a-relire, ecarte ou brouillon)")
        motif = t.get("motif_ecart") if statut == "ecarte" else None
        if statut == "ecarte" and not motif:
            raise SystemExit(f"{f} : texte écarté sans motif")
        doc = editorial.normaliser({**t, "droits": t.get("droits") or [], "scrutins": t.get("scrutins") or []})
        # « écarté » est publiable : une proposition d'écart arrive « à relire », motif pré-rempli, et
        # ne part qu'une fois que le relecteur a lui-même choisi « écarté ».
        statut = "a-relire" if statut == "ecarte" else statut
        out.append({"dossier_an": doc["dossier_an"], "statut": statut, "doc": compact(doc), "motif_ecart": motif,
                    "modifie_par": AUTEUR_BROUILLONS, "modifie_le": date, "publie_empreinte": None})
    return out


AUTEUR_VALIDATION = "claude, validé par Max"


def validations(dossier: Path, commentaire: str) -> list[str]:
    """Qualifications de DOSSIER/*.yaml validées par Max (dans le chat) : chacune est écrite au statut
    « valide » (« ecarte » si le YAML le propose, avec son motif), qu'elle existe déjà dans D1 ou non,
    avec une révision qui le dit. Ne sert que sur décision explicite de Max (CLAUDE.md)."""
    date = datetime.now(timezone.utc).isoformat(timespec="seconds")
    out = []
    for f in sorted(dossier.glob("*.yaml")):
        t = yaml.safe_load(f.read_text())
        ecarte = t.get("statut") == "ecarte"
        if ecarte and not t.get("motif_ecart"):
            raise SystemExit(f"{f} : texte écarté sans motif")
        doc = editorial.normaliser({**t, "droits": t.get("droits") or [], "scrutins": t.get("scrutins") or []})
        if not ecarte:
            err, _ = editorial.valider(doc)
            if err:
                raise SystemExit(f"{f} : {' ; '.join(err)}")
        statut, motif = ("ecarte", t["motif_ecart"]) if ecarte else ("valide", None)
        valeurs = [doc["dossier_an"], statut, compact(doc), motif, AUTEUR_VALIDATION, date]
        out.append("INSERT INTO qualifications (dossier_an, statut, doc, motif_ecart, modifie_par, modifie_le) "
                   f"VALUES ({', '.join(sql_valeur(x) for x in valeurs)}) ON CONFLICT (dossier_an) DO UPDATE SET "
                   "statut = excluded.statut, doc = excluded.doc, motif_ecart = excluded.motif_ecart, "
                   "modifie_par = excluded.modifie_par, modifie_le = excluded.modifie_le;")
        out.append("INSERT INTO revisions (dossier_an, statut, doc, motif_ecart, auteur, date, commentaire) VALUES "
                   f"({', '.join(sql_valeur(x) for x in [*valeurs, commentaire])});")
    return out


def remplacements(lignes: list[dict], commentaire: str) -> list[str]:
    """Requalification : les brouillons (`brouillons()`) remplacent la qualification existante et la
    repassent « à relire », avec une révision. `publie_empreinte` est gardée : l'admin montre l'écart avec
    la version publiée, qui reste en ligne jusqu'à la prochaine publication (le texte y figure alors
    comme « retiré » tant qu'il n'est pas revalidé)."""
    out = []
    for l in lignes:
        valeurs = [l["dossier_an"], l["statut"], l["doc"], l["motif_ecart"], l["modifie_par"], l["modifie_le"]]
        out.append("INSERT INTO qualifications (dossier_an, statut, doc, motif_ecart, modifie_par, modifie_le) "
                   f"VALUES ({', '.join(sql_valeur(x) for x in valeurs)}) ON CONFLICT (dossier_an) DO UPDATE SET "
                   "statut = excluded.statut, doc = excluded.doc, motif_ecart = excluded.motif_ecart, "
                   "modifie_par = excluded.modifie_par, modifie_le = excluded.modifie_le;")
        out.append("INSERT INTO revisions (dossier_an, statut, doc, motif_ecart, auteur, date, commentaire) VALUES "
                   f"({', '.join(sql_valeur(x) for x in [*valeurs, commentaire])});")
    return out


def _qualifs(lignes: list[dict], auteur: str, commentaire: str) -> list[str]:
    """Ajoute des qualifications absentes de D1 (jamais d'écrasement) et leur révision d'origine."""
    cols = ("dossier_an", "statut", "doc", "motif_ecart", "modifie_par", "modifie_le", "publie_empreinte")
    out = inserts("qualifications", cols, lignes, "INSERT OR IGNORE")
    out.append(f"INSERT INTO revisions (dossier_an, statut, doc, motif_ecart, auteur, date, commentaire) "
               f"SELECT dossier_an, statut, doc, motif_ecart, modifie_par, modifie_le, {sql_valeur(commentaire)} "
               f"FROM qualifications WHERE modifie_par = {sql_valeur(auteur)} AND dossier_an NOT IN "
               f"(SELECT dossier_an FROM revisions);")
    return out


TABLES = {"textes": ("id", COLONNES_TEXTES), "scrutins": ("id", COLONNES_SCRUTINS),
          "groupes": ("id", COLONNES_GROUPES), "catalogue_meta": ("cle", ("cle", "valeur"))}
PAGE = 4000  # lignes lues par requête dans D1


def _requete(admin: Path, cible: str, sql: str) -> list[dict]:
    cmd = ["npx", "wrangler", "d1", "execute", BASE, f"--{cible}", "--json", f"--command={sql}"]
    sortie = subprocess.run(cmd, cwd=admin, check=True, capture_output=True, text=True).stdout
    return json.loads(sortie)[0]["results"]


def lire_d1(admin: Path, cible: str) -> dict[str, dict[str, str]]:
    """Catalogue présent dans D1 : table → clé → ligne sérialisée (comme dans un INSERT)."""
    out = {}
    for table, (cle, cols) in TABLES.items():
        lignes, page = [], 0
        while True:
            lot = _requete(admin, cible, f"SELECT {', '.join(cols)} FROM {table} ORDER BY {cle} "
                                         f"LIMIT {PAGE} OFFSET {page * PAGE}")
            lignes += lot
            if len(lot) < PAGE:
                break
            page += 1
        out[table] = {str(r[cle]): _ligne(r, cols) for r in lignes}
    return out


def _ligne(r: dict, cols: tuple[str, ...]) -> str:
    # Les nombres entiers relus de D1 en flottants (1.0) s'écrivent comme à l'insertion (1).
    def norme(v):
        return int(v) if isinstance(v, float) and v.is_integer() else v
    return ", ".join(sql_valeur(norme(r.get(c))) for c in cols)


def difference(cat: dict[str, list[dict]], present: dict[str, dict[str, str]]) -> tuple[list[str], dict]:
    """Instructions qui amènent D1 de `present` au catalogue `cat`, et le décompte des lignes touchées."""
    out, compte = [], {}
    for table, (cle, cols) in TABLES.items():
        voulu = {str(r[cle]): r for r in cat[table]}
        avant = present.get(table, {})
        changees = [r for k, r in voulu.items() if avant.get(k) != _ligne(r, cols) and k != "sync"]
        disparues = sorted(set(avant) - set(voulu))
        for i in range(0, len(disparues), LOT):
            ids = ", ".join(sql_valeur(k) for k in disparues[i:i + LOT])
            out.append(f"DELETE FROM {table} WHERE {cle} IN ({ids});")
        out += inserts(table, cols, changees, "INSERT OR REPLACE")
        compte[table] = {"ecrites": len(changees), "effacees": len(disparues)}
    sync = [r for r in cat["catalogue_meta"] if r["cle"] == "sync"]
    out += inserts("catalogue_meta", ("cle", "valeur"), sync, "INSERT OR REPLACE")
    return out, compte


def alertes(cat: dict[str, list[dict]], qualifs: list[tuple[str, str]]) -> list[str]:
    """Scrutins retenus dans une qualification de D1 qui disparaissent du catalogue ou changent de
    dossier (renumérotés ou rattachés ailleurs) : la qualification est à revoir dans l'admin."""
    scrutins = {r["id"]: r for r in cat["scrutins"]}
    out = []
    for dossier, doc in qualifs:
        for s in json.loads(doc).get("scrutins", []):
            r = scrutins.get(s["id"])
            if r is None:
                out.append(f"{dossier} : scrutin retenu {s['id']} absent du nouveau catalogue")
            elif s.get("role") != "censure" and r["texte_id"] != dossier:
                out.append(f"{dossier} : scrutin retenu {s['id']} rattaché désormais à {r['texte_id'] or 'aucun dossier'}")
    return out


def script(export: Path, editorial_doc: dict | None = None, brouillons_lignes: list[dict] | None = None,
           avec_catalogue: bool = True) -> str:
    out = ["-- Généré par `lvnd sync-admin` : ne pas éditer."]
    if avec_catalogue or editorial_doc is not None:
        cat = catalogue(export)
        for table, cols in (("textes", COLONNES_TEXTES), ("scrutins", COLONNES_SCRUTINS),
                            ("groupes", COLONNES_GROUPES), ("catalogue_meta", ("cle", "valeur"))):
            out.append(f"DELETE FROM {table};")
            out += inserts(table, cols, cat[table])
    if editorial_doc is not None:
        out += _qualifs(qualifications(editorial_doc), "editorial.json", "import editorial.json")
    if brouillons_lignes:
        out += _qualifs(brouillons_lignes, AUTEUR_BROUILLONS, "brouillon préparé par Claude, à relire")
    return "\n".join(out) + "\n"


def sync(export: Path, admin: Path, cible: str, avec_editorial: bool, sortie: Path | None,
         dossier_brouillons: Path | None = None, valider: str | None = None, complet: bool = False,
         simuler: bool = False, remplacer: str | None = None) -> None:
    doc = editorial.charger() if avec_editorial else None
    if remplacer is not None and (not dossier_brouillons or valider is not None):
        raise SystemExit("--remplacer s'utilise avec --brouillons DOSSIER, sans --valider")
    if cible != "sql" and not complet and valider is None and dossier_brouillons is None:
        cat = catalogue(export)
        instructions, compte = difference(cat, lire_d1(admin, cible))
        for a in alertes(cat, [(q["dossier_an"], q["doc"]) for q in
                               _requete(admin, cible, "SELECT dossier_an, doc FROM qualifications")]):
            print(f"ALERTE {a}", file=sys.stderr)
        print("Sync incrémental : " + ", ".join(f"{t} {c['ecrites']} écrites, {c['effacees']} effacées"
                                                for t, c in compte.items()), file=sys.stderr)
        if doc is not None:
            instructions += _qualifs(qualifications(doc), "editorial.json", "import editorial.json")
        sql = "\n".join(["-- Généré par `lvnd sync-admin` (incrémental) : ne pas éditer.", *instructions]) + "\n"
        if simuler:
            return
    elif valider is not None:
        if not dossier_brouillons:
            raise SystemExit("--valider s'utilise avec --brouillons DOSSIER")
        sql = "\n".join(["-- Généré par `lvnd sync-admin --valider` : ne pas éditer.",
                         *validations(dossier_brouillons, valider)]) + "\n"
    elif remplacer is not None:
        sql = "\n".join(["-- Généré par `lvnd sync-admin --remplacer` : ne pas éditer.",
                         *remplacements(brouillons(dossier_brouillons), remplacer)]) + "\n"
    else:
        # `--brouillons` seul n'ajoute que les brouillons, sans réécrire le catalogue (économie de lignes D1)
        lignes = brouillons(dossier_brouillons) if dossier_brouillons else None
        sql = script(export, doc, lignes, avec_catalogue=dossier_brouillons is None)
    fichier = sortie or admin / ".wrangler" / "sync-admin.sql"
    fichier.parent.mkdir(parents=True, exist_ok=True)
    fichier.write_text(sql)
    print(f"{fichier} ({len(sql) / 1e6:.1f} Mo)", file=sys.stderr)
    if cible == "sql":
        return
    cmd = ["npx", "wrangler", "d1", "execute", BASE, f"--{cible}", f"--file={fichier.resolve()}", "--yes"]
    print(" ".join(cmd), file=sys.stderr)
    subprocess.run(cmd, cwd=admin, check=True)
