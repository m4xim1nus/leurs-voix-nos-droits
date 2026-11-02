"""Alertes : des avertissements, jamais un échec de `lvnd check`."""

import polars as pl
import pytest

from lvnd import alertes, build, check, sync_admin


def scrutin(id_, dossier="D", date="2026-01-01", numero=1, objet="ensemble", pour=100, contre=50, sort="adopte"):
    return {"id": id_, "dossier_id": dossier, "date": date, "numero": numero, "objet": objet, "pour": pour,
            "contre": contre, "sort": sort}


def texte(id_="D", decisif=None):
    return {"id": id_, "titre": f"Titre {id_}", "decisif_propose": decisif}


def qualif(textes=(), ecartes=()):
    return {"textes": list(textes), "ecartes": list(ecartes)}


def qualifie(dossier="D", *scrutins):
    return {"dossier_an": dossier, "scrutins": [{"id": i, "role": r} for i, r in scrutins]}


def types(rows):
    return [(r["type"], r["dossier_id"], r["scrutin_id"]) for r in rows]


def test_vote_posterieur():
    ss = [scrutin("S1", date="2026-01-01"), scrutin("S2", date="2026-11-18")]
    r = alertes.calculer([texte(decisif="S2")], ss, [], qualif([qualifie("D", ("S1", "decisif"))]))
    assert types(r) == [("vote_posterieur", "D", "S2")]
    assert r[0]["date"] == "2026-11-18" and "S1 du 2026-01-01 (100-50)" in r[0]["detail"]


def test_le_decisif_retenu_ne_declenche_rien():
    ss = [scrutin("S1", date="2026-01-01"), scrutin("S2", date="2026-11-18")]
    assert alertes.calculer([texte(decisif="S2")], ss, [], qualif([qualifie("D", ("S2", "decisif"))])) == []
    # même jour : le numéro départage
    ss = [scrutin("S1", numero=1), scrutin("S2", numero=2)]
    assert types(alertes.calculer([texte(decisif="S2")], ss, [], qualif([qualifie("D", ("S1", "decisif"))]))) == [
        ("vote_posterieur", "D", "S2")]


def test_vote_posterieur_a_une_motion_de_censure():
    """Texte adopté par 49.3 sans vote final : la référence est la motion retenue."""
    ss = [scrutin("M", objet="motion_censure", date="2026-01-01"), scrutin("S", date="2026-06-01")]
    r = alertes.calculer([texte(decisif="S")], ss, [], qualif([qualifie("D", ("M", "censure"))]))
    assert types(r) == [("vote_posterieur", "D", "S")]


def test_suppression_article_unique_compte_si_adoptee():
    ss = [scrutin("S1"), scrutin("S2", date="2026-02-01", objet="suppression_article_unique", sort="rejete")]
    assert alertes.calculer([texte(decisif="S1")], ss, [], qualif([qualifie("D", ("S1", "decisif"))])) == []
    ss[1]["sort"] = "adopte"
    assert len(alertes.calculer([texte(decisif="S1")], ss, [], qualif([qualifie("D", ("S1", "decisif"))]))) == 1


def test_ecart_revote():
    """AGRASC : écarté faute de source, un vote sur les conclusions de la CMP doit se voir."""
    ecart = {"dossier_an": "D", "motif": "Aucune source admise sur une de ses mesures (règle 8)."}
    avant = scrutin("S1", date="2026-06-03")
    assert alertes.calculer([texte()], [avant], [], qualif(ecartes=[ecart])) == []
    apres = scrutin("S2", date="2026-11-18", pour=120, contre=45)
    r = alertes.calculer([texte()], [avant, apres], [], qualif(ecartes=[ecart]))
    assert types(r) == [("ecart_revote", "D", "S2")]
    assert "120-45" in r[0]["detail"]
    # le motif relu cite ce vote : l'alerte tombe
    relu = {**ecart, "motif": "Toujours aucune source admise après le vote de la CMP (120-45) (règle 8)."}
    assert alertes.calculer([texte()], [avant, apres], [], qualif(ecartes=[relu])) == []


def test_ecart_revote_ni_unanimite_ni_amendement():
    unanime = {"dossier_an": "D", "motif": "Adopté sans aucune voix contre au scrutin décisif (21-0) (règle 9)."}
    apres = scrutin("S2", date="2026-11-18", pour=120, contre=0)
    assert alertes.calculer([texte()], [apres], [], qualif(ecartes=[unanime])) == []
    ecart = {"dossier_an": "D", "motif": "Hors de la grille."}
    amdt = scrutin("S3", date="2026-11-18", objet="amendement")
    assert alertes.calculer([texte()], [amdt], [], qualif(ecartes=[ecart])) == []


def test_ecart_revote_sans_scrutin_public():
    ecart = {"dossier_an": "D", "motif": "Aucune source admise."}
    lecture = {"texte_id": "D", "etape": "CMP", "chambre": "AN", "date": "2026-11-19", "issue": "adopté",
               "mode_adoption": "MAIN_LEVEE", "scrutin_id": None, "motif_ecart": None}
    r = alertes.calculer([texte()], [], [], qualif(ecartes=[ecart]), lectures=[lecture])
    assert types(r) == [("ecart_revote", "D", None)] and r[0]["id"] == "ecart_revote:D:CMP"
    relu = {**ecart, "motif": "Aucune source admise, vote à main levée du 19/11/2026."}
    assert alertes.calculer([texte()], [], [], qualif(ecartes=[relu]), lectures=[lecture]) == []


def test_unanimite_contestee():
    motif = "Adopté sans aucune voix contre au scrutin décisif (96 pour, 0 contre) : ce vote ne départage aucun député (règle 9)."
    ecarte = {"dossier_an": "D", "motif": motif}
    # toujours unanime : rien
    assert alertes.calculer([texte(decisif="S1")], [scrutin("S1", contre=0)], [], qualif(ecartes=[ecarte])) == []
    # nouveau décisif contesté
    r = alertes.calculer([texte(decisif="S2")], [scrutin("S1", contre=0), scrutin("S2", date="2026-11-19")], [],
                         qualif(ecartes=[ecarte]))
    assert types(r) == [("unanimite_contestee", "D", "S2")]
    # écarté pour un autre motif : rien
    assert alertes.calculer([texte(decisif="S2")], [scrutin("S2")], [], qualif(ecartes=[{"dossier_an": "D", "motif": "Résolution"}])) == []


def test_premier_decisif():
    assert types(alertes.calculer([texte(decisif="S1")], [scrutin("S1")], [], qualif())) == [("premier_decisif", "D", "S1")]
    # sans décisif : rien
    assert alertes.calculer([texte()], [], [], qualif()) == []


def test_inscrit():
    pts = [{"dossier_id": "D", "date": "2026-11-19", "instance": "seance"},
           {"dossier_id": "D", "date": "2026-11-18", "instance": "seance"},
           {"dossier_id": "D", "date": "2026-11-01", "instance": "commission"},
           {"dossier_id": "C", "date": "2026-11-18", "instance": "commission"},
           {"dossier_id": "HORS", "date": "2026-11-18", "instance": "seance"}]
    r = alertes.calculer([texte(), texte("C")], [], pts, qualif())
    assert types(r) == [("inscrit", "D", None)]  # séance seulement, et au catalogue
    assert r[0]["date"] == "2026-11-18" and "voté" not in r[0]["detail"]
    # déjà traité : rien
    assert alertes.calculer([texte()], [], pts, qualif(ecartes=[{"dossier_an": "D", "motif": "m"}])) == []
    assert alertes.calculer([texte()], [], pts, qualif([qualifie("D")])) == []
    # une fiche de suivi répond à l'inscription, pas au vote qui suit
    suivi = {**qualif(), "suivis": [{"dossier_an": "D"}]}
    assert alertes.calculer([texte()], [], pts, suivi) == []
    r = alertes.calculer([texte(decisif="S1")], [scrutin("S1")], pts, suivi)
    assert types(r) == [("premier_decisif", "D", "S1")]


def lecture(dossier="D", etape="AN1", chambre="AN", date="2026-10-23", issue="rejete", mode="SCRUTIN_ORDINAIRE",
            scrutin=None, motif=None):
    return {"texte_id": dossier, "etape": etape, "chambre": chambre, "date": date, "issue": issue, "mode_adoption": mode,
            "scrutin_id": scrutin, "motif_ecart": motif}


def test_vote_sans_decisif():
    # Rejet d'une partie (PLFSS 2027, V9097) : un scrutin, mais pas de décisif proposé.
    partie = [scrutin("V9097", objet="partie", pour=1, contre=115, sort="rejete", date="2026-10-23")]
    r = alertes.calculer([texte()], partie, [], qualif(), lectures=[lecture(scrutin="V9097")])
    assert types(r) == [("vote_sans_decisif", "D", "V9097")]
    assert r[0]["id"] == "vote_sans_decisif:D:AN1" and "partie" in r[0]["detail"] and "1-115" in r[0]["detail"]
    # Vote sur l'ensemble sans scrutin public : la dernière lecture de l'AN, une seule alerte.
    mains = [lecture(issue="adopte", mode="MAIN_LEVEE", date="2026-10-05"),
             lecture(etape="AN2", issue="adopte", mode="MAIN_LEVEE", date="2026-10-29")]
    r = alertes.calculer([texte()], [], [], qualif(), lectures=mains)
    assert types(r) == [("vote_sans_decisif", "D", None)] and r[0]["id"].endswith(":AN2")
    assert "MAIN_LEVEE" in r[0]["detail"]
    # Une fiche de suivi ne répond pas au vote.
    suivi = {**qualif(), "suivis": [{"dossier_an": "D"}]}
    assert types(alertes.calculer([texte()], [], [], suivi, lectures=mains))[0][0] == "vote_sans_decisif"


def test_lecture_posterieure():
    # Texte qualifié, adopté définitivement à main levée après son décisif : rien ne le voyait.
    q = qualif([{**qualifie("D", ("S1", "decisif")), "note": "Scrutin décisif : S1."}])
    avant = lecture(etape="AN1", issue="adopte", mode="SCRUTIN_ORDINAIRE", date="2026-01-01", scrutin="S1")
    cmp_ = lecture(etape="CMP", issue="adopte", mode="MAIN_LEVEE", date="2026-11-19")
    r = alertes.calculer([texte(decisif="S1")], [scrutin("S1")], [], q, lectures=[avant, cmp_])
    assert types(r) == [("lecture_posterieure", "D", None)] and r[0]["id"] == "lecture_posterieure:D:CMP"
    assert "MAIN_LEVEE" in r[0]["detail"] and "après le décisif S1" in r[0]["detail"]
    # La note relue cite la date de la lecture : l'alerte tombe.
    relu = qualif([{**qualifie("D", ("S1", "decisif")), "note": "Adopté à main levée le 19/11/2026 (règle 9)."}])
    assert alertes.calculer([texte(decisif="S1")], [scrutin("S1")], [], relu, lectures=[avant, cmp_]) == []
    # Lecture close par une motion de rejet après le décisif : vue aussi, avec son scrutin, tant qu'il n'est pas retenu.
    motion = scrutin("M", objet="motion_rejet", date="2026-11-19", numero=2)
    rejet = lecture(etape="AN2", issue="rejete", mode="MOTION_REJET", date="2026-11-19", scrutin="M")
    r = alertes.calculer([texte(decisif="S1")], [scrutin("S1"), motion], [], q, lectures=[rejet])
    assert types(r) == [("lecture_posterieure", "D", "M")]
    retenue = qualif([qualifie("D", ("S1", "decisif"), ("M", "motion"))])
    assert alertes.calculer([texte(decisif="S1")], [scrutin("S1"), motion], [], retenue, lectures=[rejet]) == []


def test_vote_posterieur_sans_decisif_a_l_an():
    # Texte qualifié sur le seul vote du Sénat, l'AN ayant voté une motion de rejet (audiovisuel public, DLR5L16N47697).
    q = qualif([qualifie("D", ("M", "motion"))])
    motion = scrutin("M", objet="motion_rejet", date="2025-03-01")
    ensemble = scrutin("S", date="2026-12-01", numero=2)
    r = alertes.calculer([texte(decisif="S")], [motion, ensemble], [], q)
    assert types(r) == [("vote_posterieur", "D", "S")] and "après M du 2025-03-01" in r[0]["detail"]
    # Aucun scrutin de l'AN retenu (Sénat seul) : tout vote de l'AN sur l'ensemble est nouveau.
    r = alertes.calculer([texte(decisif="S")], [ensemble], [], qualif([qualifie("D")]))
    assert types(r) == [("vote_posterieur", "D", "S")] and "aucun scrutin de l'AN retenu" in r[0]["detail"]


def test_vote_sans_decisif_hors_champ():
    l = lecture(issue="adopte", mode="MAIN_LEVEE")
    calc = lambda t, q, ls: alertes.calculer([t], [], [], q, lectures=ls)
    assert types(calc(texte(), qualif([qualifie("D")]), [l])) == [("lecture_posterieure", "D", None)]  # qualifié : l'autre alerte
    assert calc(texte(), qualif(ecartes=[{"dossier_an": "D", "motif": "m"}]), [l]) == []  # écarté
    assert calc(texte(), qualif(), [lecture(motif="inactif", issue="adopte")]) == []  # à l'arrêt
    assert calc(texte(), qualif(), [lecture(chambre="SN")]) == []  # Sénat
    assert calc(texte(), qualif(), [lecture(issue=None)]) == []  # lecture ouverte
    assert calc(texte("AUTRE"), qualif(), [l]) == []  # hors catalogue
    # Un décisif proposé : c'est `premier_decisif` qui parle.
    r = alertes.calculer([texte(decisif="S1")], [scrutin("S1")], [], qualif(), lectures=[l])
    assert types(r) == [("premier_decisif", "D", "S1")]


def test_scrutins_recents_hors_du_taux_de_rattachement():
    import sqlite3
    con = sqlite3.connect(":memory:")
    con.execute("create table scrutins (legislature int, date text, objet text, amendement_id text)")
    lignes = [(17, "2026-01-01", "amendement", "A"), (17, "2026-01-02", "amendement", None),
              (17, "2026-10-29", "amendement", None), (17, "2026-10-30", "amendement", "B"),
              (17, "2026-10-30", "ensemble", None)]
    con.executemany("insert into scrutins values (?, ?, ?, ?)", lignes)
    assert check.rattachement_amendements(con, 17) == (2, 1, 1)
    # L'archive bloquée depuis plus de 14 jours : ces scrutins comptent de nouveau, et le taux baisse.
    con.execute("insert into scrutins values (17, '2026-12-01', 'ensemble', null)")
    assert check.rattachement_amendements(con, 17) == (4, 2, 0)
    # Législature close : ni délai ni scrutin « récent ».
    con.execute("update scrutins set legislature = 16")
    con.execute("delete from scrutins where date = '2026-12-01'")
    assert check.rattachement_amendements(con, 16) == (4, 2, 0)


def test_identifiants_uniques():
    ss = [scrutin("S1"), scrutin("S2", date="2026-02-01"), scrutin("S3", date="2026-03-01")]
    r = alertes.calculer([texte(decisif="S3")], ss, [], qualif([qualifie("D", ("S1", "decisif"))]))
    assert len({a["id"] for a in r}) == len(r) == 2


def test_liste_vide_garde_les_colonnes():
    """Sans alerte ni point d'agenda (fin de session), le build écrit quand même des tables valides."""
    assert build._df([], alertes.COLONNES).columns == list(alertes.COLONNES)


def test_sync_lit_un_export_sans_alerte(tmp_path):
    build._df([], alertes.COLONNES).write_csv(tmp_path / "en_cours_alertes.csv")
    assert sync_admin._alertes(tmp_path) == []
    r = pl.DataFrame([{c: "x" for c in alertes.COLONNES} | {"scrutin_id": None}]).write_csv(tmp_path / "en_cours_alertes.csv")
    assert r is None and sync_admin._alertes(tmp_path)[0]["scrutin_id"] is None


@pytest.mark.donnees
def test_les_alertes_ne_font_pas_echouer_check(base, monkeypatch):
    """Tout simuler comme non traité : le résultat de `check` ne change pas."""
    ok, lignes = check.verifier(base)
    vraies = alertes.calculer
    monkeypatch.setattr(alertes, "calculer", lambda t, s, p, q, sn=(), l=(): vraies(t, s, p, {"textes": [], "ecartes": []}, sn, l))
    ok2, lignes2 = check.verifier(base)
    assert ok2 == ok
    assert sum(l.startswith("AVERTISSEMENT") for l in lignes2) > sum(l.startswith("AVERTISSEMENT") for l in lignes)


def test_alertes_senat():
    qualif = {"textes": [{"dossier_an": "Q", "scrutins": [], "senat": {"scrutins": [{"id": "S1"}]}},
                         {"dossier_an": "SB", "scrutins": []}], "ecartes": [{"dossier_an": "E", "motif": "règle 8"}]}
    s = lambda i, d, j, o="ensemble": {"id": i, "dossier_id": d, "date": j, "numero": int(i[1:]), "objet": o, "pour": 2, "contre": 1}
    scr = [s("S1", "Q", "2025-01-01"), s("S2", "Q", "2025-06-01"), s("S3", "N", "2025-01-02"), s("S4", "E", "2025-01-02"),
           s("S5", "SB", "2025-01-03"), s("S6", "M", "2025-01-03", "motion_rejet"), s("S7", None, "2025-01-03")]
    out = {a["id"]: a for a in alertes.calculer([], [], [], qualif, scr)}
    assert set(out) == {"senat_vote_posterieur:Q:S2", "senat_premier_vote:N:S3", "senat_premier_vote:SB:S5"}
