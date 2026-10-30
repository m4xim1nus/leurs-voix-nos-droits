"""Contrôles de la base produite : invariants, rattachements, textes témoins.

Un invariant ou un texte témoin en échec fait échouer `lvnd check`. Les lignes « info » renseignent
sans faire échouer.
"""

import re
import sqlite3
from pathlib import Path

from . import editorial, referentiels


def _q(con, sql: str, *args) -> list[tuple]:
    return con.execute(sql, args).fetchall()


def _un(con, sql: str, *args):
    r = _q(con, sql, *args)
    return r[0][0] if r else None


# Ventilations dont le décompte dépasse la liste nominative, dans le dump AN (même jour, même groupe).
VENTILATIONS_INCOMPLETES = {
    ("VTANR5L16V1927", "PO800502"), ("VTANR5L16V1929", "PO800502"),
    ("VTANR5L16V1930", "PO800502"), ("VTANR5L16V1948", "PO800502"),
}

# Seuils de rattachement (docs/SOURCES.md : 99,9 % des scrutins sur amendement en XVIIe au spike).
SEUIL_AMENDEMENTS = 0.995
SEUIL_DOSSIERS = 0.99


def _temoins(con, controle, out) -> None:
    ref = referentiels.droits()
    codes = {d["code"] for d in ref["droits"]}
    etiquettes = {e["code"] for e in ref["etiquettes"]}
    for t in referentiels.temoins()["textes"]:
        n = t["id"]
        texte = _q(con, "select decisif_propose, loi, nor, cc_decision, lower(cc_sens), date_loi from textes "
                        "where id = ?", t["dossier_an"])
        if not texte:
            controle(f"{n} : dossier {t['dossier_an']} au catalogue", False)
            continue
        decisif, loi, nor, cc, cc_sens, date_loi = texte[0]
        attendu = next(s["id"] for s in t["scrutins"] if s["role"] == "decisif")
        controle(f"{n} : scrutin décisif proposé = {attendu}", decisif == attendu, f"obtenu {decisif}")
        controle(f"{n} : loi {t['loi']['numero']} du {t['loi']['date']}, NOR {t['loi']['nor']}",
                 (loi, str(date_loi), nor) == (t["loi"]["numero"], str(t["loi"]["date"]), t["loi"]["nor"]),
                 f"obtenu {loi} {date_loi} {nor}")
        controle(f"{n} : décision {t['conseil_constitutionnel']['decision']} "
                 f"({t['conseil_constitutionnel']['sens']})",
                 (cc, cc_sens) == (t["conseil_constitutionnel"]["decision"], t["conseil_constitutionnel"]["sens"]),
                 f"obtenu {cc} {cc_sens}")
        for s in t["scrutins"]:
            r = _q(con, "select dossier_id, pour || '-' || contre from scrutins where id = ?", s["id"])
            ok = bool(r) and r[0][0] == t["dossier_an"] and f"({r[0][1]})" in s["objet"]
            if not ok:
                controle(f"{n} : {s['id']} rattaché au dossier, décompte conforme à « {s['objet']} »", False,
                         f"obtenu {r}")
        erreurs = [d["code"] for d in t["droits"] if d["code"] not in codes]
        erreurs += [s for d in t["droits"] for s in d["sources"] if s not in t["sources"]]
        erreurs += [e for e in t.get("etiquettes", []) if e not in etiquettes]
        if sum(d["role"] == "principal" for d in t["droits"]) != 1:
            erreurs.append("il faut exactement un droit principal")
        if not all(d["sources"] for d in t["droits"]):
            erreurs.append("un droit sans source")
        controle(f"{n} : qualification conforme à la grille (droits, étiquettes, sources)", not erreurs,
                 ", ".join(erreurs))
        cles = [s["id"] for s in t["scrutins"] if s["role"] == "amendement" and s["pour"] != "a-trancher"]
        doubles = _q(con, f"select a.division, group_concat(s.id) from scrutins s join amendements a "
                          f"on a.id = s.amendement_id where s.id in ({','.join('?' * len(cles))}) "
                          "group by s.etape, a.division having count(*) > 1", *cles) if cles else []
        controle(f"{n} : un seul amendement clé par article et par lecture", not doubles, str(doubles))
        attente = [s["id"] for s in t["scrutins"] if s["pour"] == "a-trancher"]
        if attente:
            out.append(f"info {n} : sens à trancher pour {', '.join(attente)}")


TERMES_INTERDITS = Path(__file__).resolve().parents[2] / "source/termes_interdits.txt"


def termes_interdits(texte: str, chemin: Path = TERMES_INTERDITS) -> list[str]:
    """Termes de la liste privée (source/, non versionné) présents dans `texte` (CLAUDE.md, règles dures)."""
    if not chemin.exists():
        return []
    termes = [t.strip() for t in chemin.read_text().splitlines() if t.strip() and not t.startswith("#")]
    return [t for t in termes if re.search(rf"(?<!\w){re.escape(t)}(?!\w)", texte, re.IGNORECASE)]


def _qualifications(con, controle, out) -> None:
    """Chaque qualification publiée passe les contrôles de l'admin (editorial.valider)."""
    doc = editorial.charger()
    if TERMES_INTERDITS.exists():
        trouves = termes_interdits(editorial.serialiser(doc))
        controle("aucun terme interdit dans les qualifications (source/termes_interdits.txt)", not trouves,
                 f"{len(trouves)} terme(s) trouvé(s)")
    infos = {sid: {"dossier_id": d, "etape": e, "division": div, "objet": o, "pour": p, "contre": c}
             for sid, d, e, div, o, p, c in _q(
                 con, "select s.id, s.dossier_id, s.etape, a.division, s.objet, s.pour, s.contre from scrutins s "
                      "left join amendements a on a.id = s.amendement_id")}
    for t in doc["textes"]:
        err, avert = editorial.valider(t, infos)
        controle(f"{t['id']} : qualification valide", not err, " ; ".join(err))
        out += [f"info {t['id']} : {a}" for a in avert]
    out.append(f"info {len(doc['textes'])} textes qualifiés, {len(doc.get('ecartes', []))} écartés")


def verifier(chemin: Path) -> tuple[bool, list[str]]:
    if not chemin.exists():
        return False, [f"base absente : {chemin} (lancer `lvnd build`)"]
    con = sqlite3.connect(chemin)
    ok, out = True, []

    def controle(nom: str, reussi: bool, detail: str = "") -> None:
        nonlocal ok
        ok &= reussi
        out.append(f"{'OK ' if reussi else 'ÉCHEC'} {nom}" + (f" : {detail}" if detail and not reussi else ""))

    out.append("== Votes")
    ecarts = _q(con, "select s.id from scrutins s join (select scrutin_id, sum(pour) p, sum(contre) c, "
                     "sum(abstention) a from positions_groupes group by 1) v on v.scrutin_id = s.id "
                     "where (s.pour, s.contre, s.abstention) != (v.p, v.c, v.a)")
    controle("la ventilation par groupe redonne le décompte de chaque scrutin", not ecarts, str(ecarts[:5]))
    ecarts = _q(con, "select p.scrutin_id, p.groupe_id from positions_groupes p left join (select scrutin_id, "
                     "groupe_id, sum(position = 'pour') p, sum(position = 'contre') c, "
                     "sum(position = 'abstention') a from votes group by 1, 2) v using (scrutin_id, groupe_id) "
                     "where (p.pour, p.contre, p.abstention) != (coalesce(v.p, 0), coalesce(v.c, 0), coalesce(v.a, 0))")
    connus = [e for e in ecarts if e in VENTILATIONS_INCOMPLETES]
    ecarts = [e for e in ecarts if e not in VENTILATIONS_INCOMPLETES]
    controle("les votes nominatifs redonnent la ventilation de chaque groupe", not ecarts, str(ecarts[:5]))
    for sid, gid in connus:
        out.append(f"info {sid} ({gid}) : un vote de la ventilation manque à la liste nominative (dump AN)")
    controle("aucune ventilation sans organe (PO0)", not _un(con, "select count(*) from positions_groupes "
                                                                  "where groupe_id = 'PO0'"))
    controle("tout groupe des ventilations est décrit", not _un(con, "select count(*) from positions_groupes "
                                                                    "where groupe_id not in (select id from groupes)"))
    doubles = _un(con, "select count(*) from (select 1 from votes group by scrutin_id, acteur_id having count(*) > 1)")
    controle("un seul vote par député et par scrutin", not doubles, f"{doubles} doublons")
    hors = _un(con, "select count(*) from votes v join scrutins s on s.id = v.scrutin_id where not exists ("
                    "select 1 from mandats m where m.acteur_id = v.acteur_id and m.debut <= s.date "
                    "and (m.fin is null or s.date <= m.fin))")
    controle("tout votant est député à la date du scrutin", not hors, f"{hors} votes hors mandat")
    autre = _q(con, "select count(*), count(distinct v.acteur_id) from votes v join scrutins s on s.id = v.scrutin_id "
                    "join groupes gv on gv.id = v.groupe_id where not exists (select 1 from appartenances a "
                    "join groupes ga on ga.id = a.groupe_id where a.acteur_id = v.acteur_id and ga.lignee = gv.lignee "
                    "and a.debut <= s.date and (a.fin is null or s.date <= a.fin))")[0]
    out.append(f"info {autre[0]} votes ({autre[1]} députés) ventilés dans un groupe que l'AMO ne leur donne pas "
               "à la date (changement de groupe le jour même, ou décalage de l'AMO)")
    out.append(f"info {_un(con, 'select count(*) from mises_au_point')} mises au point (affichées, pas comptées)")

    out.append("\n== Rattachements")
    for leg in (16, 17):
        n, ok_amdt = _q(con, "select count(*), count(amendement_id) from scrutins where legislature = ? "
                             "and objet in ('amendement', 'suppression_article_unique')", leg)[0]
        if not _un(con, "select count(*) from amendements where id like ?", f"AMANR5L{leg}%"):
            controle(f"XV{'I' * (leg - 15)}e : amendements présents (lancer `lvnd download an_amendements_{leg}`)",
                     False)
            continue
        controle(f"XV{'I' * (leg - 15)}e : scrutins sur amendement rattachés à leur amendement",
                 ok_amdt / n >= SEUIL_AMENDEMENTS, f"{ok_amdt}/{n} ({ok_amdt / n:.1%})")
        out.append(f"info XV{'I' * (leg - 15)}e : {ok_amdt}/{n} ({ok_amdt / n:.1%}) scrutins sur amendement rattachés")
        n, ok_d = _q(con, "select count(*), count(dossier_id) from scrutins where legislature = ?", leg)[0]
        controle(f"XV{'I' * (leg - 15)}e : scrutins rattachés à un dossier", ok_d / n >= SEUIL_DOSSIERS,
                 f"{ok_d}/{n} ({ok_d / n:.1%})")
        out.append(f"info XV{'I' * (leg - 15)}e : {ok_d}/{n} ({ok_d / n:.1%}) scrutins rattachés à un dossier")
    orphelins = [i for (i,) in _q(con, "select id from scrutins where objet = 'ensemble' and dossier_id is null")]
    controle("votes sur l'ensemble tous rattachés à un dossier (décisif possible)", not orphelins,
             ", ".join(orphelins))
    desaccords = _un(con, "select count(*) from scrutins s join amendements a on a.id = s.amendement_id "
                          "where s.rattachement = 'objet' and a.dossier_id != s.dossier_id")
    out.append(f"info {desaccords} scrutins dont l'amendement est rangé sous un autre dossier que "
               "`objet.dossierLegislatif` (dossiers rapprochés ; `objet` prime)")

    out.append("\n== Textes témoins (referentiels/temoins.yaml)")
    _temoins(con, controle, out)

    out.append(f"\n== Qualifications ({'data/editorial.json' if editorial.CHEMIN.exists() else 'textes témoins'})")
    _qualifications(con, controle, out)

    out.append("\n== Catalogue")
    for nature, n, c, s in _q(con, "select nature, count(*), sum(droits_candidats != '' or etiquettes_candidates != ''), "
                                   "sum(n_scrutins = 0) from textes group by 1 order by 2 desc"):
        out.append(f"  {nature} : {n} textes, {c} candidats par mots-clés, {s} sans scrutin public à l'AN")
    qualifies = [t["dossier_an"] for t in editorial.charger()["textes"]]
    sans = _q(con, f"select id from textes where n_scrutins = 0 and id in ({','.join('?' * len(qualifies))})", *qualifies)
    controle("aucun texte qualifié sans scrutin public à l'AN", not sans, str(sans[:5]))
    con.close()
    return ok, out
