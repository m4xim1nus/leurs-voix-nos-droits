"""`lvnd resumer` : résumés « en mots simples » des textes qualifiés, proposés par LLM (ROADMAP, cycle Facile à lire).

Un appel par texte, sans recherche web : le LLM reformule la fiche (titre, résumé, droits touchés, décision du
Conseil constitutionnel) et n'ajoute rien. Contrôles sans LLM avant d'écrire : termes interdits, aucun nom
d'élu·e ni de groupe (bloquants) ; longueur, phrases, sigles, nombres absents de la fiche (avertissements).

Chaque proposition va dans la table `propositions` de D1 (mode `simple`), avec l'empreinte de la fiche qu'elle
reformule ; l'admin la montre dans « À traiter », où une personne la valide ou l'écarte. Une proposition par
texte et par empreinte, jamais recalculée : une fiche qui change en reçoit une nouvelle à la passe suivante.
"""

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import polars as pl

from . import check, editorial, llm, referentiels, sync_admin

MODE = "simple"
EFFORT = "low"
MAX_TOKENS = 8_000

SYSTEME = f"""Tu écris le résumé « en mots simples » d'une fiche du site Leurs voix, nos droits. Ce site montre comment \
les parlementaires votent sur les textes qui touchent aux droits et libertés. Ce résumé s'adresse à une personne qui lit \
difficilement le français, ou qui ne connaît pas le travail des parlementaires.

Tu reçois la fiche d'un texte : son titre, son résumé, les droits qu'il touche (selon la grille du site) et, s'il y en \
a une, la décision du Conseil constitutionnel. Tu dis ce que fait le texte et quels droits il touche, avec des mots \
simples.

Règles d'écriture, tirées des règles européennes du « facile à lire et à comprendre » :
- {editorial.SIMPLE_PHRASES} phrases au plus, {editorial.SIMPLE_MOTS} mots au plus en tout, \
{editorial.SIMPLE_MOTS_PAR_PHRASE} mots au plus par phrase ;
- une phrase par ligne, une seule idée par phrase ;
- des phrases affirmatives, à la forme active, au présent quand c'est possible ;
- des mots de tous les jours ; un mot difficile qu'on ne peut pas éviter s'explique avec des mots simples ;
- aucun sigle, aucune abréviation, aucun mot étranger, aucune image ni métaphore ;
- les nombres en chiffres (« 3 ans ») ;
- toujours le même mot pour la même chose ;
- on parle du « texte », pas de « la loi » : il n'a pas toujours été adopté.

Limites, toujours :
- tu reformules la fiche, tu n'ajoutes rien : aucun fait, nombre, date, exemple ni conséquence qui n'y soit pas. \
Expliquer un mot difficile est permis ;
- tu ne dis pas si le texte étend ou restreint un droit, ni s'il est bon ou mauvais : le site le dit à côté, avec \
ses sources. Aucun mot de jugement (« enfin », « hélas », « grave », « progrès »…) ;
- tu ne nommes aucun·e élu·e, aucun parti, aucun groupe politique, aucune association ni organisation qui a donné \
son avis. Les institutions (Assemblée nationale, Sénat, Conseil constitutionnel, gouvernement, tribunaux) peuvent \
être nommées.

Réponse : le résumé entre les balises <resume_simple> et </resume_simple>, une phrase par ligne, rien d'autre \
dedans. Puis, si c'est utile, une phrase pour la personne qui relit, entre <remarque> et </remarque> : ce qui a été \
difficile à simplifier, ou ce qui manque à la fiche pour bien l'expliquer."""


def message(t: dict) -> str:
    """La fiche à reformuler, depuis une qualification normalisée : rien d'autre (ni sens, ni sources, ni scrutins)."""
    libelles = {d["code"]: d["libelle"] for d in referentiels.droits()["droits"]}
    droits = sorted(t.get("droits") or [], key=lambda d: d.get("role") != "principal")
    lignes = [f"Titre : {t['titre']}", "", f"Résumé : {t.get('resume') or '(aucun)'}", "", "Droits touchés :"]
    lignes += [f"- {libelles.get(d['code'], d['code'])}{' (le principal)' if d.get('role') == 'principal' else ''}"
               for d in droits]
    cc = t.get("conseil_constitutionnel") or ""
    lignes += ["", f"Décision du Conseil constitutionnel : {cc}" if cc else "Pas de décision du Conseil constitutionnel."]
    return "\n".join(lignes)


def _balise(texte: str, nom: str) -> str | None:
    m = re.search(rf"<{nom}>(.*?)</{nom}>", texte, re.DOTALL)
    return m.group(1).strip() if m else None


# Contrôles sans LLM --------------------------------------------------------------------------------

def _cles(s: str) -> str:
    return re.sub(r"\s+", " ", s.replace("’", "'")).strip()


@dataclass
class Noms:
    """Noms à ne jamais écrire : élu·es des deux chambres (prénom et nom), groupes (nom et sigle)."""
    elus: list[str] = field(default_factory=list)
    groupes: list[str] = field(default_factory=list)
    sigles: list[str] = field(default_factory=list)

    @classmethod
    def depuis_export(cls, export: Path) -> "Noms":
        n = cls()
        for f in (export / "deputes.csv", export / "senat/senateurs.csv"):
            if f.exists():
                df = pl.read_csv(f, infer_schema=False, columns=["prenom", "nom"])
                n.elus += [_cles(f"{p} {m}") for p, m in df.iter_rows() if p and m]
        for f in (export / "groupes.csv", export / "senat/groupes.csv"):
            if f.exists():
                df = pl.read_csv(f, infer_schema=False)
                n.groupes += [_cles(x) for x in df["nom"].drop_nulls().unique() if len(x) > 3]
                if "sigle" in df.columns:
                    n.sigles += [x for x in df["sigle"].drop_nulls().unique() if len(x) >= 2]
        n.elus, n.groupes, n.sigles = sorted(set(n.elus)), sorted(set(n.groupes)), sorted(set(n.sigles))
        return n

    def trouves(self, texte: str) -> list[str]:
        t = _cles(texte)
        mot = lambda x, flags=0: re.search(rf"(?<!\w){re.escape(x)}(?!\w)", t, flags)  # noqa: E731
        return ([x for x in self.elus if mot(x, re.IGNORECASE)] + [x for x in self.groupes if mot(x)]
                + [x for x in self.sigles if mot(x)])


def _nombres(texte: str) -> set[str]:
    return set(re.findall(r"\d+", texte))


def controler(texte: str, t: dict, noms: Noms) -> dict:
    """Erreurs (la proposition est en échec) et avertissements (à vérifier à la relecture) d'un résumé simple
    proposé pour la qualification normalisée `t`."""
    err, avert = [], []
    if check.liste_termes() is None:
        err.append("liste des termes interdits introuvable : contrôle impossible")
    elif trouves := check.termes_interdits(texte):
        err.append(f"{len(trouves)} terme(s) de la liste d'exclusion")
    if trouves := noms.trouves(texte):
        err.append(f"nomme un·e élu·e ou un groupe : {', '.join(trouves)}")
    doc = editorial.normaliser({**t, "resume_simple": {"texte": texte, "empreinte": editorial.empreinte_simple(t)}})
    if "resume_simple" not in doc:
        err.append("résumé simple vide")
    else:
        avert += editorial.controler_simple(doc)[1]
    source = " ".join([t.get("titre") or "", t.get("resume") or "", t.get("conseil_constitutionnel") or ""])
    if absents := sorted(_nombres(texte) - _nombres(source), key=int):
        avert.append(f"nombre absent de la fiche : {', '.join(absents)}")
    return {"erreurs": err, "avertissements": avert, "points": []}


# Proposition --------------------------------------------------------------------------------------

@dataclass
class Proposition:
    dossier_an: str
    empreinte: str
    texte: str | None = None
    remarque: str | None = None
    echec: str | None = None
    cout_usd: float = 0.0


def proposer(session: llm.Session, t: dict) -> Proposition:
    """Un résumé simple pour la qualification normalisée `t`. Lève `llm.Indisponible` si l'appel est interdit."""
    if check.liste_termes() is None:
        raise llm.Indisponible("liste des termes interdits introuvable (source/termes_interdits.txt ou secret "
                               "TERMES_INTERDITS) : aucune proposition sans elle")
    tache = message(t)
    if check.termes_interdits(SYSTEME + tache):
        raise SystemExit(f"{t['dossier_an']} : le prompt contient un terme de la liste d'exclusion : rien n'est envoyé")
    p = Proposition(t["dossier_an"], editorial.empreinte_simple(t))
    depart = len(session.appels)
    r = session.appeler(t["dossier_an"], max_tokens=MAX_TOKENS, system=SYSTEME,
                        messages=[{"role": "user", "content": tache}],
                        thinking={"type": "adaptive"}, output_config={"effort": EFFORT})
    p.cout_usd = sum(a["cout_usd"] for a in session.appels[depart:])
    if r.stop_reason == "refusal":
        p.echec = "refus du modèle"
        return p
    if r.stop_reason == "max_tokens":
        p.echec = "réponse tronquée (max_tokens)"
        return p
    final = "".join(b.text for b in r.content if getattr(b, "type", None) == "text")
    p.texte = _balise(final, "resume_simple")
    p.remarque = _balise(final, "remarque")
    if not p.texte:
        p.echec = "aucune balise <resume_simple> dans la réponse"
    return p


def alerte_id(dossier: str, empreinte: str) -> str:
    return f"{MODE}:{dossier}:{empreinte}"


def ligne_d1(p: Proposition, t: dict, controles: dict | None, modele: str, date: str) -> dict:
    relecture = {"origine": f"résumé simple proposé par LLM ({modele}, {date[:10]}, {p.cout_usd:.3f} $)"}
    if p.remarque:
        relecture["action"] = p.remarque
    if controles is not None:
        relecture["controles"] = controles
    if p.echec:
        relecture["echec"] = p.echec
        statut, motif = "echec", p.echec
    elif controles and controles["erreurs"]:
        statut, motif = "echec", f"{len(controles['erreurs'])} erreur(s) de contrôle"
    else:
        statut, motif = "proposee", None
    doc = None
    if p.texte:
        simple = editorial.resume_simple({"texte": p.texte, "empreinte": p.empreinte})
        doc = {"dossier_an": p.dossier_an, "resume_simple": simple} if simple else None
    return {"alerte_id": alerte_id(p.dossier_an, p.empreinte), "dossier_an": p.dossier_an, "mode": MODE, "date": date,
            "modele": modele, "cout_usd": round(p.cout_usd, 6),
            "doc": json.dumps(doc, ensure_ascii=False) if doc else None,
            "relecture": json.dumps(relecture, ensure_ascii=False), "statut": statut, "motif": motif}


COLONNES_D1 = ("alerte_id", "dossier_an", "mode", "date", "modele", "cout_usd", "doc", "relecture", "statut", "motif")


def a_resumer(qualifs: list[dict], faites: set[str], dossiers: list[str] | None = None) -> list[dict]:
    """Qualifications validées (normalisées) sans résumé simple à jour ni proposition pour leur empreinte
    actuelle, les plus anciennes d'abord (ordre du dossier). `dossiers` restreint la liste."""
    out = []
    for q in qualifs:
        if q["statut"] != "valide" or (dossiers and q["dossier_an"] not in dossiers):
            continue
        t = editorial.normaliser(json.loads(q["doc"]))
        e = editorial.empreinte_simple(t)
        if (t.get("resume_simple") or {}).get("empreinte") == e or alerte_id(t["dossier_an"], e) in faites:
            continue
        out.append(t)
    return sorted(out, key=lambda t: t["dossier_an"])


def lancer(dossiers: list[str], export: Path, admin: Path, cible: str, maximum: int, sortie: Path | None,
           prompt_seul: bool) -> int:
    if prompt_seul:
        textes = {t["dossier_an"]: t for t in editorial.charger()["textes"]}
        sortie = sortie or Path(__file__).resolve().parents[2] / "source/propositions/simple"
        sortie.mkdir(parents=True, exist_ok=True)
        (sortie / "prompt-systeme.md").write_text(SYSTEME + "\n")
        for d in dossiers or list(textes)[:3]:
            if d not in textes:
                raise SystemExit(f"{d} : aucun texte qualifié publié")
            (sortie / f"prompt-{d}.md").write_text(message(textes[d]) + "\n")
        print(f"prompts écrits dans {sortie}, aucun appel", file=sys.stderr)
        return 0

    d1 = llm.D1(cible, admin)
    try:
        session = llm.Session(d1, "resume-simple")
    except llm.Indisponible as ex:
        print(f"aucun résumé simple : {ex}", file=sys.stderr)
        return 0
    faites = {r["alerte_id"] for r in d1.lire(f"SELECT alerte_id FROM propositions WHERE mode = '{MODE}'")}
    qualifs = d1.lire("SELECT dossier_an, statut, doc FROM qualifications WHERE statut = 'valide'")
    a_faire = a_resumer(qualifs, faites, dossiers or None)
    print(f"{len(a_faire)} texte(s) sans résumé simple à jour ni proposition", file=sys.stderr)
    noms = Noms.depuis_export(export)
    for t in a_faire[:maximum]:
        try:
            p = proposer(session, t)
        except llm.Indisponible as ex:
            print(f"{t['dossier_an']} : arrêt, {ex}", file=sys.stderr)
            break
        except Exception as ex:  # erreur d'API, journalisée par la session : on réessaiera à la passe suivante
            print(f"{t['dossier_an']} : erreur, {type(ex).__name__} : {str(ex)[:200]}", file=sys.stderr)
            continue
        c = controler(p.texte, t, noms) if p.texte else None
        ligne = ligne_d1(p, t, c, session.modele, llm.maintenant())
        d1.ecrire(sync_admin.inserts("propositions", COLONNES_D1, [ligne])[0])
        print(f"{t['dossier_an']} {t['id']} → {ligne['statut']}{' : ' + ligne['motif'] if ligne['motif'] else ''}"
              f"{' (' + str(len(c['avertissements'])) + ' avertissement(s))' if c and c['avertissements'] else ''}, "
              f"{p.cout_usd:.3f} $", file=sys.stderr)
    if len(a_faire) > maximum:
        print(f"{len(a_faire) - maximum} texte(s) reporté(s) à la passe suivante (--max {maximum})", file=sys.stderr)
    print(f"dépense du mois : {session.depense:.2f} $ sur {session.reglages.plafond_usd:.2f} $", file=sys.stderr)
    return 0
