"""`lvnd resumer` : résumés en mots simples (cycle Facile à lire), avec un faux client et une fausse D1."""

import json
from types import SimpleNamespace as NS

from lvnd import editorial, llm, resumer
from test_llm import EN_SERVICE, FausseD1, FauxClient, termes, usage  # noqa: F401 (fixture)

FICHE = editorial.normaliser({
    "id": "essai-2026", "dossier_an": "DLR5L17N1", "legislature": 17, "titre": "Loi sur les caméras",
    "resume": "Le texte autorise les caméras dans 12 villes pendant 2 ans.",
    "droits": [{"code": "libertes", "role": "secondaire", "sens": "restreint", "sources": ["s1"]},
               {"code": "vie-privee", "role": "principal", "sens": "restreint", "sources": ["s1"]}],
    "sources": {"s1": {"auteur": "CNIL", "titre": "Avis", "date": "2024-01-01", "url": "https://cnil.fr"}},
    "scrutins": [{"id": "V1", "role": "decisif", "pour": "texte", "objet": "x"}]})
NOMS = resumer.Noms(elus=["Alain David"], groupes=["Les Républicains"], sigles=["RN"])


def test_message_sans_sens_ni_source():
    m = resumer.message(FICHE)
    assert "Vie privée et surveillance (le principal)" in m.splitlines()[5]  # le principal d'abord
    assert "restreint" not in m and "CNIL" not in m and "V1" not in m
    assert "Pas de décision du Conseil constitutionnel." in m


def test_controles(termes):
    c = resumer.controler("Ce texte met des caméras dans 12 villes.\nC'est pour 3 ans.", FICHE, NOMS)
    assert c["erreurs"] == [] and c["avertissements"] == ["nombre absent de la fiche : 3"]
    c = resumer.controler("Alain David et le RN parlent de l'Organisation Exclue.", FICHE, NOMS)
    assert c["erreurs"] == ["1 terme(s) de la liste d'exclusion", "nomme un·e élu·e ou un groupe : Alain David, RN"]
    assert "résumé simple : sigle à expliquer ou à éviter : RN" in c["avertissements"]
    assert resumer.controler("  \n ", FICHE, NOMS)["erreurs"] == ["résumé simple vide"]


def test_a_resumer_saute_les_textes_a_jour_ou_deja_proposes():
    e = editorial.empreinte_simple(FICHE)
    ligne = lambda doc, statut="valide": {"dossier_an": doc["dossier_an"], "statut": statut,  # noqa: E731
                                          "doc": json.dumps(doc, ensure_ascii=False)}
    a_jour = {**FICHE, "dossier_an": "DLR5L17N2", "resume_simple": {"texte": "Une phrase.", "empreinte":
              editorial.empreinte_simple({**FICHE, "dossier_an": "DLR5L17N2"})}}
    perime = {**FICHE, "dossier_an": "DLR5L17N3", "resume_simple": {"texte": "Une phrase.", "empreinte": "0" * 16}}
    qualifs = [ligne(FICHE), ligne(a_jour), ligne(perime), ligne({**FICHE, "dossier_an": "DLR5L17N4"}, "a-relire")]
    assert [t["dossier_an"] for t in resumer.a_resumer(qualifs, set())] == ["DLR5L17N1", "DLR5L17N3"]
    assert [t["dossier_an"] for t in resumer.a_resumer(qualifs, {f"simple:DLR5L17N1:{e}"})] == ["DLR5L17N3"]
    assert [t["dossier_an"] for t in resumer.a_resumer(qualifs, set(), ["DLR5L17N3"])] == ["DLR5L17N3"]


def test_proposition_puis_ligne_d1(termes):
    texte = NS(type="text", text="<resume_simple>\nCe texte met des caméras dans 12 villes.\n</resume_simple>\n"
                                 "<remarque>Le mot « caméra » suffit.</remarque>")
    client = FauxClient([NS(stop_reason="end_turn", content=[texte], usage=usage())])
    s = llm.Session(FausseD1(EN_SERVICE), "resume-simple", client=client, secret="s")
    p = resumer.proposer(s, FICHE)
    assert p.texte == "Ce texte met des caméras dans 12 villes." and p.remarque == "Le mot « caméra » suffit."
    assert "tools" not in client.recus[0] and client.recus[0]["output_config"] == {"effort": "low"}
    c = resumer.controler(p.texte, FICHE, NOMS)
    ld = resumer.ligne_d1(p, FICHE, c, s.modele, "2026-11-02T10:00:00+00:00")
    assert ld["alerte_id"] == f"simple:DLR5L17N1:{editorial.empreinte_simple(FICHE)}" and ld["statut"] == "proposee"
    assert json.loads(ld["doc"]) == {"dossier_an": "DLR5L17N1", "resume_simple": {
        "texte": p.texte, "empreinte": editorial.empreinte_simple(FICHE)}}
    assert json.loads(ld["relecture"])["action"] == "Le mot « caméra » suffit."
    # une erreur de contrôle met la proposition en échec, sans la perdre
    ld = resumer.ligne_d1(p, FICHE, {"erreurs": ["x"], "avertissements": [], "points": []}, s.modele, "d")
    assert ld["statut"] == "echec" and ld["doc"]


def test_sans_balise_en_echec(termes):
    client = FauxClient([NS(stop_reason="end_turn", content=[NS(type="text", text="Voici.")], usage=usage())])
    s = llm.Session(FausseD1(EN_SERVICE), "resume-simple", client=client, secret="s")
    p = resumer.proposer(s, FICHE)
    assert p.echec == "aucune balise <resume_simple> dans la réponse"
    assert resumer.ligne_d1(p, FICHE, None, s.modele, "d")["statut"] == "echec"


def test_systeme_reprend_les_regles_d_ecriture():
    assert f"{editorial.SIMPLE_MOTS} mots au plus" in resumer.SYSTEME
    assert "{" not in resumer.SYSTEME
