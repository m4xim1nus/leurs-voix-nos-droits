"""Agenda de l'AN : points gardés, écartés, et effet sur l'état d'un texte."""

import json
import sqlite3

import pytest

from lvnd import agenda, encours


def reunion(type_="seance_type", etat="Confirmé", points=()):
    return {"@xsi:type": type_, "uid": "R1", "timeStampDebut": "2026-11-18T21:30:00.000+01:00",
            "cycleDeVie": {"etat": etat}, "organeReuniRef": "PO838901", "ODJ": {"pointsODJ": {"pointODJ": list(points)}}}


def point(uid="P1", etat="Confirmé", dossiers="DLR5L17N53069"):
    refs = {"dossierRef": dossiers} if dossiers else None
    return {"uid": uid, "cycleDeVie": {"etat": etat}, "dossiersLegislatifsRefs": refs,
            "typePointODJ": "Discussion", "objet": "Discussion, en 2e lecture", "procedure": None}


def test_point_de_seance():
    r = agenda.points_reunion(reunion(points=[point()]))
    assert len(r) == 1
    assert (r[0]["dossier_id"], r[0]["date"], r[0]["heure"], r[0]["instance"], r[0]["etat"]) == (
        "DLR5L17N53069", "2026-11-18", "21:30", "seance", "confirme")


def test_points_ecartes():
    assert agenda.points_reunion(reunion(points=[point(etat="Supprimé")])) == []
    assert agenda.points_reunion(reunion(points=[point(etat="Annulé")])) == []
    assert agenda.points_reunion(reunion(etat="Supprimé", points=[point()])) == []
    assert agenda.points_reunion(reunion(points=[point(dossiers=None)])) == []
    assert agenda.points_reunion(reunion(type_="reunionInitParlementaire_type", points=[point()])) == []
    # un seul point dans le dump : un objet, pas une liste
    r = reunion()
    r["ODJ"]["pointsODJ"]["pointODJ"] = point()
    assert len(agenda.points_reunion(r)) == 1


def test_etat_eventuel_et_commission():
    r = agenda.points_reunion(reunion("reunionCommission_type", "Eventuel", [point()]))
    assert (r[0]["instance"], r[0]["etat"]) == ("commission", "eventuel")
    assert agenda.points_reunion(reunion(points=[point(etat="Eventuel")]))[0]["etat"] == "eventuel"


def test_plusieurs_dossiers_et_filtre_de_date(tmp_path):
    d = tmp_path / "an_agenda_17" / "x" / "json" / "reunion"
    d.mkdir(parents=True)
    avant = {**reunion(points=[point()]), "timeStampDebut": "2026-10-01T15:00:00.000+02:00"}
    (d / "avant.json").write_text(json.dumps({"reunion": avant}))
    (d / "apres.json").write_text(json.dumps({"reunion": reunion(points=[point(dossiers=["D2", "D1"])])}))
    assert [p["dossier_id"] for p in agenda.points(tmp_path, "2026-10-29")] == ["D1", "D2"]


def test_dump_absent(tmp_path):
    with pytest.raises(SystemExit, match="lvnd download an_agenda_17"):
        agenda.points(tmp_path, "2026-10-29")


def test_seance_inscrite():
    att = {"attente": "lecture", "etape": "AN2", "chambre": "AN", "type_lecture": "deuxieme"}
    d = {"actesLegislatifs": None}
    # l'agenda suffit, avec ou sans étape ouverte dans le dossier
    assert encours.seance_inscrite(d, att, [], ["2026-11-18"], "2026-10-29") == "2026-11-18"
    assert encours.seance_inscrite(d, None, [], ["2026-11-19"], "2026-10-29") == "2026-11-19"
    # une séance passée n'est pas une inscription
    assert encours.seance_inscrite(d, att, [], ["2026-10-01"], "2026-10-29") is None
    # séance du Sénat : seulement si le texte y est attendu
    assert encours.seance_inscrite(d, att, ["2026-11-20"], [], "2026-10-29") is None
    sn = {**att, "etape": "SN1", "chambre": "SN"}
    assert encours.seance_inscrite(d, sn, ["2026-11-20"], [], "2026-10-29") == "2026-11-20"


@pytest.mark.donnees
def test_agenda_exporte(base):
    con = sqlite3.connect(base)
    assert not con.execute("select 1 from en_cours_agenda where etat not in ('confirme', 'eventuel') "
                           "or instance not in ('seance', 'commission') or dossier_id is null").fetchall()
