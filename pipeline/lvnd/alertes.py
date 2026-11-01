"""Alertes : ce qu'un nouveau vote ou une inscription demande de regarder (ROADMAP, Au fil des votes).

Ce sont des **avertissements** : ils ne font jamais échouer `lvnd check`, car un nouveau vote ne doit
pas bloquer la mise à jour des données. Ils sont affichés par `check` et par la file « À traiter » de
l'admin, qui retire ceux que D1 a déjà traités (admin/src/lib/alertes.ts).

- `vote_posterieur` : vote sur l'ensemble après le décisif d'un texte qualifié ;
- `unanimite_contestee` : texte écarté pour unanimité (règle 9) dont le décisif proposé a désormais
  des voix des deux côtés ;
- `ecart_revote` : texte écarté pour un autre motif que l'unanimité (faute de source, hors grille…), revoté à l'AN sur
  l'ensemble après la dernière revue des écarts (`ECARTS_RELUS_LE`). L'alerte tombe quand le texte est qualifié, ou
  quand son motif, relu, cite ce vote : son décompte (« 120-45 »), ou sa date (« 19/11/2026 ») sans scrutin public ;
- `premier_decisif` : décisif proposé sur un texte ni qualifié ni écarté (une fiche de suivi n'y change
  rien : le vote attendu a eu lieu, il reste à qualifier) ;
- `vote_sans_decisif` : lecture de l'AN close sur un texte ni qualifié ni écarté, sans décisif proposé : rejet
  d'une partie d'un texte financier, ou vote sur l'ensemble sans scrutin public. Hors textes à l'arrêt ou écartés
  (`motif_ecart`), et hors Sénat, dont les lectures n'ont ni scrutin ni mode ;
- `inscrit` : texte ni qualifié, ni écarté, ni suivi, inscrit à l'ordre du jour d'une séance. Inscrit ne
  veut pas dire voté ;
- `senat_premier_vote` : vote du Sénat en scrutin public sur l'ensemble d'un texte ni écarté ni lu pour
  le Sénat (une fiche de suivi n'y change rien, comme pour `premier_decisif`) ;
- `senat_vote_posterieur` : vote du Sénat sur l'ensemble après ceux que retient une qualification (règle 25).
"""

import re

from .textes import ENSEMBLE

COLONNES = ("id", "type", "dossier_id", "scrutin_id", "date", "titre", "detail")
SANS_OPPOSITION = re.compile(r"sans aucune voix (contre|pour)", re.I)  # motif écrit par l'admin (site : donnees.ts)
ECARTS_RELUS_LE = "2026-11-01"  # un vote antérieur a déjà été vu quand l'écart a été décidé ou revu


def _decompte(s: dict) -> str:
    return f"{s['id']} du {s['date']} ({s['pour']}-{s['contre']})"


def _cle(s: dict) -> tuple:
    return (s["date"], s["numero"])


def calculer(textes: list[dict], scrutins: list[dict], points: list[dict], qualif: dict,
             scrutins_senat: list[dict] = (), lectures: list[dict] = ()) -> list[dict]:
    """`textes` : id, titre, decisif_propose. `scrutins` : id, dossier_id, date, numero, objet, sort, pour,
    contre. `points` : dossier_id, date, instance (`agenda.points`). `qualif` : `editorial.charger`.
    `scrutins_senat` : id, dossier_id, date, numero, objet, pour, contre. `lectures` : texte_id, etape, chambre,
    date, issue, mode_adoption, scrutin_id, motif_ecart (`en_cours_lectures` et `en_cours`)."""
    titre = {t["id"]: t["titre"] for t in textes}
    scr = {s["id"]: s for s in scrutins}
    qualifies = {t["dossier_an"]: t for t in qualif["textes"]}
    ecartes = {e["dossier_an"]: e for e in qualif.get("ecartes", [])}
    suivis = {s["dossier_an"] for s in qualif.get("suivis", [])}
    sans_propose = {t["id"] for t in textes if not t["decisif_propose"]}
    out = []

    def ajouter(type_: str, dossier: str, scrutin: str | None, date: str, detail: str, suffixe: str | None = None) -> None:
        suffixe = suffixe or scrutin
        out.append({"id": f"{type_}:{dossier}" + (f":{suffixe}" if suffixe else ""), "type": type_, "dossier_id": dossier,
                    "scrutin_id": scrutin, "date": date, "titre": titre.get(dossier), "detail": detail})

    finals: dict[str, list[dict]] = {}
    for s in scrutins:
        if s["dossier_id"] and (s["objet"] in ENSEMBLE or (s["objet"] == "suppression_article_unique" and s["sort"] == "adopte")):
            finals.setdefault(s["dossier_id"], []).append(s)

    for d, t in qualifies.items():
        retenus = [scr[s["id"]] for s in t["scrutins"] if s["id"] in scr and s["role"] in ("decisif", "censure")]
        if not retenus:
            continue  # scrutin disparu du catalogue : signalé par le contrôle des qualifications
        ref = max(retenus, key=_cle)
        for s in finals.get(d, []):
            if _cle(s) > _cle(ref):
                ajouter("vote_posterieur", d, s["id"], s["date"], f"{_decompte(s)}, après le décisif {_decompte(ref)}")

    for t in textes:
        d, s = t["id"], scr.get(t["decisif_propose"])
        if s is None:
            continue
        e = ecartes.get(d)
        if e and SANS_OPPOSITION.search(e["motif"]) and s["pour"] and s["contre"]:
            ajouter("unanimite_contestee", d, s["id"], s["date"], f"écarté pour unanimité, décisif proposé : {_decompte(s)}")
        elif d not in qualifies and d not in ecartes:
            ajouter("premier_decisif", d, s["id"], s["date"], f"décisif proposé : {_decompte(s)}")

    closes: dict[str, list[dict]] = {}
    for l in lectures:
        if l["chambre"] == "AN" and l["issue"] and not l["scrutin_id"]:
            closes.setdefault(l["texte_id"], []).append(l)
    for d, e in ecartes.items():
        if SANS_OPPOSITION.search(e["motif"]):
            continue
        votes = [s for s in finals.get(d, []) if s["date"] > ECARTS_RELUS_LE]
        sans_scrutin = [l for l in closes.get(d, []) if l["date"] > ECARTS_RELUS_LE]
        if votes:
            s = max(votes, key=_cle)
            if f"{s['pour']}-{s['contre']}" not in e["motif"]:
                ajouter("ecart_revote", d, s["id"], s["date"], f"écarté (« {e['motif']} »), nouveau vote : {_decompte(s)}")
        elif sans_scrutin:
            l = max(sans_scrutin, key=lambda x: (x["date"], x["etape"]))
            if "/".join(reversed(l["date"].split("-"))) not in e["motif"]:
                ajouter("ecart_revote", d, None, l["date"], f"écarté (« {e['motif']} »), {l['etape']} {l['issue']} le {l['date']} "
                        f"sans scrutin public ({l['mode_adoption']})", suffixe=l["etape"])

    sans_decisif: dict[str, dict] = {}
    for l in lectures:
        d = l["texte_id"]
        if (l["chambre"] == "AN" and l["issue"] and not l["motif_ecart"] and d not in qualifies and d not in ecartes
                and d in sans_propose and (d not in sans_decisif or (l["date"], l["etape"]) > (sans_decisif[d]["date"], sans_decisif[d]["etape"]))):
            sans_decisif[d] = l
    for d, l in sans_decisif.items():
        s = scr.get(l["scrutin_id"])
        vote = f"{s['objet']}, {_decompte(s)}" if s else f"sans scrutin public ({l['mode_adoption']})"
        ajouter("vote_sans_decisif", d, s["id"] if s else None, l["date"], f"{l['etape']} {l['issue']} le {l['date']}, {vote}",
                suffixe=l["etape"])

    inscrits: dict[str, str] = {}
    for p in points:
        if p["instance"] == "seance" and p["dossier_id"] in titre:
            inscrits[p["dossier_id"]] = min(p["date"], inscrits.get(p["dossier_id"], p["date"]))
    for d, jour in inscrits.items():
        if d not in qualifies and d not in ecartes and d not in suivis:
            ajouter("inscrit", d, None, jour, f"inscrit en séance à partir du {jour}")

    par_dossier: dict[str, list[dict]] = {}
    for s in scrutins_senat:
        if s["dossier_id"] and s["objet"] in ENSEMBLE:
            par_dossier.setdefault(s["dossier_id"], []).append(s)
    senat_scr = {s["id"]: s for s in scrutins_senat}
    for d, votes in par_dossier.items():
        if d in ecartes:
            continue
        dernier = max(votes, key=_cle)
        retenus = [senat_scr[s["id"]] for s in (qualifies.get(d, {}).get("senat") or {}).get("scrutins", []) if s["id"] in senat_scr]
        if not retenus:
            ajouter("senat_premier_vote", d, dernier["id"], dernier["date"], f"vote du Sénat sur l'ensemble : {_decompte(dernier)}")
        elif _cle(dernier) > _cle(max(retenus, key=_cle)):
            ajouter("senat_vote_posterieur", d, dernier["id"], dernier["date"],
                    f"vote du Sénat sur l'ensemble : {_decompte(dernier)}, après ceux que retient la qualification")
    return sorted(out, key=lambda a: a["id"])
