import csv

from lvnd import editorial, recherche

DOC = {"textes": [{"id": "t1"}, {"id": "t2"}], "ecartes": [{"dossier_an": "D1"}], "suivis": [{"id": "s1"}]}


def test_les_termes_sont_du_texte():
    ref = {"textes": {"t1": {"termes": [49.3, "APL"], "surnoms": ["loi X"]}}, "ecartes": {"D1": {"termes": ["Y"]}}}
    assert recherche.lignes_termes(ref) == [
        {"cle": "t1", "type": "terme", "terme": "49.3"},
        {"cle": "t1", "type": "terme", "terme": "APL"},
        {"cle": "t1", "type": "surnom", "terme": "loi X"},
        {"cle": "D1", "type": "terme", "terme": "Y"},
    ]


def test_terme_vide_ou_en_double_refuses_cle_inconnue_signalee():
    ref = {"textes": {"t1": {"termes": ["a", "A"]}, "absent": {"termes": ["b"]}, "s1": {"termes": []}},
           "ecartes": {"D2": {"termes": ["c"]}}}
    err, a_deplacer, sans = recherche.controler_termes(DOC, ref)
    assert any("s1 : terme vide" in e for e in err)
    assert any("t1 : terme en double" in e for e in err)
    assert not any("inconnu" in e for e in err)  # une publication ne bloque plus la passe (01/11/2026)
    assert any(a.startswith("absent : inconnu") for a in a_deplacer)
    assert any(a.startswith("D2 : inconnu") for a in a_deplacer)
    assert sans == ["t2"]


def test_un_ecarte_devenu_qualifie_garde_ses_termes():
    doc = {"textes": [{"id": "t1", "dossier_an": "D1"}], "ecartes": [], "suivis": []}
    ref = {"textes": {}, "ecartes": {"D1": {"termes": ["x"]}}}
    assert recherche.lignes_termes(ref, doc) == [{"cle": "t1", "type": "terme", "terme": "x"}]
    assert recherche.lignes_termes(ref) == [{"cle": "D1", "type": "terme", "terme": "x"}]
    err, a_deplacer, sans = recherche.controler_termes(doc, ref)
    assert err == [] and sans == []
    assert a_deplacer == ["D1 : qualifié ou suivi sous `t1`, ligne à déplacer dans `textes` (ses termes le suivent déjà)"]


def test_le_referentiel_des_termes_est_coherent_avec_editorial():
    # clés à déplacer et textes sans terme, qu'une publication de l'admin peut créer, sont signalés par `lvnd check`,
    # sans rougir les tests
    err, _, _ = recherche.controler_termes(editorial.charger())
    assert err == []


def test_table_des_pays_complete():
    assert recherche.controler_pays() == []
    lignes = recherche.lignes_pays()
    par_pays = {l["pays"]: l for l in lignes}
    assert len({l["circo"] for l in lignes}) == recherche.CIRCONSCRIPTIONS
    assert par_pays["Allemagne"]["circo"] == "099-07"
    assert par_pays["États-Unis"]["circo"] == "099-01"
    assert par_pays["Royaume-Uni"]["alias"].startswith("Angleterre")
    assert par_pays["Australie"]["circo"] == "099-11"
    assert par_pays["Israël"]["circo"] == "099-08" and par_pays["Israël"]["hors_tableau"] == ""
    hors = {l["pays"] for l in lignes if l["hors_tableau"]}
    assert hors == {"Kosovo", "Monténégro", "Serbie", "Soudan du Sud", "Territoires palestiniens", "Taïwan"}


def test_pays_doublon_ou_alias_orphelin_refuses():
    base = {n: [] for n in range(1, 12)}
    ref = {"circonscriptions": {**base, 1: ["A", "B"], 2: ["A"]}, "hors_tableau": {}, "alias": {"Z": ["W"]}}
    err = recherche.controler_pays(ref)
    assert any("en double : A" in e for e in err)
    assert any("alias d'un pays inconnu : Z" in e for e in err)


def test_ecriture_des_csv(tmp_path):
    recherche.ecrire(tmp_path)
    with (tmp_path / "pays_circonscriptions.csv").open() as f:
        assert list(csv.DictReader(f))[0].keys() == set(recherche.COLONNES_PAYS)
    with (tmp_path / "termes_recherche.csv").open() as f:
        termes = list(csv.DictReader(f))
    assert {"cle": "duplomb-2025", "type": "surnom", "terme": "loi Duplomb"} in termes
    assert {"cle": "kasbarian-berge", "type": "terme", "terme": "squat"} in termes
