import csv

from lvnd import editorial, recherche

DOC = {"textes": [{"id": "t1", "dossier_an": "D1", "recherche": {"termes": ["49.3", "APL"], "surnoms": ["loi X"]}},
                  {"id": "t2", "dossier_an": "D2"}],
       "ecartes": [{"dossier_an": "D3", "recherche": {"termes": ["Y"]}}],
       "suivis": [{"id": "s1", "dossier_an": "D4", "recherche": {"termes": ["a", "A"]}}]}


def test_les_termes_viennent_d_editorial():
    assert recherche.lignes_termes(DOC) == [
        {"cle": "t1", "type": "terme", "terme": "49.3"},
        {"cle": "t1", "type": "terme", "terme": "APL"},
        {"cle": "t1", "type": "surnom", "terme": "loi X"},
        {"cle": "s1", "type": "terme", "terme": "a"},
        {"cle": "s1", "type": "terme", "terme": "A"},
        {"cle": "D3", "type": "terme", "terme": "Y"},
    ]


def test_doublon_refuse_texte_sans_terme_signale():
    err, sans = recherche.controler_termes(DOC)
    assert err == ["s1 : terme en double"]
    assert sans == ["t2"]


def test_les_termes_publies_sont_coherents():
    err, _ = recherche.controler_termes(editorial.charger())
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

