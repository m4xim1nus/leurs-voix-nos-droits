"""Lecture de Dosleg : mini-dump au format COPY de PostgreSQL."""

import pytest

from lvnd import build, editorial, parcours, scores, senat
from lvnd.cli import EXPORT

COPIES = {
    "scr": (senat.TABLES["scr"], [["2026", "41", "C1", "sur l\\u0027ensemble", "2026-10-27", "334", "334", "229", "105", "\\N"]]),
    "votsen": (senat.TABLES["votsen"], [["2026", "41", "1A", "1", "0", "\\N", "\\N"], ["2026", "41", "2B", "2", "0", "1A", "*"],
                                        ["2026", "41", "3C", "4", "8", "\\N", "\\N"], ["2021", "1", "1A", "1", "0", "\\N", "\\N"]]),
    "stavot": (senat.TABLES["stavot"], [["0", "Sans statut"], ["8", "Président de séance"]]),
    "corscr": (senat.TABLES["corscr"], [["2026", "41", "1", "M. X aurait souhaité voter contre.\\r\\n", "https://x"],
                                        ["2026", "41", "0", " ", "\\N"], ["2021", "1", "0", "ancien", "\\N"]]),
    "typlec": (senat.TABLES["typlec"], [["1", "Première lecture"], ["2", "Deuxième lecture"]]),
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


HISTO = """% Requête : select
% from sen
Matricule,Code du groupe politique,Nom court du groupe politique,Date de début d'appartenance,Date de fin d'appartenance
1A,UMP,Groupe Les Républicains,2020-10-05 00:00:00.0,2026-09-30 00:00:00.0
1A,UMP,Groupe Les Républicains,2020-10-05 00:00:00.0,2026-09-30 00:00:00.0
1A,AUCUN,Sénateurs n'appartenant à aucun groupe,2026-10-01 00:00:00.0,2026-10-04 00:00:00.0
1A,UMP,Groupe Les Républicains,2026-10-05 00:00:00.0,
2B,LREM,Groupe RDPI,2023-10-03 00:00:00.0,2029-11-27 00:00:00.0
3C,NI,Réunion administrative des non-inscrits,2023-10-03 00:00:00.0,2026-10-04 00:00:00.0
3C,UNT,Groupe Union Nationale,2026-10-05 00:00:00.0,
"""
GENERAL = """% Requête
Matricule,Qualité,Nom usuel,Prénom usuel,État,Groupe politique,Type d'app au grp politique,Circonscription,Courrier électronique
1A,M.,Un,Alain,ACTIF,Les Républicains,,Saint-Martin,a@senat.fr
2B,Mme,Deux,Béa,ACTIF,RDPI,Rattaché,Alpes de Haute-Provence,Non public
3C,M.,Trois,Céd,ACTIF,UNT,,Corse-du-Sud,c@senat.fr
"""


@pytest.fixture
def odsen(tmp_path):
    for cle, contenu in (("senat_groupes", HISTO), ("senat_senateurs", GENERAL)):
        chemin = senat.extraits(tmp_path, cle)
        chemin.parent.mkdir(parents=True)
        chemin.write_text(contenu, encoding="latin-1")
    return tmp_path


def test_appartenances_sans_aucun_ni_fin_future(odsen):
    a = senat.appartenances(odsen, "2026-10-31").rows()
    # le passage par AUCUN au renouvellement ne coupe pas la période ; 2029 est une erreur de saisie
    assert a == [("1A", "UMP", "2020-10-05", None), ("2B", "LREM", "2023-10-03", None),
                 ("3C", "NI", "2023-10-03", "2026-10-04"), ("3C", "UNT", "2026-10-05", None)]


def test_groupes_sigle_des_membres_en_poste(odsen):
    g = senat.groupes(odsen, {"UMP", "LREM", "NI"}, "2026-10-31").rows()
    assert g == [("LREM", "RDPI", "RDPI"), ("NI", "NI", "Réunion administrative des non-inscrits"),
                 ("UMP", "Les Républicains", "Les Républicains")]


def test_senateurs_departement_et_courriel_public(odsen):
    s = senat.senateurs(odsen, {"1A", "2B", "3C"}, {"alpes de haute provence": "04", "corse du sud": "2A"})
    assert s.select("id", "departement", "courriel", "etat").rows() == [
        ("1A", "978", "a@senat.fr", "actif"), ("2B", "04", None, "actif"), ("3C", "2A", "c@senat.fr", "actif")]
    with pytest.raises(SystemExit, match="Corse-du-Sud"):
        senat.senateurs(odsen, {"3C"}, {})


def test_votes_groupe_du_jour_et_marques(tables, odsen):
    scr = senat.scrutins(tables)
    v = senat.votes(tables, scr, senat.appartenances(odsen, "2026-10-31"))
    assert v.select("senateur_id", "groupe_id", "position", "statut", "delegue_a", "mise_au_point").rows() == [
        ("1A", "UMP", "pour", None, "2B", False), ("2B", "LREM", "contre", None, None, True),
        ("3C", "UNT", "non_votant", "Président de séance", None, False)]
    assert senat.ventilations(v)[0] == {"scrutin_id": "SN2026-41", "groupe_id": "LREM", "membres": 1, "pour": 0,
                                        "contre": 1, "abstention": 0, "non_votants": 0}


def test_scrutin_decompte_de_la_liste_nominative(tables, odsen):
    v = senat.votes(tables, senat.scrutins(tables), senat.appartenances(odsen, "2026-10-31"))
    s = senat.export_scrutins(tables, v, {"85760": "DL1"}).to_dicts()[0]
    assert (s["pour"], s["contre"], s["pour_scr"], s["contre_scr"], s["non_votants"]) == (1, 1, 229, 105, 1)
    assert (s["sort"], s["requis"], s["dossier_id"], s["signet"], s["lecture"]) == ("rejete", 2, "DL1", "ppl24-001", "Première lecture")
    assert s["url"] == "https://www.senat.fr/scrutin-public/2026/scr2026-41.html"


def test_mises_au_point_sans_lignes_vides(tables):
    m = senat.mises_au_point(tables, senat.scrutins(tables)).rows()
    assert m == [("SN2026-41", 1, "M. X aurait souhaité voter contre.", "https://x")]


def test_votes_mensuels(tables, odsen, tmp_path):
    v = senat.votes(tables, senat.scrutins(tables), senat.appartenances(odsen, "2026-10-31"))
    assert build._ecrire_votes_senat(tmp_path, v) == 1
    assert (tmp_path / "votes/2026-10.csv").read_text().splitlines() == [
        "scrutin,senateur,position,statut,delegue_a,mise_au_point",
        "2026-41,1A,P,,2B,", "2026-41,2B,C,,,1", "2026-41,3C,N,Président de séance,,"]


def _classe(uid, loicod, statut, dates):
    return {"uid": uid, "statut": statut, "sn": {"loicod": loicod} if loicod else None,
            "lectures": [{"dec": {}, "date": d} for d in dates]}


def test_dossier_de_l_an_d_une_loi_du_senat():
    classes = [_classe("A", "1", "promulguee", ["2024-01-01"]), _classe("B", "1", "autre", ["2025-01-01", "2025-02-01"]),
               _classe("C", "2", "autre", ["2025-01-01"]), _classe("D", "2", "autre", ["2025-03-01"]), _classe("E", None, "autre", [])]
    assert parcours.dossier_par_loi(classes) == {"1": "A", "2": "D"}


def test_les_exports_du_senat_ne_changent_pas_les_scores_de_l_an(tmp_path):
    """Garde-fou du cycle Sénat : les scores de l'AN ne lisent rien dans data/export/senat/."""
    qualif = editorial.charger()
    senat_factice = tmp_path / "avec"
    senat_factice.mkdir()
    sans = tmp_path / "sans"
    sans.mkdir()
    for f in EXPORT.iterdir():
        if f.name != "senat":
            (sans / f.name).symlink_to(f)
            (senat_factice / f.name).symlink_to(f)
    (senat_factice / "senat/votes").mkdir(parents=True)
    (senat_factice / "senat/scrutins.csv").write_text("illisible\n")
    (senat_factice / "senat/votes/2024-01.csv").write_text("illisible\n")
    assert scores.depuis_export(senat_factice, qualif) == scores.depuis_export(sans, qualif)

