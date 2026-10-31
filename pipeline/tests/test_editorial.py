import copy
import pytest
import yaml
import json
import sqlite3
from pathlib import Path

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
        assert list(t) == [k for k in editorial.CLES_TEXTE if k != "senat"]
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
    assert "il faut exactement un scrutin décisif (ou, pour un texte adopté par 49.3 sans vote final, au moins une motion de censure)" in err
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


FIXTURE = Path(__file__).parent / "fixtures/editorial_suivis.json"
FIXTURE_SENAT = Path(__file__).parent / "fixtures/editorial_senat.json"


def test_senat_a_l_octet_et_controles():
    """Même fixture que admin/src/lib/qualification.test.ts : mêmes octets, mêmes messages."""
    f = json.loads(FIXTURE_SENAT.read_text())
    assert editorial.serialiser(editorial.document([editorial.normaliser(t) for t in f["entrees"]], [])) == f["sortie"]
    for c in f["cas"]:
        doc = editorial.normaliser(c["doc"])
        assert editorial.valider(doc, c.get("infos"), c.get("infos_senat")) == (c["erreurs"], c["avertissements"]), c["nom"]


def test_senat_absent_quand_vide():
    assert "senat" not in _texte()
    assert "senat" not in _texte(senat={"version": "meme", "scrutins": [], "note": ""})
    t = _texte(senat={"version": "meme", "scrutins": [{"id": "SN1", "role": "decisif", "pour": "texte", "objet": "x"}]})
    assert list(t["senat"]) == list(editorial.CLES_SENAT)


def test_complement_ne_touche_que_le_senat(tmp_path, monkeypatch):
    base = _texte()
    monkeypatch.setattr(editorial, "charger", lambda: {"textes": [base], "ecartes": []})
    (tmp_path / "t.yaml").write_text(yaml.safe_dump({"id": "t", "dossier_an": "DLR5L17N1", "senat": {
        "version": "meme", "scrutins": [{"id": "SN1", "role": "decisif", "pour": "texte", "objet": "x (2-1)"}]}}))
    sql = sync_admin.validations(tmp_path, "validé")
    assert "json_set(doc, '$.senat'" in sql[0] and "UPDATE qualifications" in sql[0]
    con = sqlite3.connect(":memory:")
    con.executescript("create table qualifications (dossier_an, statut, doc, motif_ecart, modifie_par, modifie_le);"
                      "create table revisions (dossier_an, statut, doc, motif_ecart, auteur, date, commentaire);")
    con.execute("insert into qualifications values (?, 'valide', ?, null, 'x', 'y')", ("DLR5L17N1", sync_admin.compact(base)))
    con.executescript("\n".join(sql))
    doc, = con.execute("select doc from qualifications").fetchone()
    assert doc == sync_admin.compact(editorial.normaliser({**base, "senat": {
        "version": "meme", "scrutins": [{"id": "SN1", "role": "decisif", "pour": "texte", "objet": "x (2-1)"}]}}))
    assert con.execute("select count(*), max(commentaire) from revisions").fetchone() == (1, "validé")
    # un texte non publié ne se complète pas
    (tmp_path / "t.yaml").write_text(yaml.safe_dump({"id": "autre", "dossier_an": "DLR5L17N9", "senat": {"version": "meme"}}))
    with pytest.raises(SystemExit):
        sync_admin.validations(tmp_path, "validé")


def test_ecarte_sans_senat(tmp_path, monkeypatch):
    monkeypatch.setattr(editorial, "charger", lambda: {"textes": [], "ecartes": []})
    (tmp_path / "e.yaml").write_text(yaml.safe_dump({"id": "", "dossier_an": "DLR5L17N2", "legislature": 17, "titre": "Loi",
                                                     "statut": "ecarte", "motif_ecart": "règle 8", "senat": {
        "version": "seul", "scrutins": [{"id": "SN1", "role": "ensemble", "pour": "texte", "objet": "x"}]}}))
    sql = "\n".join(sync_admin.validations(tmp_path, "validé"))
    assert "'ecarte'" in sql and "senat" not in sql


def test_suivis_a_l_octet():
    """Même fixture que admin/src/lib/qualification.test.ts : les deux écrivent les mêmes octets."""
    brut = FIXTURE.read_text()
    doc = json.loads(brut)
    # Une fiche stockée dans D1 (document complet, clés dans le désordre) redonne la même entrée.
    d1 = [editorial.doc_suivi(s) for s in reversed(doc["suivis"])]
    assert all(s["scrutins"] == [] and s["etiquettes"] == [] for s in d1)
    assert editorial.serialiser(editorial.document(doc["textes"], doc["ecartes"], d1)) == brut


def test_sans_suivi_la_cle_n_apparait_pas():
    doc = json.loads(FIXTURE.read_text())
    assert "suivis" not in editorial.document(doc["textes"], doc["ecartes"])
    assert "suivis" not in editorial.document(doc["textes"], doc["ecartes"], [])


def test_valider_suivi():
    doc = json.loads(FIXTURE.read_text())
    s = doc["suivis"][0]
    assert editorial.valider_suivi(s) == ([], [])
    assert editorial.valider_suivi(editorial.doc_suivi(s)) == ([], [])
    assert "il faut au moins un droit touché" in editorial.valider_suivi({**s, "droits": []})[0]
    sens = {**s, "droits": [{"code": "etrangers", "sens": "etend", "sources": ["s2"]}]}
    assert editorial.valider_suivi(sens)[0] == ["etrangers : ni sens ni rôle avant le vote"]
    sans = {**s, "droits": [{"code": "etrangers", "sources": []}]}
    assert "etrangers : aucune source" in editorial.valider_suivi(sans)[0]
    assert "droit inconnu : x" in editorial.valider_suivi({**s, "droits": [{"code": "x", "sources": ["s1"]}]})[0]
    assert editorial.valider_suivi({**s, "scrutins": [{"id": "V"}]})[0] == ["aucun scrutin retenu avant le vote"]
    assert "source s1 définie mais citée nulle part" in editorial.valider_suivi(
        {**s, "droits": [{"code": "etrangers", "sources": ["s2"]}]})[1]
    assert "source citée mais non définie : s2" in editorial.valider_suivi({**s, "sources": {}})[0]


def test_amorcage_et_validation_des_suivis(tmp_path):
    doc = json.loads(FIXTURE.read_text())
    lignes = {l["dossier_an"]: l for l in sync_admin.qualifications(doc)}
    l = lignes["DLR5L17N3"]
    assert l["statut"] == "a-suivre" and l["publie_empreinte"] == sync_admin.empreinte(l["doc"], "a-suivre", None)
    assert '"role"' not in l["doc"] and '"sens"' not in l["doc"]
    (tmp_path / "s.yaml").write_text(yaml.safe_dump({**doc["suivis"][0], "statut": "a-suivre"}, allow_unicode=True))
    assert sync_admin.brouillons(tmp_path)[0]["statut"] == "a-relire"
    sql = "\n".join(sync_admin.validations(tmp_path, "validé par Max"))
    assert "'a-suivre'" in sql
    (tmp_path / "s.yaml").write_text(yaml.safe_dump({**doc["suivis"][0], "statut": "a-suivre", "scrutins": [{"id": "V"}]}))
    with pytest.raises(SystemExit, match="aucun scrutin"):
        sync_admin.validations(tmp_path, "x")


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


def _base_d1() -> sqlite3.Connection:
    base = sqlite3.connect(":memory:")
    base.executescript((Path(__file__).resolve().parents[2] / "admin/migrations/0001_init.sql").read_text())
    return base


def test_brouillon_recoit_sa_revision_meme_si_le_texte_en_a_deja_une(tmp_path):
    (tmp_path / "a.yaml").write_text(
        "id: essai\ndossier_an: DLR5L17N1\nlegislature: 17\ntitre: Loi\nstatut: a-relire\n"
        "droits: []\nscrutins: []\n")
    (tmp_path / "b.yaml").write_text(
        "id: autre\ndossier_an: DLR5L17N2\nlegislature: 17\ntitre: Loi 2\nstatut: a-relire\n"
        "droits: []\nscrutins: []\n")
    base = _base_d1()
    # DLR5L17N1 : brouillon retiré d'un lot précédent (sa révision reste). DLR5L17N2 : déjà en cours, intact.
    base.execute("INSERT INTO revisions (dossier_an, statut, doc, auteur, date) "
                 f"VALUES ('DLR5L17N1', 'a-relire', '{{}}', '{sync_admin.AUTEUR_BROUILLONS}', '2026-01-01')")
    base.execute("INSERT INTO qualifications (dossier_an, statut, doc, modifie_par, modifie_le) "
                 f"VALUES ('DLR5L17N2', 'brouillon', '{{}}', '{sync_admin.AUTEUR_BROUILLONS}', '2026-01-01')")
    sql = sync_admin.script(tmp_path, None, sync_admin.brouillons(tmp_path), avec_catalogue=False)
    base.executescript(sql)
    base.executescript(sql)  # un même script rejoué n'ajoute rien
    revisions = base.execute("SELECT dossier_an, date FROM revisions ORDER BY dossier_an, date").fetchall()
    assert [r[0] for r in revisions] == ["DLR5L17N1", "DLR5L17N1"]
    assert revisions[0][1] == "2026-01-01"
    assert base.execute("SELECT statut FROM qualifications WHERE dossier_an = 'DLR5L17N2'").fetchone() == ("brouillon",)


def test_remplacements_repassent_a_relire(tmp_path):
    (tmp_path / "a.yaml").write_text(
        "id: essai\ndossier_an: DLR5L17N1\nlegislature: 17\ntitre: Loi\nstatut: a-relire\n"
        "droits: []\nscrutins: []\n")
    sql = sync_admin.remplacements(sync_admin.brouillons(tmp_path), "requalification, lot 5")
    assert len(sql) == 2 and "ON CONFLICT (dossier_an) DO UPDATE" in sql[0] and "'a-relire'" in sql[0]
    assert "publie_empreinte" not in sql[0] and "'requalification, lot 5'" in sql[1]


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


def test_validation_refuse_d_ecarter_un_texte_publie(tmp_path, monkeypatch):
    monkeypatch.setattr(editorial, "charger", lambda: {"textes": [{"id": "pub", "dossier_an": "DLR5L17N2"}]})
    (tmp_path / "b.yaml").write_text(yaml.safe_dump({"id": "", "dossier_an": "DLR5L17N2", "legislature": 17,
                                                      "titre": "T", "statut": "ecarte", "motif_ecart": "m"}))
    with pytest.raises(SystemExit, match="publié comme qualifié"):
        sync_admin.validations(tmp_path, "x")
    assert "'ecarte'" in sync_admin.validations(tmp_path, "x", ecarter_publie=True)[0]


def test_texte_adopte_par_49_3():
    # Pas de décisif, mais des motions de censure : valide (règle 9), même hors du dossier.
    censure = [{"id": "C", "role": "censure", "pour": "contre-texte", "objet": "motion de censure"}]
    assert editorial.valider(_texte(scrutins=censure))[0] == []
    infos = {"C": {"dossier_id": None, "objet": "motion_censure"}, "X": {"dossier_id": "DLR5L17N1", "objet": "ensemble"}}
    assert editorial.valider(_texte(scrutins=censure), infos)[0] == []
    autre = [{"id": "X", "role": "censure", "pour": "contre-texte"}]
    assert editorial.valider(_texte(scrutins=autre), infos)[0] == ["X : pas une motion de censure"]
    err, _ = editorial.valider(_texte(scrutins=[{"id": "A", "role": "amendement", "pour": "texte"}]))
    assert "il faut exactement un scrutin décisif (ou, pour un texte adopté par 49.3 sans vote final, au moins une motion de censure)" in err


def test_sync_incremental_n_ecrit_que_les_differences():
    cat = {"textes": [{"id": "T1", "legislature": 17, "titre": "A"}, {"id": "T2", "legislature": 17, "titre": "B"}],
           "scrutins": [], "groupes": [], "alertes": [], "senat_scrutins": [], "senat_groupes": [],
           "catalogue_meta": [{"cle": "grille", "valeur": "{}"}, {"cle": "sync", "valeur": '"2026"'}]}
    cols = sync_admin.COLONNES_TEXTES
    present = {"textes": {"T1": sync_admin._ligne({"id": "T1", "legislature": 17.0, "titre": "A"}, cols),
                          "T3": "x"},
               "catalogue_meta": {"grille": sync_admin._ligne({"cle": "grille", "valeur": "{}"}, ("cle", "valeur"))}}
    sql, compte = sync_admin.difference(cat, present)
    assert compte["textes"] == {"ecrites": 1, "effacees": 1}  # T2 ajouté, T3 effacé, T1 inchangé
    assert compte["catalogue_meta"] == {"ecrites": 0, "effacees": 0}
    assert "DELETE FROM textes WHERE id IN ('T3');" in sql
    assert any("INSERT OR REPLACE INTO textes" in i and "'T2'" in i and "'T1'" not in i for i in sql)
    assert any("'sync'" in i for i in sql)  # date du sync toujours écrite


def test_sync_alerte_scrutin_retenu_disparu_ou_deplace():
    cat = {"scrutins": [{"id": "V1", "texte_id": "D1"}, {"id": "V2", "texte_id": "D2"}, {"id": "C", "texte_id": ""}]}
    doc = json.dumps({"scrutins": [{"id": "V1", "role": "decisif"}, {"id": "V2", "role": "amendement"},
                                   {"id": "V3", "role": "amendement"}, {"id": "C", "role": "censure"}]})
    assert sync_admin.alertes(cat, [("D1", doc)]) == [
        "D1 : scrutin retenu V2 rattaché désormais à D2",
        "D1 : scrutin retenu V3 absent du nouveau catalogue",
    ]
