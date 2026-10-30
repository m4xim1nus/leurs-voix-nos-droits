"""Alertes : quatre avertissements, jamais un échec de `lvnd check`."""

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
    monkeypatch.setattr(alertes, "calculer", lambda t, s, p, q: vraies(t, s, p, {"textes": [], "ecartes": []}))
    ok2, lignes2 = check.verifier(base)
    assert ok2 == ok
    assert sum(l.startswith("AVERTISSEMENT") for l in lignes2) > sum(l.startswith("AVERTISSEMENT") for l in lignes)
