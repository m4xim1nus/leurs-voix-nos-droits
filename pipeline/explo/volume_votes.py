"""Spike : volume des votes nominatifs AN (XVIe, XVIIe) et taille de stockage selon le format.

Question : peut-on versionner tous les votes nominatifs, sous forme compacte, pour que
qualifier un nouveau scrutin dans l'admin n'exige pas de relancer le pipeline ?

    uv run python explo/volume_votes.py
"""

import gzip
import io
import json
import sqlite3
import sys
import tempfile
from collections import Counter
from pathlib import Path

import polars as pl

RAW = Path(__file__).resolve().parents[2] / "data/raw"
ICI = Path(__file__).parent
POS = {"pours": "P", "contres": "C", "abstentions": "A", "nonVotants": "N"}


def liste(v):
    return [] if v is None else v if isinstance(v, list) else [v]


def votes(leg: int):
    mises_au_point = Counter()
    for p in sorted((RAW / f"an_scrutins_{leg}/x/json").glob("VTANR5*.json")):
        s = json.loads(p.read_text())["scrutin"]
        for g in liste(s["ventilationVotes"]["organe"]["groupes"]["groupe"]):
            nom = g["vote"].get("decompteNominatif") or {}
            for k, code in POS.items():
                bloc = nom.get(k)
                for v in liste(bloc.get("votant") if isinstance(bloc, dict) else None):
                    yield {"scrutin": s["uid"], "acteur": v["acteurRef"], "groupe": g["organeRef"],
                           "position": code, "delegation": v.get("parDelegation") == "true"}
        if s.get("miseAuPoint"):
            for k, bloc in s["miseAuPoint"].items():
                if isinstance(bloc, dict):
                    mises_au_point[k] += len(liste(bloc.get("votant")))
    print(f"  mises au point (XV{'I' * (leg - 15)}e) : {dict(mises_au_point)}", file=sys.stderr)


def taille(octets: int) -> str:
    return f"{octets / 1e6:6.1f} Mo"


def main():
    dfs = []
    for leg in (16, 17):
        df = pl.DataFrame(list(votes(leg)))
        print(f"XV{'I' * (leg - 15)}e : {df['scrutin'].n_unique():,} scrutins, {len(df):,} votes nominatifs, "
              f"{df['acteur'].n_unique()} députés", file=sys.stderr)
        print("  " + str(dict(df.group_by("position").len().iter_rows())), file=sys.stderr)
        dfs.append(df.with_columns(pl.lit(leg).alias("legislature")))
    df = pl.concat(dfs)
    df.write_parquet(ICI / "out_votes.parquet")

    # formats compacts : identifiants entiers (VTANR5L17V1234 → 17·10⁵ + 1234, PA123 → 123)
    compact = df.select(
        (pl.col("legislature") * 100_000 + pl.col("scrutin").str.extract(r"V(\d+)$").cast(pl.Int32)).alias("scrutin"),
        pl.col("acteur").str.slice(2).cast(pl.Int32).alias("acteur"),
        pl.col("position"),
    )
    print(f"\nTotal : {len(df):,} lignes", file=sys.stderr)
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        csv = compact.write_csv().encode()
        print(f"  CSV brut (ids entiers)      {taille(len(csv))}", file=sys.stderr)
        print(f"  CSV gzip                    {taille(len(gzip.compress(csv, 9)))}", file=sys.stderr)
        compact.write_parquet(t / "v.parquet", compression="zstd", compression_level=19)
        print(f"  Parquet zstd                {taille((t / 'v.parquet').stat().st_size)}", file=sys.stderr)
        con = sqlite3.connect(t / "v.sqlite")
        con.execute("create table vote (scrutin int, acteur int, position text, primary key (scrutin, acteur)) without rowid")
        con.executemany("insert into vote values (?,?,?)", compact.iter_rows())
        con.commit()
        con.execute("vacuum")
        con.close()
        print(f"  SQLite (without rowid)      {taille((t / 'v.sqlite').stat().st_size)}", file=sys.stderr)
        # une ligne par scrutin : positions par député, séparées par position
        par_scr = (compact.group_by("scrutin", "position").agg(pl.col("acteur").sort())
                   .sort("scrutin", "position"))
        j = json.dumps([[s, p, a] for s, p, a in par_scr.iter_rows()], separators=(",", ":")).encode()
        print(f"  JSON par scrutin            {taille(len(j))}, gzip {taille(len(gzip.compress(j, 9)))}",
              file=sys.stderr)
        # même chose, en un fichier par législature et par mois (diffs git plus courts)
        print(f"  Fichiers JSON par mois : ~{len(j) / 48 / 1e3:.0f} Ko en moyenne", file=sys.stderr)


if __name__ == "__main__":
    main()
