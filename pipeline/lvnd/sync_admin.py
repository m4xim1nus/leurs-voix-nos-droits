"""Pousse le catalogue dans la base D1 de l'admin (docs/CONCEPTION.md, Admin).

On lit `data/export/` (versionné) plutôt que la base locale : le sync peut ainsi tourner sans
dump. Le script SQL remplace le catalogue (textes, scrutins rattachés, groupes, grille) et ne
touche jamais aux tables éditoriales, sauf `--editorial`, qui y ajoute les qualifications
publiées absentes de D1 (amorçage, ou reconstruction de D1 depuis git) sans écraser un brouillon.

Le script est exécuté par `wrangler d1 execute` depuis `admin/`. Le premier sync écrit 40 800 lignes
(index compris), un sync suivant environ le double (effacement puis réécriture) : un seul par jour
sous la limite gratuite de D1 (100 000 lignes écrites).
"""

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import polars as pl

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


def inserts(table: str, colonnes: tuple[str, ...], lignes: list[dict], verbe: str = "INSERT") -> list[str]:
    out = []
    for i in range(0, len(lignes), LOT):
        valeurs = ",\n".join("(" + ", ".join(sql_valeur(r.get(c)) for c in colonnes) + ")"
                             for r in lignes[i:i + LOT])
        out.append(f"{verbe} INTO {table} ({', '.join(colonnes)}) VALUES\n{valeurs};")
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
        if r["dossier_id"] not in ids:
            continue
        a = amdts.get(r["amendement_id"] or "", {})
        scrutins.append({
            **{k: r[k] for k in ("id", "legislature", "numero", "date", "type_vote", "titre", "objet", "sort", "pour",
                                 "contre", "abstention", "non_votants", "amendement_id")},
            "texte_id": r["dossier_id"],
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


def script(export: Path, editorial_doc: dict | None = None) -> str:
    cat = catalogue(export)
    out = ["-- Généré par `lvnd sync-admin` : ne pas éditer."]
    for table, cols in (("textes", COLONNES_TEXTES), ("scrutins", COLONNES_SCRUTINS),
                        ("groupes", COLONNES_GROUPES), ("catalogue_meta", ("cle", "valeur"))):
        out.append(f"DELETE FROM {table};")
        out += inserts(table, cols, cat[table])
    if editorial_doc is not None:
        q = qualifications(editorial_doc)
        cols = ("dossier_an", "statut", "doc", "motif_ecart", "modifie_par", "modifie_le", "publie_empreinte")
        out += inserts("qualifications", cols, q, "INSERT OR IGNORE")
        # révision d'origine, seulement pour les qualifications qui viennent d'être créées
        out += [f"INSERT INTO revisions (dossier_an, statut, doc, motif_ecart, auteur, date, commentaire) "
                f"SELECT dossier_an, statut, doc, motif_ecart, modifie_par, modifie_le, 'import editorial.json' "
                f"FROM qualifications WHERE modifie_par = 'editorial.json' AND dossier_an NOT IN "
                f"(SELECT dossier_an FROM revisions);"]
    return "\n".join(out) + "\n"


def sync(export: Path, admin: Path, cible: str, avec_editorial: bool, sortie: Path | None) -> None:
    doc = editorial.charger() if avec_editorial else None
    sql = script(export, doc)
    fichier = sortie or admin / ".wrangler" / "sync-admin.sql"
    fichier.parent.mkdir(parents=True, exist_ok=True)
    fichier.write_text(sql)
    print(f"{fichier} ({len(sql) / 1e6:.1f} Mo)", file=sys.stderr)
    if cible == "sql":
        return
    cmd = ["npx", "wrangler", "d1", "execute", BASE, f"--{cible}", f"--file={fichier.resolve()}", "--yes"]
    print(" ".join(cmd), file=sys.stderr)
    subprocess.run(cmd, cwd=admin, check=True)
