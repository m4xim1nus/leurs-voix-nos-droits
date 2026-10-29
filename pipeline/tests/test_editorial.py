import copy
import pytest
import yaml
import json

from lvnd import editorial, referentiels, sync_admin


def _texte(**kw):
    t = {"id": "t", "dossier_an": "DLR5L17N1", "legislature": 17, "titre": "Loi",
         "droits": [{"code": "vie-privee", "role": "principal", "sens": "restreint", "sources": ["s1"]}],
         "sources": {"s1": {"auteur": "CNIL", "titre": "Avis", "date": "2024-01-01", "url": "https://cnil.fr"}},
         "scrutins": [{"id": "D", "role": "decisif", "pour": "texte", "objet": "ensemble"}]}
    t.update(kw)
    return editorial.normaliser(t)


def test_temoins_convertis_et_valides():
    doc = editorial.depuis_temoins(referentiels.temoins())
    assert [t["id"] for t in doc["textes"]] == sorted(t["id"] for t in referentiels.temoins()["textes"])
    for t in doc["textes"]:
        assert list(t) == list(editorial.CLES_TEXTE)
        assert not editorial.valider(t)[0], t["id"]
    kb = next(t for t in doc["textes"] if t["id"] == "kasbarian-berge")
    assert kb["vigilance"][0]["sources"] == []  # chaîne simple → objet
    assert kb["conseil_constitutionnel"].startswith("Censure de l'article 7")


def test_serialisation_deterministe():
    doc = editorial.depuis_temoins(referentiels.temoins())
    melange = copy.deepcopy(doc)
    melange["textes"].reverse()
    assert editorial.serialiser(editorial.document(melange["textes"], [])) == editorial.serialiser(doc)
    assert json.loads(editorial.serialiser(doc)) == doc


def test_erreurs_bloquantes():
    assert editorial.valider(_texte()) == ([], [])
    err, _ = editorial.valider(_texte(droits=[]))
    assert "il faut exactement un droit principal" in err
    err, _ = editorial.valider(_texte(droits=[{"code": "inconnu", "role": "principal", "sens": "etend", "sources": []}]))
    assert {"droit inconnu : inconnu", "inconnu : aucune source"} <= set(err)
    err, _ = editorial.valider(_texte(scrutins=[]))
    assert "il faut exactement un scrutin décisif" in err
    err, _ = editorial.valider(_texte(sources={}))
    assert "source citée mais non définie : s1" in err


def test_avertissements():
    _, av = editorial.valider(_texte(scrutins=[{"id": "D", "role": "decisif", "pour": "texte"},
                                               {"id": "A", "role": "amendement", "pour": "a-trancher"}]))
    assert av == ["A : sens à trancher, scrutin non compté"]
    _, av = editorial.valider(_texte(droits=[{"code": "sante", "role": "principal", "sens": "etend", "sources": ["s1"]}]))
    assert any("règle 7" in a for a in av)


def test_controles_open_data():
    infos = {"D": {"dossier_id": "DLR5L17N1", "etape": "AN1", "division": None},
             "A1": {"dossier_id": "DLR5L17N1", "etape": "AN1", "division": "Article 7"},
             "A2": {"dossier_id": "DLR5L17N1", "etape": "AN1", "division": "Article 7"},
             "X": {"dossier_id": "DLR5L17N2", "etape": "AN1", "division": None}}
    sc = [{"id": "D", "role": "decisif", "pour": "texte"}, {"id": "A1", "role": "amendement", "pour": "contre-texte"},
          {"id": "A2", "role": "amendement", "pour": "contre-texte"}, {"id": "X", "role": "motion", "pour": "texte"}]
    err, _ = editorial.valider(_texte(scrutins=sc), infos)
    assert "X : scrutin absent du dossier DLR5L17N1" in err
    assert any("plusieurs amendements clés sur « Article 7 »" in e for e in err)


def test_sql_echappe_les_apostrophes():
    assert sync_admin.sql_valeur("l'aide") == "'l''aide'"
    assert sync_admin.sql_valeur(None) == "NULL" and sync_admin.sql_valeur(True) == "1"
    sql = sync_admin.inserts("t", ("a", "b"), [{"a": 1, "b": "x"}] * 3)
    assert len(sql) == 1 and sql[0].count("(1, 'x')") == 3
    gros = sync_admin.inserts("t", ("a",), [{"a": "x" * 40_000}] * 5)
    assert len(gros) == 3 and all(len(i.encode()) < 100_000 for i in gros)


def test_qualifications_importees_valides_et_publiees():
    doc = editorial.depuis_temoins(referentiels.temoins())
    q = sync_admin.qualifications(doc)
    assert {r["statut"] for r in q} == {"valide"}
    r = q[0]
    assert r["publie_empreinte"] == sync_admin.empreinte(r["doc"], "valide", None)


def test_brouillons_charges_a_relire_sans_ecraser(tmp_path):
    (tmp_path / "a.yaml").write_text(
        "id: essai\ndossier_an: DLR5L17N1\nlegislature: 17\ntitre: Loi\nstatut: a-relire\n"
        "droits: []\nscrutins: []\nrelecture: {points_attention: [x]}\n")
    (tmp_path / "b.yaml").write_text(
        "id: ''\ndossier_an: DLR5L17N2\nlegislature: 17\ntitre: Loi 2\nstatut: ecarte\nmotif_ecart: organisationnel\n")
    lignes = sync_admin.brouillons(tmp_path)
    assert [(l["statut"], l["motif_ecart"]) for l in lignes] == [("a-relire", None), ("a-relire", "organisationnel")]
    assert "relecture" not in json.loads(lignes[0]["doc"])
    sql = sync_admin.script(tmp_path, None, lignes, avec_catalogue=False)
    assert "DELETE FROM" not in sql and "INSERT OR IGNORE INTO qualifications" in sql


def test_amendement_unanime_ou_article_unique_refuse():
    infos = {"D": {"dossier_id": "DLR5L17N1", "etape": "AN1", "division": None, "objet": "ensemble", "pour": 10, "contre": 5},
             "U": {"dossier_id": "DLR5L17N1", "etape": "AN1", "division": "Article 2", "objet": "amendement", "pour": 0, "contre": 46},
             "S": {"dossier_id": "DLR5L17N1", "etape": "AN1", "division": None, "objet": "suppression_article_unique",
                   "pour": 65, "contre": 95}}
    sc = [{"id": "D", "role": "decisif", "pour": "texte"}, {"id": "U", "role": "amendement", "pour": "texte"},
          {"id": "S", "role": "amendement", "pour": "contre-texte"}]
    err, _ = editorial.valider(_texte(scrutins=sc), infos)
    assert "U : amendement unanime (0-46), pas un amendement clé (règle 11)" in err
    assert "S : suppression d'un article unique, pas un amendement clé (règle 11)" in err
    assert not any(e.startswith("D : décisif unanime") for e in err)


def test_decisif_unanime_refuse():
    infos = {"D": {"dossier_id": "DLR5L17N1", "etape": "AN1", "division": None, "objet": "ensemble", "pour": 503, "contre": 0}}
    err, _ = editorial.valider(_texte(scrutins=[{"id": "D", "role": "decisif", "pour": "texte"}]), infos)
    assert "D : décisif unanime (503-0), texte à écarter (règle 9)" in err


def test_termes_interdits(tmp_path):
    from lvnd import check
    liste = tmp_path / "t.txt"
    liste.write_text("# commentaire\nABC\nAssociation Exemple\n")
    assert check.termes_interdits("Source : abc, avis", liste) == ["ABC"]
    assert check.termes_interdits("ABCD et xabc ne comptent pas", liste) == []
    assert check.termes_interdits("l'association exemple a dit", liste) == ["Association Exemple"]
    assert check.termes_interdits("rien", tmp_path / "absent.txt") == []


def test_validations(tmp_path):
    t = _texte()
    (tmp_path / "a.yaml").write_text(yaml.safe_dump({**t, "statut": "a-relire"}, allow_unicode=True))
    (tmp_path / "b.yaml").write_text(yaml.safe_dump({"id": "", "dossier_an": "DLR5L17N2", "legislature": 17,
                                                      "titre": "T", "statut": "ecarte", "motif_ecart": "m"}))
    sql = sync_admin.validations(tmp_path, "validé par Max")
    assert len(sql) == 4 and "ON CONFLICT (dossier_an) DO UPDATE" in sql[0]
    assert "'valide'" in sql[0] and "'ecarte'" in sql[2] and "'validé par Max'" in sql[3]
    (tmp_path / "c.yaml").write_text(yaml.safe_dump({**t, "dossier_an": "X", "droits": []}))
    with pytest.raises(SystemExit, match="droit principal"):
        sync_admin.validations(tmp_path, "x")
