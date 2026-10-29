"""Spike : recoupe referentiels/temoins.yaml avec les dumps AN (scrutins, dossiers, Conseil
constitutionnel, promulgation) et avec referentiels/droits.yaml.

    uv run python explo/verifier_temoins.py
"""

import json
import sys
from pathlib import Path

import yaml

RACINE = Path(__file__).resolve().parents[2]
RAW = RACINE / "data/raw"
REF = RACINE / "pipeline/referentiels"


def actes(a):
    yield a
    e = (a.get("actesLegislatifs") or {}).get("acteLegislatif")
    for x in e if isinstance(e, list) else [e] if e else []:
        yield from actes(x)


def main() -> int:
    droits = yaml.safe_load((REF / "droits.yaml").read_text())
    codes = {d["code"] for d in droits["droits"]}
    etiquettes = {e["code"] for e in droits["etiquettes"]}
    erreurs = []
    for t in yaml.safe_load((REF / "temoins.yaml").read_text())["textes"]:
        leg = t["legislature"]
        d = json.loads((RAW / f"an_dossiers_{leg}/x/json/dossierParlementaire/{t['dossier_an']}.json").read_text())
        tous = [a for r in (lambda r: r if isinstance(r, list) else [r])(d["dossierParlementaire"]["actesLegislatifs"]["acteLegislatif"])
                for a in actes(r)]
        cc = next(a for a in tous if a["codeActe"] == "CC-CONCLUSION")
        prom = next(a for a in tous if a["codeActe"] == "PROM-PUB")
        decision = t["conseil_constitutionnel"]["decision"]
        if not decision.endswith(f"-{cc['numDecision']} DC"):
            erreurs.append(f"{t['id']} : décision {decision} ≠ {cc['numDecision']} au dossier")
        if t["conseil_constitutionnel"]["sens"].lower() != cc["statutConclusion"]["libelle"].lower():
            erreurs.append(f"{t['id']} : sens CC « {t['conseil_constitutionnel']['sens']} » ≠ « {cc['statutConclusion']['libelle']} »")
        if prom["codeLoi"] != t["loi"]["numero"] or prom["infoJO"]["referenceNOR"] != t["loi"]["nor"]:
            erreurs.append(f"{t['id']} : loi {t['loi']} ≠ {prom['codeLoi']} / {prom['infoJO']['referenceNOR']}")
        if prom["dateActe"][:10] != str(t["loi"]["date"]):
            erreurs.append(f"{t['id']} : date de loi {t['loi']['date']} ≠ {prom['dateActe'][:10]}")
        for dr in t["droits"]:
            if dr["code"] not in codes:
                erreurs.append(f"{t['id']} : droit inconnu {dr['code']}")
            for s in dr["sources"]:
                if s not in t["sources"]:
                    erreurs.append(f"{t['id']} : source inconnue {s}")
        if sum(dr["role"] == "principal" for dr in t["droits"]) != 1:
            erreurs.append(f"{t['id']} : il faut exactement un droit principal")
        for e in t.get("etiquettes", []):
            if e not in etiquettes:
                erreurs.append(f"{t['id']} : étiquette inconnue {e}")
        for s in t["scrutins"]:
            p = RAW / f"an_scrutins_{leg}/x/json/{s['id']}.json"
            if not p.exists():
                erreurs.append(f"{t['id']} : scrutin absent {s['id']}")
                continue
            sc = json.loads(p.read_text())["scrutin"]
            dec = sc["syntheseVote"]["decompte"]
            compte = f"({dec['pour']}-{dec['contre']})"
            if compte not in s["objet"]:
                erreurs.append(f"{t['id']} : {s['id']} {compte} ne correspond pas à « {s['objet']} »")
        print(f"{t['id']:18} {len(t['scrutins'])} scrutins, CC {decision}, loi {t['loi']['numero']}")
    print("\n".join(erreurs) or "\nTout concorde.", file=sys.stderr)
    return 1 if erreurs else 0


if __name__ == "__main__":
    sys.exit(main())
