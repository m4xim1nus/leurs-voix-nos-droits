from lvnd.textes import Index, rattacher


def dossier(uid: str, titre: str, votes: list[str] = (), seance: str | None = None, engagement: bool = False) -> dict:
    actes = [{"codeActe": "AN1-DEC", "uid": f"{uid}-DEC", "voteRefs": {"voteRef": list(votes)}}]
    if seance:
        actes.append({"codeActe": "AN1-DEBATS-SEANCE", "uid": f"{uid}-S", "reunionRef": seance, "dateActe": "2020-01-01"})
    return {"uid": uid, "titreDossier": {"titre": titre}, "procedureParlementaire": {"code": "13" if engagement else "1"},
            "actesLegislatifs": {"acteLegislatif": [{"codeActe": "AN1", "uid": f"{uid}-AN1",
                                                     "actesLegislatifs": {"acteLegislatif": actes}}]}}


def scrutin(titre: str, seance: str = "S1", id_: str = "V1") -> dict:
    return {"id": id_, "titre": titre, "objet": "amendement", "seance": seance, "date": "2020-01-01", "dossier_objet": None}


def test_motion_citee_deux_fois_va_a_l_engagement_quel_que_soit_l_ordre():
    texte, engagement = dossier("A", "retraites", ["V1"]), dossier("Z", "engagement", ["V1"], engagement=True)
    assert Index({"A": texte, "Z": engagement}).vote_refs["V1"] == "Z"
    assert Index({"Z": engagement, "A": texte}).vote_refs["V1"] == "Z"


DOSSIERS = {"BON": dossier("BON", "relatif à la restauration de la cathédrale", seance="S1"),
            "AUTRE": dossier("AUTRE", "création du centre national de la musique")}


def test_amendement_d_un_autre_texte_refuse():
    s = scrutin("l'amendement n° 12 de Mme Kuster au projet de loi relatif à la restauration de la cathédrale")
    lien = rattacher([s], DOSSIERS, {}, {"V1": {"amendement_id": "X", "dossier_id": "AUTRE"}})["V1"]
    assert (lien["dossier_id"], lien["rattachement"], lien["amendement_refuse"]) == ("BON", "seance", True)


def test_amendement_du_bon_texte_garde():
    s = scrutin("l'amendement n° 12 de Mme Kuster au projet de loi relatif à la restauration de la cathédrale")
    lien = rattacher([s], DOSSIERS, {}, {"V1": {"amendement_id": "X", "dossier_id": "BON"}})["V1"]
    assert (lien["dossier_id"], lien["rattachement"], lien["amendement_refuse"]) == ("BON", "amendement", False)


def test_titre_muet_garde_l_amendement():
    s = scrutin("l'amendement n° 12 de Mme Kuster à l'article 3")
    lien = rattacher([s], DOSSIERS, {}, {"V1": {"amendement_id": "X", "dossier_id": "AUTRE"}})["V1"]
    assert (lien["dossier_id"], lien["amendement_refuse"]) == ("AUTRE", False)
