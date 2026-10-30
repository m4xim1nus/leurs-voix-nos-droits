"""Où en est chaque texte : règle de périmètre, prochaine étape, état, décisions du Sénat lues dans Dosleg."""

import sqlite3

import pytest

from lvnd import encours, parcours, textes

REF = "2026-10-28"


def lecture(etape, chambre, type_lecture, rang, date=None, statut=None, typlec="1"):
    """Lecture au format de `parcours.lectures_dossier` ; `statut` : code TSORTF… (None = pas de décision)."""
    dec = {"codeActe": f"{etape}-DEBATS-DEC", "dateActe": date, "statutConclusion": {"fam_code": statut}} if statut else None
    return {"dossier": "DLRTEST", "etape": etape, "chambre": chambre, "type_lecture": type_lecture, "typlec": typlec,
            "rang": rang, "ordre_brut": rang, "dec": dec, "date": date or ""}


ADOPTE, MODIFIE, REJETE = "TSORTF01", "TSORTF05", "TSORTF07"


def test_seuil_inactivite():
    assert encours.seuil_inactivite("2026-10-28") == "2025-10-28"
    assert encours.seuil_inactivite("2026-10-28", 6) == "2026-04-28"
    assert encours.seuil_inactivite("2024-02-29") == "2023-02-28"


# --- Règle de périmètre ---------------------------------------------------------

def test_voté_transmis_en_cours():
    ls = [lecture("AN1", "AN", "premiere", 0, "2026-07-07", ADOPTE), lecture("SN1", "SN", "premiere", 1)]
    assert encours.motif_ecart(ls, [], "ordinaire", "en_cours", "2026-07-07", REF) is None


def test_inactif_au_dela_de_douze_mois():
    ls = [lecture("AN1", "AN", "premiere", 0, "2025-02-20", ADOPTE),
          lecture("SN1", "SN", "premiere", 1, "2025-06-12", REJETE), lecture("AN2", "AN", "deuxieme", 2)]
    assert encours.motif_ecart(ls, [], "ordinaire", "en_cours", "2025-06-12", REF) == "inactif"
    # une séance inscrite à l'ordre du jour compte comme activité
    assert encours.motif_ecart(ls, [], "ordinaire", "en_cours", "2026-11-19", REF) is None
    # la limite est incluse
    assert encours.motif_ecart(ls, [], "ordinaire", "en_cours", "2025-10-28", REF) is None


def test_rejet_par_la_premiere_assemblee():
    ls = [lecture("AN1", "AN", "premiere", 0, "2026-10-01", REJETE)]
    assert encours.motif_ecart(ls, [], "ordinaire", None, "2026-10-01", REF) == "rejete"
    # loi de financement : transmise au Sénat malgré le rejet (PLFSS 2027)
    assert encours.motif_ecart(ls, [], "financement_ss", None, "2026-10-23", REF) is None
    # rejet suivi d'une autre lecture : le texte a été transmis (comptes de la Sécurité sociale)
    ls2 = ls + [lecture("SN1", "SN", "premiere", 1, "2026-10-10", MODIFIE)]
    assert encours.motif_ecart(ls2, [], "ordinaire", "en_cours", "2026-10-10", REF) is None


def test_rejet_par_la_seconde_assemblee_ne_clot_pas():
    ls = [lecture("AN1", "AN", "premiere", 0, "2026-06-23", ADOPTE),
          lecture("SN1", "SN", "premiere", 1, "2026-10-26", REJETE)]
    assert encours.motif_ecart(ls, [], "constitutionnelle", "en_cours", "2026-10-26", REF) is None


def test_etats_dosleg_et_retrait():
    ls = [lecture("SN1", "SN", "premiere", 0, "2026-10-01", ADOPTE)]
    for etat in ("rejete", "caduc", "fusionne", "retire"):
        assert encours.motif_ecart(ls, [], "ordinaire", etat, "2026-10-01", REF) == etat
    assert encours.motif_ecart(ls, [{"type": "retrait"}], "ordinaire", "en_cours", "2026-10-01", REF) == "retire"


def test_motif_sans_lecture():
    """Résolution ou texte retiré sans lecture : la règle ne plante pas."""
    assert encours.motif_ecart([], [], "ordinaire", None, "2026-10-01", REF) is None
    assert encours.motif_ecart([], [{"type": "retrait"}], "ordinaire", None, "2026-10-01", REF) == "retire"
    assert encours.motif_ecart([], [], "ordinaire", None, "", REF) == "inactif"


# --- Prochaine étape -------------------------------------------------------------

def test_attente_etape_ouverte():
    ls = [lecture("AN1", "AN", "premiere", 0, "2026-07-07", ADOPTE), lecture("SN1", "SN", "premiere", 1)]
    assert encours.attente(ls, []) == {"attente": "lecture", "etape": "SN1", "chambre": "SN", "type_lecture": "premiere"}


def test_attente_transmis_sans_etape_ouverte():
    ls = [lecture("SN1", "SN", "premiere", 0, "2026-10-27", ADOPTE)]
    assert encours.attente(ls, [])["attente"] == "transmis"
    assert encours.attente(ls, [])["chambre"] == "AN"
    # texte financier rejeté en première lecture à l'AN : transmis au Sénat
    ls = [lecture("AN1", "AN", "premiere", 0, "2026-10-23", REJETE)]
    assert encours.attente(ls, [], "financement_ss")["chambre"] == "SN"
    # rejet par la seconde assemblée : la suite n'est pas enregistrée
    ls = [lecture("AN1", "AN", "premiere", 0, "2026-06-23", ADOPTE),
          lecture("SN1", "SN", "premiere", 1, "2026-10-26", REJETE)]
    assert encours.attente(ls, [])["attente"] == "navette"


def test_attente_cmp():
    ls = [lecture("AN1", "AN", "premiere", 0, "2026-03-01", ADOPTE),
          lecture("SN1", "SN", "premiere", 1, "2026-05-01", MODIFIE)]
    convoquee = [{"type": "cmp_convoquee", "date": "2026-05-10"}]
    assert encours.attente(ls, convoquee)["attente"] == "cmp"
    accord = convoquee + [{"type": "cmp_accord", "date": "2026-05-20"}]
    assert encours.attente(ls, accord)["attente"] == "cmp_conclusions"
    desaccord = convoquee + [{"type": "cmp_desaccord", "date": "2026-05-20"}]
    assert encours.attente(ls, desaccord)["attente"] == "navette"
    # conclusions lues à l'AN, le Sénat reste
    ls3 = ls + [lecture("CMP", "AN", "cmp", 2, "2026-06-01", "TSORTF18", "4")]
    r = encours.attente(ls3, accord)
    assert (r["attente"], r["chambre"]) == ("cmp_conclusions", "SN")


# --- État ------------------------------------------------------------------------

def test_etat():
    vote = [lecture("AN1", "AN", "premiere", 0, "2026-07-07", ADOPTE)]
    depot = [lecture("AN1", "AN", "premiere", 0)]
    assert encours.etat("promulguee", vote, None) == "loi"
    assert encours.etat("adoptee", vote, None) == "adopte"
    assert encours.etat("autre", vote, None) == "en_navette"
    assert encours.etat("autre", depot, None) == "avant_vote"
    assert encours.etat("autre", [], None) == "hors_navette"
    assert encours.etat("autre", vote, "inactif") == "a_l_arret"
    assert encours.etat("autre", vote, "rejete") == "rejete"


# --- Décisions du Sénat absentes du dossier AN ---------------------------------------

def test_completer_senat_par_scrutin():
    idx = parcours.Index([], [{"id": "SN2026-41", "date": "2026-10-27", "numero": 41, "objet": "ensemble",
                               "sort": "adopte", "loicod": "85760", "typleccod": "1"}])
    ls = [lecture("SN1", "SN", "premiere", 0)]
    encours.completer_senat(ls, "85760", {}, idx)
    assert ls[0]["date"] == "2026-10-27" and ls[0]["decision_dosleg"]
    assert parcours._statut(ls[0]["dec"])["issue"] == "adopte"


def test_completer_senat_par_texte_puis_question_prealable():
    idx = parcours.Index([], [{"id": "SN1", "date": "2026-03-02", "numero": 3, "objet": "motion_rejet",
                               "sort": "adopte", "loicod": "1", "typleccod": "1"}])
    ls = [lecture("SN1", "SN", "premiere", 0)]
    encours.completer_senat(ls, "1", {}, idx)
    assert parcours._statut(ls[0]["dec"])["issue"] == "rejete"
    # le texte adopté (Dosleg) prime sur les scrutins
    ls = [lecture("SN1", "SN", "premiere", 0)]
    encours.completer_senat(ls, "1", {("1", "1"): ("2026-03-05", "adopte")}, idx)
    assert (ls[0]["date"], parcours._statut(ls[0]["dec"])["issue"]) == ("2026-03-05", "adopte")


# --- Catalogue élargi ------------------------------------------------------------------

def test_catalogue_sans_scrutin():
    d = {"legislature": "17", "titreDossier": {"titre": "Texte", "titreChemin": "t"}}
    rows = textes.catalogue({"D1": d, "D2": d}, [], {}, {"D1", "D3"})  # D3 : cité par l'agenda, sans dossier
    assert [r["id"] for r in rows] == ["D1"]
    assert (rows[0]["n_scrutins"], rows[0]["decisif_propose"], rows[0]["dernier_scrutin"]) == (0, None, None)


# --- Base produite ---------------------------------------------------------------------

@pytest.mark.donnees
def test_temoins_en_cours(base):
    con = sqlite3.connect(base)
    # casseurs-payeurs (voté au Sénat, décision lue dans Dosleg), rapports locatifs (2e lecture à l'AN)
    r = dict(con.execute("select id, attente_chambre from en_cours where motif_ecart is null "
                         "and id in ('DLR5L17N54925', 'DLR5L17N53069')").fetchall())
    assert r == {"DLR5L17N54925": "AN", "DLR5L17N53069": "AN"}
    assert con.execute("select seance_inscrite from en_cours where id = 'DLR5L17N53069'").fetchone()[0] == "2026-11-18"
    # aucune lecture ne reprend un scrutin rattaché à un autre dossier
    assert not con.execute("select 1 from en_cours_lectures l join scrutins s on s.id = l.scrutin_id "
                           "where not l.art_49_3 and s.dossier_id != l.texte_id").fetchall()


@pytest.mark.donnees
def test_un_etat_pour_chaque_texte_qualifie(base):
    from lvnd import editorial
    con = sqlite3.connect(base)
    etats = dict(con.execute("select id, etat from en_cours_etats").fetchall())
    assert all(t["dossier_an"] in etats for t in editorial.charger()["textes"])
    assert etats["DLR5L17N53069"] == "en_navette"
    # casseurs-payeurs : aucun scrutin public à l'AN, mais au catalogue
    assert con.execute("select n_scrutins from textes where id = 'DLR5L17N54925'").fetchone() == (0,)
