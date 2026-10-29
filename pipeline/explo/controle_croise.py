"""Spike : contrôle croisé des ventilations par groupe avec le `dataset.json` public de
leurs-votes.fr (1 949 entrées, XVIe et XVIIe).

On compare, pour chaque scrutin commun et chaque groupe :
  - les décomptes (pour, contre, abstention, autres) : notre ventilation AN contre leur `dist` ;
  - la position : la nôtre (majoritaire parmi les exprimés, règle de CLAUDE.md) contre leur `pos`.

    uv run python explo/controle_croise.py <chemin/vers/dataset.json>
"""

import json
import sys
from collections import Counter
from pathlib import Path

RAW = Path(__file__).resolve().parents[2] / "data/raw"


def liste(v):
    return [] if v is None else v if isinstance(v, list) else [v]


def sigles() -> dict[str, str]:
    """organeRef → sigle normalisé sur ceux de leurs-votes.fr (« LFI-NFP » → « LFI », « RE » → « EPR »…)."""
    alias = {"ECOS": "ECOLO", "ECOLO-NUPES": "ECOLO", "RE": "EPR", "DR": "LR", "UDDPLR": "UDR", "LFI-NFP": "LFI",
             "LFI-NUPES": "LFI", "GDR-NUPES": "GDR", "AD": "UDR"}
    out = {}
    for p in (RAW / "an_amo/x/json/organe").glob("PO*.json"):
        o = json.loads(p.read_text())["organe"]
        if o.get("codeType") == "GP":
            s = (o.get("libelleAbrege") or "").upper().replace(" ", "")
            out[o["uid"]] = alias.get(s, s)
    return out


def position(pour: int, contre: int) -> str:
    if pour > contre:
        return "pour"
    if contre > pour:
        return "contre"
    return "egalite" if pour else "aucun_exprime"


def main(dataset: Path):
    lv = json.loads(dataset.read_text())["votes"]
    sig = sigles()
    stats, ecarts_pos, ecarts_dist = Counter(), Counter(), []
    for v in lv:
        p = RAW / f"an_scrutins_{v['legislature']}/x/json/VTANR5L{v['legislature']}V{v['voteNumero']}.json"
        if not p.exists():
            stats["scrutin absent du dump"] += 1
            continue
        s = json.loads(p.read_text())["scrutin"]
        stats["scrutins comparés"] += 1
        nous = {}
        for g in liste(s["ventilationVotes"]["organe"]["groupes"]["groupe"]):
            dv = g["vote"]["decompteVoix"]
            pc, cc, ab = int(dv["pour"]), int(dv["contre"]), int(dv["abstentions"])
            nous[sig.get(g["organeRef"], g["organeRef"])] = (pc, cc, ab, int(g["nombreMembresGroupe"]) - pc - cc - ab)
        for gp, d in v["dist"].items():
            if gp not in nous:
                stats[f"groupe {gp} absent de notre ventilation"] += 1
                continue
            stats["paires scrutin × groupe"] += 1
            if tuple(d[:3]) != nous[gp][:3]:
                stats["décomptes différents"] += 1
                ecarts_dist.append((v["id"], gp, d, nous[gp]))
            elif d[3] != nous[gp][3]:
                stats["« autres » différents (non-votants / absents)"] += 1
            if gp in v["pos"]:
                eux, n = v["pos"][gp], position(*nous[gp][:2])
                if eux != n:
                    ecarts_pos[(eux, n)] += 1
    for k, n in stats.items():
        print(f"{n:7,}  {k}")
    print("\nPositions différentes (leurs-votes → nous) :")
    for (eux, n), k in ecarts_pos.most_common():
        print(f"{k:7,}  {eux} → {n}")
    print("\nExemples de décomptes différents (id, groupe, leurs-votes [p, c, a, autres], nous) :")
    for e in ecarts_dist[:10]:
        print("  ", e)


if __name__ == "__main__":
    main(Path(sys.argv[1]))
