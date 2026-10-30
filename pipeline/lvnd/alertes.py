"""Alertes : ce qu'un nouveau vote ou une inscription demande de regarder (ROADMAP, Au fil des votes).

Ce sont des **avertissements** : ils ne font jamais échouer `lvnd check`, car un nouveau vote ne doit
pas bloquer la mise à jour des données. Ils sont affichés par `check` et par la file « À traiter » de
l'admin, qui retire ceux que D1 a déjà traités (admin/src/lib/alertes.ts).

- `vote_posterieur` : vote sur l'ensemble après le décisif d'un texte qualifié ;
- `unanimite_contestee` : texte écarté pour unanimité (règle 9) dont le décisif proposé a désormais
  des voix des deux côtés ;
- `premier_decisif` : décisif proposé sur un texte ni qualifié ni écarté (une fiche de suivi n'y change
  rien : le vote attendu a eu lieu, il reste à qualifier) ;
- `inscrit` : texte ni qualifié, ni écarté, ni suivi, inscrit à l'ordre du jour d'une séance. Inscrit ne
  veut pas dire voté.
"""

import re

from .textes import ENSEMBLE

COLONNES = ("id", "type", "dossier_id", "scrutin_id", "date", "titre", "detail")
SANS_OPPOSITION = re.compile(r"sans aucune voix (contre|pour)", re.I)  # motif écrit par l'admin (site : donnees.ts)


def _decompte(s: dict) -> str:
    return f"{s['id']} du {s['date']} ({s['pour']}-{s['contre']})"


def _cle(s: dict) -> tuple:
    return (s["date"], s["numero"])


def calculer(textes: list[dict], scrutins: list[dict], points: list[dict], qualif: dict) -> list[dict]:
    """`textes` : id, titre, decisif_propose. `scrutins` : id, dossier_id, date, numero, objet, sort, pour,
    contre. `points` : dossier_id, date, instance (`agenda.points`). `qualif` : `editorial.charger`."""
    titre = {t["id"]: t["titre"] for t in textes}
    scr = {s["id"]: s for s in scrutins}
    qualifies = {t["dossier_an"]: t for t in qualif["textes"]}
    ecartes = {e["dossier_an"]: e for e in qualif.get("ecartes", [])}
    suivis = {s["dossier_an"] for s in qualif.get("suivis", [])}
    out = []

    def ajouter(type_: str, dossier: str, scrutin: str | None, date: str, detail: str) -> None:
        out.append({"id": f"{type_}:{dossier}" + (f":{scrutin}" if scrutin else ""), "type": type_, "dossier_id": dossier,
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

    inscrits: dict[str, str] = {}
    for p in points:
        if p["instance"] == "seance" and p["dossier_id"] in titre:
            inscrits[p["dossier_id"]] = min(p["date"], inscrits.get(p["dossier_id"], p["date"]))
    for d, jour in inscrits.items():
        if d not in qualifies and d not in ecartes and d not in suivis:
            ajouter("inscrit", d, None, jour, f"inscrit en séance à partir du {jour}")
    return sorted(out, key=lambda a: a["id"])
