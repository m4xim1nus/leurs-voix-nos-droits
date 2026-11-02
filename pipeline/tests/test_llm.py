"""Usage du LLM : clé chiffrée (croisé avec l'admin), coût, plafond, journal ; boucle d'une proposition et
contrôles sans LLM, avec un faux client et une fausse D1."""

import json
from pathlib import Path
from types import SimpleNamespace as NS

import httpx
import pytest
import yaml

from lvnd import check, controles, llm, proposer

FIXTURES = Path(__file__).parent / "fixtures"


class FausseD1:
    def __init__(self, reglages: dict | None = None, depense: float = 0.0):
        self.reglages = {k: json.dumps(v) for k, v in (reglages or {}).items()}
        self.depense = depense
        self.ecrits: list[str] = []

    def lire(self, sql):
        if "llm_reglages" in sql:
            return [{"cle": k, "valeur": v} for k, v in self.reglages.items()]
        return [{"s": self.depense}]

    def ecrire(self, sql):
        self.ecrits.append(sql)


def usage(entree=1000, sortie=500, lus=0, ecrits=0, recherches=0):
    u = {"input_tokens": entree, "output_tokens": sortie, "cache_read_input_tokens": lus,
         "cache_creation_input_tokens": ecrits, "server_tool_use": {"web_search_requests": recherches,
                                                                   "web_fetch_requests": 0}}
    return NS(model_dump=lambda: u)


class FauxClient:
    """Rejoue une liste de messages ; garde les paramètres reçus."""

    def __init__(self, reponses):
        self.reponses, self.recus = list(reponses), []
        self.messages = self

    def stream(self, **kw):
        self.recus.append(kw)
        m = self.reponses.pop(0)
        return _Flux(m)


class _Flux:
    def __init__(self, m):
        self.m = m

    def __enter__(self):
        return NS(get_final_message=lambda: self.m)

    def __exit__(self, *a):
        return False


EN_SERVICE = {"actif": True, "plafond_usd": 10, "modele": "claude-sonnet-5-5", "cle_api": {"chiffre": "v1:x", "fin": "x"}}


@pytest.fixture
def termes(tmp_path, monkeypatch):
    f = tmp_path / "termes.txt"
    f.write_text("# liste d'essai\nOrganisation Exclue\n")
    monkeypatch.setattr(check.termes_interdits, "__defaults__", (f,))
    monkeypatch.setattr(check.liste_termes, "__defaults__", (f,))
    return f


def test_dechiffre_le_vecteur_de_l_admin():
    vecteur = (FIXTURES / "llm_vecteur.txt").read_text().strip()
    assert llm.dechiffrer("secret-de-test", vecteur) == "sk-ant-api03-essai"
    with pytest.raises(Exception):
        llm.dechiffrer("autre", vecteur)


def test_cout():
    u = usage(entree=1_000_000, sortie=100_000, lus=2_000_000, ecrits=0, recherches=3).model_dump()
    assert llm.cout("claude-opus-5-5", u) == pytest.approx(4 + 2 + 0.4 + 0.03)
    assert llm.cout("claude-sonnet-5-5", u) == pytest.approx(2 + 1 + 0.2 + 0.03)
    u1h = {"input_tokens": 0, "output_tokens": 0, "cache_creation_input_tokens": 1_000_000,
           "cache_creation": {"ephemeral_1h_input_tokens": 1_000_000, "ephemeral_5m_input_tokens": 0}}
    assert llm.cout("claude-opus-5-5", u1h) == pytest.approx(8)


@pytest.mark.parametrize("reglages, depense, secret, motif", [
    ({}, 0, "s", "coupé"),
    ({**EN_SERVICE, "actif": False}, 0, "s", "coupé"),
    (EN_SERVICE, 0, None, "LLM_CHIFFREMENT"),
    ({k: v for k, v in EN_SERVICE.items() if k != "cle_api"}, 0, "s", "aucune clé"),
    (EN_SERVICE, 10, "s", "plafond"),
])
def test_session_indisponible(reglages, depense, secret, motif):
    with pytest.raises(llm.Indisponible, match=motif):
        llm.Session(FausseD1(reglages, depense), "essai", client=FauxClient([]), secret=secret)


def test_session_journalise_et_s_arrete_avant_le_plafond():
    d1 = FausseD1(EN_SERVICE, depense=8.8)
    fin = NS(stop_reason="end_turn", content=[], usage=usage(entree=100_000, sortie=10_000))
    s = llm.Session(d1, "essai", client=FauxClient([fin]), secret="s")
    s.appeler("DLR5L17N1", max_tokens=10, messages=[])
    assert len(d1.ecrits) == 1 and "INSERT INTO llm_appels" in d1.ecrits[0] and "'DLR5L17N1'" in d1.ecrits[0]
    assert s.depense == pytest.approx(8.8 + 0.2 + 0.1)
    with pytest.raises(llm.Indisponible, match="réserve"):
        s.appeler("DLR5L17N1", max_tokens=10, messages=[])  # reste 0,90 $ < 1 $ de réserve


def _texte(t):
    return NS(type="text", text=t)


def _lu(url, texte):
    return NS(type="web_fetch_tool_result",
              content=NS(type="web_fetch_result", url=url, content=NS(source=NS(type="text", data=texte))))


BROUILLON = """\
id: essai-2026
dossier_an: DLR5L17N1
legislature: 17
titre: "Loi essai"
statut: a-relire
resume: "Un texte d'essai."
droits:
  - { code: vie-privee, role: principal, sens: restreint, sources: [cnil], justification: "…" }
sources:
  cnil: { auteur: CNIL, titre: "Avis", date: 2026-01-01, url: "https://cnil.fr/avis" }
scrutins:
  - { id: VTANR5L17V1, role: decisif, pour: texte, objet: "ensemble, 1re lecture (10-5)" }
relecture:
  points_attention: ["CAS NON PRÉVU : essai"]
  extraits: ["cnil : « porte une atteinte   disproportionnée » "]
"""


@pytest.fixture
def export(tmp_path):
    (tmp_path / "textes.csv").write_text("id,legislature,titre\nDLR5L17N1,17,Loi essai\n")
    (tmp_path / "scrutins.csv").write_text(
        "id,dossier_id,numero,date,etape,objet,sort,pour,contre,abstention,titre,amendement_id\n"
        "VTANR5L17V1,DLR5L17N1,1,2026-01-10,AN1,ensemble,adopte,10,5,0,l'ensemble,\n")
    return tmp_path


def test_proposition_reprend_les_pauses_et_lit_le_yaml(export, termes):
    pause = NS(stop_reason="pause_turn", content=[_lu("https://cnil.fr/avis", "La mesure porte une atteinte disproportionnée.")],
               usage=usage())
    fin = NS(stop_reason="end_turn", content=[_texte(f"Compte rendu.\n\n```yaml\n{BROUILLON}```\n")], usage=usage())
    client = FauxClient([pause, fin])
    s = llm.Session(FausseD1(EN_SERVICE), "essai", client=client, secret="s")
    p = proposer.proposer(s, export, "DLR5L17N1", "complet", aujourd_hui="2026-11-02")
    assert p.echec is None and p.doc["id"] == "essai-2026" and p.appels == 2
    assert p.documents == {"https://cnil.fr/avis": "La mesure porte une atteinte disproportionnée."}
    # La reprise renvoie le tour en pause tel quel, après la tâche ; le système est mis en cache.
    assert client.recus[1]["messages"][-1] == {"role": "assistant", "content": pause.content}
    assert client.recus[0]["system"][0]["cache_control"]["ttl"] == "1h"
    assert all(o["blocked_domains"] == ["technoperchoir.fr"] for o in client.recus[0]["tools"])
    assert "VTANR5L17V1" in client.recus[0]["messages"][0]["content"]

    infos_an = {"VTANR5L17V1": {"dossier_id": "DLR5L17N1", "etape": "AN1", "division": None, "objet": "ensemble",
                                "pour": 10, "contre": 5}}
    r = controles.controler(p.doc, p.yaml_brut, "DLR5L17N1", infos_an, {}, {}, p.documents, client=_sans_reseau())
    assert r.erreurs == [], r.erreurs
    assert any(x.startswith("CAS NON PRÉVU") for x in r.points)


def test_proposition_en_echec(export, termes):
    refus = NS(stop_reason="refusal", content=[], usage=usage(), stop_details=NS(category="cyber"))
    s = llm.Session(FausseD1(EN_SERVICE), "essai", client=FauxClient([refus]), secret="s")
    assert "refus" in proposer.proposer(s, export, "DLR5L17N1", "complet").echec
    sans_yaml = NS(stop_reason="end_turn", content=[_texte("Rien trouvé.")], usage=usage())
    s = llm.Session(FausseD1(EN_SERVICE), "essai", client=FauxClient([sans_yaml]), secret="s")
    assert proposer.proposer(s, export, "DLR5L17N1", "complet").echec == "aucun bloc YAML dans la réponse"


def test_pas_de_proposition_sans_liste_d_exclusion(export, tmp_path, monkeypatch):
    absent = tmp_path / "absent.txt"
    monkeypatch.setattr(check.liste_termes, "__defaults__", (absent,))
    monkeypatch.delenv("TERMES_INTERDITS", raising=False)
    s = llm.Session(FausseD1(EN_SERVICE), "essai", client=FauxClient([]), secret="s")
    with pytest.raises(llm.Indisponible, match="termes interdits"):
        proposer.proposer(s, export, "DLR5L17N1", "complet")
    monkeypatch.setenv("TERMES_INTERDITS", "Organisation Exclue\n")
    assert check.liste_termes() == ["Organisation Exclue"]


def _sans_reseau():
    return httpx.Client(transport=httpx.MockTransport(lambda req: httpx.Response(404)))


INFOS = {"VTANR5L17V1": {"dossier_id": "DLR5L17N1", "etape": "AN1", "division": None, "objet": "ensemble",
                         "pour": 10, "contre": 5}}


def _controler(brouillon: str, documents=None, publies=None, client=None):
    doc = yaml.safe_load(brouillon)
    return controles.controler(doc, brouillon, "DLR5L17N1", INFOS, {}, publies or {}, documents,
                               client=client or _sans_reseau())


def test_controles_extrait_introuvable_et_decompte(termes):
    doc = {"https://cnil.fr/avis": "Un tout autre texte."}
    r = _controler(BROUILLON.replace("(10-5)", "(11-5)"), doc)
    assert any("introuvable" in e for e in r.erreurs)
    assert any("décompte" in e for e in r.erreurs)


def test_controles_lit_l_url_que_le_llm_n_a_pas_rendue(termes):
    lu = httpx.Client(transport=httpx.MockTransport(
        lambda req: httpx.Response(200, html="<p>Elle porte une atteinte\ndisproportionnée.</p>")))
    assert _controler(BROUILLON, client=lu).erreurs == []
    r = _controler(BROUILLON)  # 404 : avertissement, et extrait invérifiable
    assert any("répond 404" in a for a in r.avertissements)
    assert any("invérifiable" in e for e in r.erreurs)


def test_controles_exclusion_et_identifiant(termes):
    doc = {"https://cnil.fr/avis": "porte une atteinte disproportionnée"}
    r = _controler(BROUILLON.replace("Un texte d'essai.", "Selon Organisation Exclue."), doc)
    assert any("liste d'exclusion" in e for e in r.erreurs)
    signe = BROUILLON + "  signataires: { cnil: [Ligue A, organisation exclue] }\n"
    assert any("cosignée" in e for e in _controler(signe, doc).erreurs)
    assert any("déjà pris" in e for e in _controler(BROUILLON, doc, {"essai-2026": "DLR5L17N9"}).erreurs)


def test_segments_d_une_citation_coupee():
    assert controles.segments("le texte prévoit […] une atteinte grave aux libertés") == [
        "le texte prévoit", "une atteinte grave aux libertés"]
    assert controles.normaliser("L’accès « libre »\n à la jus-\n  tice") == "l'accès\"libre\"à la justice"


def test_secret_lu_dans_env(tmp_path, monkeypatch):
    monkeypatch.delenv("LLM_CHIFFREMENT", raising=False)
    f = tmp_path / ".env"
    assert llm.secret_local(env=f) is None
    f.write_text('AUTRE=1\nLLM_CHIFFREMENT="abc="\n')
    assert llm.secret_local(env=f) == "abc="
    monkeypatch.setenv("LLM_CHIFFREMENT", "env")
    assert llm.secret_local(env=f) == "env"


def test_reste_a_traiter_comme_l_admin():
    from lvnd.propositions import reste_a_traiter as r
    a = lambda t, s=None: {"type": t, "scrutin_id": s, "date": "2026-11-18"}
    assert r(a("inscrit"), None, None) and not r(a("inscrit"), "brouillon", "{}")
    assert not r(a("inscrit"), "a-suivre", "{}") and r(a("premier_decisif"), "a-suivre", "{}")
    assert r(a("vote_sans_decisif"), None, None) and not r(a("vote_sans_decisif"), "ecarte", "{}")
    assert r(a("vote_posterieur", "S2"), "valide", json.dumps({"scrutins": [{"id": "S1"}]}))
    assert not r(a("vote_posterieur", "S2"), "a-relire", json.dumps({"scrutins": [{"id": "S2"}]}))
    assert not r(a("lecture_posterieure"), "a-relire", json.dumps({"note": "Adopté à main levée le 18/11/2026."}))
    assert r(a("lecture_posterieure"), "valide", json.dumps({"note": "Décisif : S1."}))
    assert r(a("unanimite_contestee"), "ecarte", "{}") and not r(a("unanimite_contestee"), "valide", "{}")
    assert r(a("senat_premier_vote"), "valide", "{}") and not r(a("senat_premier_vote"), "ecarte", "{}")
    assert not r(a("senat_vote_posterieur", "SN1"), "valide", json.dumps({"senat": {"scrutins": [{"id": "SN1"}]}}))


def test_alertes_deja_proposees_ou_traitees_sautees(tmp_path):
    from lvnd.propositions import alertes_a_proposer
    (tmp_path / "en_cours_alertes.csv").write_text(
        "id,type,dossier_id,scrutin_id,date,titre,detail\n"
        "inscrit:D1,inscrit,D1,,2026-11-02,T1,x\n"
        "inscrit:D2,inscrit,D2,,2026-11-03,T2,x\n"
        "inscrit:D3,inscrit,D3,,2026-11-04,T3,x\n"
        "premier_decisif:D4,premier_decisif,D4,S,2026-11-05,T4,x\n")

    class D1:
        def lire(self, sql):
            if "FROM propositions" in sql:
                return [{"alerte_id": "inscrit:D1"}]
            return [{"dossier_an": "D2", "statut": "brouillon", "doc": "{}"}]

    assert [a["id"] for a in alertes_a_proposer(tmp_path, D1(), {"inscrit"})] == ["inscrit:D3"]
