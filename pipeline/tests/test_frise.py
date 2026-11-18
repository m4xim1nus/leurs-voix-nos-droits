"""Frise d'un texte : origine (gouvernement ou groupe de l'auteur·ice) et grandes étapes datées."""

from lvnd import an, frise


def acte(code, date, texte=None, **kw):
    return {"codeActe": code, "dateActe": f"{date}T00:00:00.000+02:00", "texteAssocie": texte, **kw}


def dossier(texte, acteurs=(), etapes=()):
    return {"uid": "DLRTEST", "initiateur": {"acteurs": {"acteur": [{"acteurRef": a} for a in acteurs]}},
            "actesLegislatifs": {"acteLegislatif": [{**e, "actesLegislatifs": None} for e in etapes]},
            "_texte": texte}


def classe(d, lectures=(), evts=()):
    return {"uid": "DLRTEST", "dossier": d, "lectures": list(lectures), "evts": list(evts)}


def lecture(chambre, type_lecture, date, statut="TSORTF01", etape="AN1"):
    return {"etape": etape, "chambre": chambre, "type_lecture": type_lecture, "date": date,
            "dec": {"statutConclusion": {"fam_code": statut}} if statut else None}


def evt(type_, date, detail=None):
    return {"type": type_, "date": date, "detail": detail}


def test_projet_de_loi_vient_du_gouvernement(monkeypatch):
    monkeypatch.setattr(an, "enfants", lambda d: d["actesLegislatifs"]["acteLegislatif"])
    monkeypatch.setattr(an, "parcourir", lambda e: [e])
    d = dossier("PRJL", ["PA1"], [acte("AN1-DEPOT", "2023-02-01", "PRJLANR5L16B0001")])
    rows = frise.etapes(classe(d))
    assert rows[0]["etape"] == "depot" and rows[0]["origine"] == "gouvernement"
    assert rows[0]["auteur_groupe"] is None and rows[0]["chambre"] == "AN"


def test_proposition_garde_auteur_cosignataires_et_groupe_a_la_date(monkeypatch):
    monkeypatch.setattr(an, "enfants", lambda d: d["actesLegislatifs"]["acteLegislatif"])
    monkeypatch.setattr(an, "parcourir", lambda e: [e])
    vus = []
    monkeypatch.setattr(an, "_groupe_a_date", lambda raw, a, date: vus.append((a, date)) or "PO800")
    d = dossier("PION", ["PA7", "PA8", "PA9"], [acte("AN1-DEPOT", "2024-09-10", "PIONANR5L17B0001")])
    r = frise.etapes(classe(d), raw=object())[0]
    assert (r["origine"], r["auteur_id"], r["auteur_groupe"], r["cosignataires"]) == ("parlementaire", "PA7", "PO800", 2)
    assert vus == [("PA7", "2024-09-10")]


def test_proposition_du_senat_sans_groupe_connu(monkeypatch):
    monkeypatch.setattr(an, "enfants", lambda d: d["actesLegislatifs"]["acteLegislatif"])
    monkeypatch.setattr(an, "parcourir", lambda e: [e])
    monkeypatch.setattr(an, "_groupe_a_date", lambda raw, a, date: None)
    d = dossier("PION", ["PA7"], [acte("SN1-DEPOT", "2024-09-10", "PIONSNR5S1B0001")])
    r = frise.etapes(classe(d), raw=object())[0]
    assert r["chambre"] == "SN" and r["origine"] == "parlementaire" and r["auteur_groupe"] is None


def test_etapes_dans_l_ordre_une_ligne_par_cmp(monkeypatch):
    monkeypatch.setattr(an, "enfants", lambda d: d["actesLegislatifs"]["acteLegislatif"])
    monkeypatch.setattr(an, "parcourir", lambda e: [e])
    d = dossier("PRJL", [], [acte("AN1-DEPOT", "2023-01-02", "PRJLANR5L16B0001")])
    ls = [lecture("SN", "premiere", "2023-03-01"), lecture("AN", "premiere", "2023-02-01"),
          lecture("AN", "cmp", "2023-05-02", etape="CMP"), lecture("AN", "deuxieme", "2023-04-01", None)]
    es = [evt("cmp_convoquee", "2023-04-20"), evt("cmp_accord", "2023-04-25"),
          evt("decision_cc", "2023-06-01", "Partiellement conforme | https://cc"), evt("promulgation", "2023-06-10", "2023-100")]
    rows = frise.etapes(classe(d, ls, es))
    assert [(r["etape"], r["chambre"], r["issue"]) for r in rows] == [
        ("depot", "AN", None), ("lecture", "AN", "adopte"), ("lecture", "SN", "adopte"),
        ("cmp", None, "accord"), ("cc", None, None), ("promulgation", None, None)]
    assert [r["ordre"] for r in rows] == [1, 2, 3, 4, 5, 6]
    assert rows[4]["detail"] == "Partiellement conforme" and rows[5]["detail"] == "2023-100"


def test_cmp_convoquee_sans_resultat_reste_visible(monkeypatch):
    monkeypatch.setattr(an, "enfants", lambda d: [])
    rows = frise.etapes(classe(dossier("PRJL"), [], [evt("cmp_convoquee", "2025-12-23")]))
    assert [(r["etape"], r["issue"]) for r in rows] == [("cmp", "convoquee")]
