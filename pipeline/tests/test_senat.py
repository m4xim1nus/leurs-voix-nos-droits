"""Lecture de Dosleg : mini-dump au format COPY de PostgreSQL."""

import pytest

from lvnd import senat

COPIES = {
    "scr": (senat.TABLES["scr"], [["2026", "41", "C1", "sur l\\u0027ensemble", "2026-10-27", "334", "334", "229", "105"]]),
    "date_seance": (senat.TABLES["date_seance"], [["C1", "LA1", "2026-10-27 00:00:00"], ["C2", "LA2", "2026-11-20 00:00:00"]]),
    "lecass": (senat.TABLES["lecass"], [["LA1", "L1", "S"], ["LA2", "L2", "S"], ["LA3", "L1", "A"]]),
    "lecture": (senat.TABLES["lecture"], [["L1", "85760", "1"], ["L2", "85761", "2"]]),
    "loi": (senat.TABLES["loi"], [["85760", "ppl", "01", "ppl24-001", "\\N", "Titre"], ["85761", "pjl", "06", "\\N", "\\N", "\\N"]]),
    "texte": (senat.TABLES["texte"], [["1", "2", "LA1", "2026-10-27 00:00:00"], ["2", "29", "LA1", "2026-10-20 00:00:00"],
                                      ["3", "9", "LA3", "2026-09-01 00:00:00"]]),
    "oritxt": (senat.TABLES["oritxt"], [["2", "adopté", "N"], ["29", "commission", "N"], ["9", "définitif", "D"]]),
}


@pytest.fixture
def tables(tmp_path):
    d = tmp_path / "senat_dosleg" / "x"
    d.mkdir(parents=True)
    sql = ["-- dump", "COPY public.autre (a) FROM stdin;", "x", "\\."]
    for nom, (cols, lignes) in COPIES.items():
        # une colonne en plus : seules celles de TABLES sont gardées
        sql.append(f"COPY public.{nom} ({', '.join(cols)}, extra) FROM stdin;")
        sql += ["\t".join([*l, "z"]) for l in lignes]
        sql.append("\\.")
    (d / "dosleg.sql").write_text("\n".join(sql) + "\n")
    return senat.dosleg(tmp_path)


def test_tables_et_nils(tables):
    assert set(tables) == set(senat.TABLES)
    assert tables["loi"]["signet"].to_list() == ["ppl24-001", None]


def test_decisions_seance_ignore_les_textes_de_commission(tables):
    assert senat.decisions_seance(tables) == {("85760", "1"): ("2026-10-27", "adopte")}


def test_activite_et_seances(tables):
    assert sorted(senat.activite(tables)["85760"]) == ["2026-09-01", "2026-10-20", "2026-10-27", "2026-10-27"]
    assert senat.seances(tables) == {"85760": ["2026-10-27"], "85761": ["2026-11-20"]}


def test_etats_et_definitifs(tables):
    assert senat.etats(tables) == {"85760": "en_cours", "85761": "retire"}
    assert senat.adoptes_definitivement(tables) == {"85760"}
    assert senat.lois(tables)["par_signet"]["ppl24-001"]["loicod"] == "85760"


def test_scrutins_decomptes(tables):
    s = senat.scrutins(tables).to_dicts()[0]
    assert (s["id"], s["sort"], s["pour"], s["contre"], s["loicod"], s["typleccod"]) == ("SN2026-41", "adopte", 229, 105, "85760", "1")


def test_dump_absent(tmp_path):
    with pytest.raises(SystemExit, match="lvnd download senat_dosleg"):
        senat.dosleg(tmp_path)
