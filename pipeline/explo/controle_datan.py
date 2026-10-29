"""Spike : contrôle croisé des positions de groupe avec datan.fr, sur un échantillon de scrutins.

datan ne publie pas les positions par scrutin en open data (data.gouv.fr : seulement des fiches
députés et groupes) : on lit les pages de vote (« La position des groupes », colonnes POUR /
CONTRE / ABSTENTION). Échantillon tiré au hasard (graine fixe), une requête par seconde.

datan n'affiche que deux colonnes, POUR et CONTRE : un groupe majoritairement abstentionniste,
partagé à égalité ou sans votant n'y figure pas (on le note « absent »). On compare la position
datan à deux règles calculées sur notre ventilation AN :
  - « exprimés » : majorité entre pour et contre (notre règle, CLAUDE.md) ;
  - « votants » : majorité entre pour, contre et abstention.

    uv run python explo/controle_datan.py [taille_echantillon]
"""

import json
import random
import re
import sys
import time
from collections import Counter
from pathlib import Path

import httpx

RAW = Path(__file__).resolve().parents[2] / "data/raw"
CACHE = RAW / "datan"


def liste(v):
    return [] if v is None else v if isinstance(v, list) else [v]


def sigles() -> dict[str, str]:
    out = {}
    for p in (RAW / "an_amo/x/json/organe").glob("PO*.json"):
        o = json.loads(p.read_text())["organe"]
        if o.get("codeType") == "GP":
            out[o["uid"]] = (o.get("libelleAbrege") or "").upper().replace(" ", "")
    return out


def page(client: httpx.Client, leg: int, num: int) -> str:
    CACHE.mkdir(parents=True, exist_ok=True)
    p = CACHE / f"{leg}_{num}.html"
    if not p.exists():
        r = client.get(f"https://datan.fr/votes/legislature-{leg}/vote_{num}")
        r.raise_for_status()
        p.write_text(r.text)
        time.sleep(1)
    return p.read_text()


def positions_datan(h: str) -> dict[str, str]:
    i = h.find("La position des groupes")
    out, courante = {}, None
    fin = h.find("LOYAL", i)  # après les groupes viennent les députés (« loyal » / « rebelle »)
    for m in re.finditer(r'title="[^"]+\(([A-Za-z-]+)\)"|>\s*(POUR|CONTRE|ABSTENTION)\s*<', h[i:fin]):
        if m.group(2):
            courante = m.group(2).lower()
        elif courante:
            g = m.group(1).upper()
            out.setdefault({"UDDPLR": "UDR", "ECOLO": "ECOLO-NUPES", "SOC-A": "SOC"}.get(g, g), courante)
    return out


def majorite(d: dict[str, int]) -> str | None:
    rang = sorted(d.items(), key=lambda kv: -kv[1])
    if not rang or rang[0][1] == 0 or (len(rang) > 1 and rang[0][1] == rang[1][1]):
        return None
    return rang[0][0]


def main(n: int):
    sig = sigles()
    fichiers = sorted((RAW / "an_scrutins_17/x/json").glob("VTANR5*.json")) + \
        sorted((RAW / "an_scrutins_16/x/json").glob("VTANR5*.json"))
    random.seed(2026)
    stats, ecarts = Counter(), []
    with httpx.Client(timeout=30, headers={"User-Agent": "lvnd-spike (controle croise, 1 req/s)"}) as client:
        for p in random.sample(fichiers, n):
            s = json.loads(p.read_text())["scrutin"]
            leg, num = int(s["legislature"]), int(s["numero"])
            try:
                dat = positions_datan(page(client, leg, num))
            except httpx.HTTPError as e:
                stats[f"page indisponible ({type(e).__name__})"] += 1
                continue
            stats["scrutins"] += 1
            for g in liste(s["ventilationVotes"]["organe"]["groupes"]["groupe"]):
                gp = sig.get(g["organeRef"])
                if gp is None:
                    continue
                dv = g["vote"]["decompteVoix"]
                pc, cc, ab = int(dv["pour"]), int(dv["contre"]), int(dv["abstentions"])
                exp = majorite({"pour": pc, "contre": cc})
                vot = majorite({"pour": pc, "contre": cc, "abstention": ab})
                if gp == "NI":  # datan n'affiche pas les non-inscrits
                    continue
                d = dat.get(gp)
                vot = vot if vot in ("pour", "contre") else None
                exp = exp if d is not None or vot is None else exp  # absent chez datan : comparé tel quel
                stats["paires"] += 1
                stats[f"datan {'=' if d == vot else '≠'} règle « votants »"] += 1
                stats[f"datan {'=' if d == exp else '≠'} règle « exprimés »"] += 1
                if d != vot:
                    ecarts.append((s["uid"], gp, d, (pc, cc, ab)))
    for k, v in stats.items():
        print(f"{v:6,}  {k}")
    print("\nÉcarts à la règle « votants » (scrutin, groupe, datan, [pour, contre, abst.]) :")
    for e in ecarts[:15]:
        print("  ", e)


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 40)
