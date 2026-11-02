"""Veille des sources : lecture des flux (sans LLM), rapprochement (faux client), clés des propositions."""

import json
from datetime import datetime, timezone
from types import SimpleNamespace as NS

import httpx
import pytest

from lvnd import check, llm, veille

RSS = b"""<?xml version="1.0"?><rss version="2.0"><channel>
<item><title>Avis sur le projet de loi &#171; immigration &#187;</title><link>https://cncdh.fr/avis-1</link>
<pubDate>Mon, 02 Nov 2026 09:00:00 +0100</pubDate><description><![CDATA[<p>La CNCDH  s'inqui\xc3\xa8te</p>]]></description></item>
<item><title>Ancien</title><link>https://cncdh.fr/vieux</link><pubDate>Mon, 05 Oct 2026 09:00:00 +0000</pubDate></item>
<item><title>Sans date</title><link>https://cncdh.fr/sans-date</link></item>
</channel></rss>"""

ATOM = b"""<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom">
<entry><title>Recours</title><link rel="alternate" href="https://quadrature.net/recours"/>
<updated>2026-11-01T10:00:00Z</updated><summary>Contre la loi</summary></entry></feed>"""

FLUX = [{"cle": "cncdh", "auteur": "CNCDH", "url": "https://cncdh.fr/rss"},
        {"cle": "lqdn", "auteur": "La Quadrature du Net", "url": "https://quadrature.net/feed"},
        {"cle": "panne", "auteur": "Panne", "url": "https://panne.fr/rss"}]


def _client():
    def repondre(req):
        return {"cncdh.fr": httpx.Response(200, content=RSS), "quadrature.net": httpx.Response(200, content=ATOM)}.get(
            req.url.host, httpx.Response(500))
    return httpx.Client(transport=httpx.MockTransport(repondre))


def test_collecte_rss_et_atom_sans_llm():
    pubs, pannes = veille.collecter(FLUX, datetime(2026, 10, 25, tzinfo=timezone.utc), _client())
    assert [p.lien for p in pubs] == ["https://cncdh.fr/avis-1", "https://quadrature.net/recours"]
    assert pubs[0].titre == "Avis sur le projet de loi « immigration »" and pubs[0].resume == "La CNCDH s'inquiète"
    assert pubs[0].date == "2026-11-02T08:00:00+00:00"
    assert len(pannes) == 1 and pannes[0].startswith("panne")


def test_textes_suivis():
    publie = {"textes": [{"dossier_an": "D1", "titre": "T1", "droits": [{"code": "vie-privee"}],
                          "recherche": {"termes": ["APL"], "surnoms": ["loi X"]}}],
              "suivis": [{"dossier_an": "D2", "titre": "T2", "droits": []}],
              "ecartes": [{"dossier_an": "D3", "titre": "T3", "motif": "Aucune source admise trouvée (règle 7)."},
                          {"dossier_an": "D4", "titre": "T4", "motif": "Résolution (règle 8)."}]}
    t = veille.textes_suivis(publie)
    assert [(x["dossier_an"], x["statut"]) for x in t] == [("D1", "qualifié"), ("D2", "suivi"),
                                                           ("D3", "écarté faute de source")]
    assert t[0]["termes"] == ["APL", "loi X"]


class _Session:
    def __init__(self, reponse):
        self.reponse, self.recus = reponse, []

    def appeler(self, dossier, **kw):
        self.recus.append(kw)
        return NS(content=[NS(type="text", text=json.dumps(self.reponse))])


@pytest.fixture
def sans_exclusion(tmp_path, monkeypatch):
    f = tmp_path / "t.txt"
    f.write_text("Organisation Exclue\n")
    monkeypatch.setattr(check.termes_interdits, "__defaults__", (f,))
    monkeypatch.setattr(check.liste_termes, "__defaults__", (f,))


def test_rapprochement_ne_garde_que_ce_qui_existe(sans_exclusion):
    pubs = [veille.Publication("cncdh", "CNCDH", "Avis", "https://cncdh.fr/a", "2026-11-02T08:00:00+00:00", "")]
    textes = [{"dossier_an": "D1", "statut": "qualifié", "titre": "T1", "droits": [], "termes": []}]
    s = _Session({"correspondances": [{"lien": "https://cncdh.fr/a", "dossier_an": "D1", "raison": "avis"},
                                      {"lien": "https://inventé.fr", "dossier_an": "D1", "raison": "x"},
                                      {"lien": "https://cncdh.fr/a", "dossier_an": "D9", "raison": "x"}]})
    assert veille.rapprocher(s, pubs, textes) == [{"lien": "https://cncdh.fr/a", "dossier_an": "D1", "raison": "avis"}]
    assert s.recus[0]["output_config"]["format"]["type"] == "json_schema"
    exclue = [veille.Publication("x", "Organisation Exclue", "T", "https://x.fr", "2026-11-02T08:00:00+00:00", "")]
    with pytest.raises(llm.Indisponible, match="exclusion"):
        veille.rapprocher(s, exclue, textes)


def test_cle_stable():
    assert veille.cle_alerte("D1", "https://a") == veille.cle_alerte("D1", "https://a")
    assert veille.cle_alerte("D1", "https://a") != veille.cle_alerte("D1", "https://b")
    assert veille.cle_alerte("D1", "https://a").startswith("veille:D1:")


def test_flux_du_referentiel_sans_exclusion():
    from lvnd import referentiels
    flux = referentiels.charger("sources_veille")["flux"]
    assert len({f["cle"] for f in flux}) == len(flux) and all(f["url"].startswith("https://") for f in flux)
    assert check.termes_interdits(json.dumps(flux, ensure_ascii=False)) == []
