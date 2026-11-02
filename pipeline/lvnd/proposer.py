"""Proposition de qualification par LLM (ROADMAP, cycle Pré-qualification, items 2 et 5).

Pour un dossier, et l'alerte qui le signale, le LLM prépare un brouillon au format habituel (YAML d'une
entrée de `temoins.yaml`, plus `statut`, `motif_ecart` et `relecture`), comme les agents de
`docs/QUALIFICATION.md`. Il cherche ses sources sur le web (outils web_search et web_fetch du
fournisseur). Le LLM propose : rien ici ne valide ni ne publie. Le brouillon passe ensuite les contrôles
sans LLM (`lvnd.controles`).

Le prompt n'est bâti que sur ce qui est versionné (méthode, consigne, grille, témoins) et sur l'open data :
aucun nom de la liste d'exclusion n'y figure, et il est vérifié avant chaque envoi.
"""

import base64
import io
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import polars as pl
import yaml

from . import check, editorial, llm

RACINE = Path(__file__).resolve().parents[2]
REFERENTIELS = Path(__file__).resolve().parents[1] / "referentiels"

# Type d'alerte → mode de la proposition (docs/QUALIFICATION.md, « Au fil de l'eau »).
MODES = {
    "premier_decisif": "complet",
    "vote_sans_decisif": "complet",
    "unanimite_contestee": "ecart",
    "ecart_revote": "ecart",
    "vote_posterieur": "requalification",
    "lecture_posterieure": "requalification",
    "inscrit": "suivi",
    "senat_premier_vote": "senat",
    "senat_vote_posterieur": "senat",
}

CONSIGNES = {
    "complet": "Qualifie ce texte, ou propose de l'écarter (`statut: ecarte` et `motif_ecart`) si les règles 8 ou 9 "
               "l'imposent. Faute de source admise, propose l'écart avec ce motif.",
    "ecart": "Ce texte est écarté (motif publié ci-dessous), et un vote vient remettre l'écart en question. Relis-le : "
             "qualifie le texte, ou garde l'écart avec un motif à jour qui cite ce vote (décompte « 120-45 », ou date).",
    "requalification": "Ce texte est publié (version ci-dessous), et un vote ou une lecture a eu lieu après son décisif. "
                       "Repars de la version publiée, garde son `id`, et ne change que ce que ce vote change : décisif "
                       "(règle 9), sens relu sur le texte voté (règle 6), sources revérifiées. Pour une lecture close sans "
                       "vote public sur l'ensemble, retiens la motion ou écris dans la note ce qui s'est passé, avec la "
                       "date au format JJ/MM/AAAA.",
    "suivi": "Ce texte est inscrit en séance mais pas encore voté. Prépare une fiche de suivi (`statut: a-suivre`) : "
             "droits touchés et sources, sans sens, sans rôle, sans scrutin. Sans source admise, ne rédige pas de "
             "fiche : rends `statut: sans-source`, avec ce que tu as cherché dans `relecture.points_attention`.",
    "senat": "Le Sénat a voté ce texte sur l'ensemble. Prépare le bloc `senat` (section « Vote du Sénat » de la "
             "consigne) : un YAML sans `titre` (`id`, `dossier_an`, `senat`, `relecture`) si le texte est qualifié à "
             "l'Assemblée, un YAML complet sinon.",
}

PREAMBULE = """\
Tu prépares des propositions de qualification pour le projet « Leurs voix, nos droits », qui montre comment les
parlementaires votent sur les textes touchant aux droits et libertés. Une personne relira chaque proposition
avant toute validation : tu proposes, tu ne décides pas. Ce qui compte, dans cet ordre : exactitude des faits et
des citations, respect strict des règles de la méthode, franchise sur ce qui reste incertain.

Tu travailles sans accès au dépôt : les extraits utiles de l'open data sont dans le message de la tâche. Tu as deux
outils, web_search et web_fetch, pour trouver et lire les sources. La consigne aux agents (plus bas) s'applique,
avec ces différences :
- n'écris aucun fichier : ta réponse finale se termine par un seul bloc ```yaml contenant le brouillon ;
- chaque extrait de `relecture.extraits` a la forme `clé : « citation »`, où la citation est copiée mot pour mot
  d'un document que tu as lu avec web_fetch (une coupe se marque « […] ») : un programme vérifiera chaque
  extrait dans le document, et écartera la proposition s'il ne l'y trouve pas ;
- une règle de la méthode ne couvre pas le cas : ne l'invente pas, décris le cas dans
  `relecture.points_attention` en commençant par « CAS NON PRÉVU » ;
- certaines organisations sont exclues des sources de ce projet, et leur liste ne t'est pas donnée. Pour toute
  publication collective (communiqué commun, tribune, lettre ouverte, rapport d'un collectif ou d'une
  coordination), recopie la liste complète de ses signataires dans `relecture.signataires`, sous la clé de la
  source ; une personne la contrôlera ;
- ajoute à `relecture` une liste `incertitudes` : ce que tu n'as pas pu vérifier, et pourquoi.

Format attendu du bloc final (champs de la consigne, plus ceux de `relecture`) :

```yaml
id: …
dossier_an: …
legislature: …
titre: "…"
statut: a-relire          # ou ecarte, a-suivre, sans-source (selon la tâche)
motif_ecart: null
resume: "…"
droits: []
etiquettes: []
vigilance: []
conseil_constitutionnel: ""
note: ""
sources: {}
scrutins: []
relecture:
  points_attention: []
  extraits: []
  incertitudes: []
  signataires: {}          # clé de source → liste des signataires d'une publication collective
```
"""


def _section(texte: str, debut: str) -> str:
    i = texte.index(debut)
    return texte[i:]


def contexte_fixe() -> str:
    """Partie stable du prompt (mise en cache) : préambule, méthode, consigne, grille, témoins."""
    methodo = (RACINE / "docs/METHODO.md").read_text()
    qualification = _section((RACINE / "docs/QUALIFICATION.md").read_text(), "## Au fil de l'eau")
    grille = (REFERENTIELS / "droits.yaml").read_text()
    temoins = (REFERENTIELS / "temoins.yaml").read_text()
    return "\n\n".join([
        PREAMBULE,
        "# Méthode (docs/METHODO.md)\n\n" + methodo,
        "# Procédure et consigne aux agents (docs/QUALIFICATION.md, extrait)\n\n" + qualification,
        "# Grille des droits (referentiels/droits.yaml)\n\n```yaml\n" + grille + "\n```",
        "# Six qualifications témoins validées (referentiels/temoins.yaml)\n\n```yaml\n" + temoins + "\n```",
    ])


# Données de la tâche ---------------------------------------------------------------------------

COLONNES_SCRUTINS = ("id", "date", "etape", "objet", "sort", "pour", "contre", "abstention", "titre")
MAX_SCRUTINS = 400


def _csv(df: pl.DataFrame) -> str:
    return df.write_csv() if df.height else "(aucun)\n"


def scrutins_du_dossier(export: Path, dossier: str) -> pl.DataFrame:
    """Scrutins de l'AN du dossier ; au-delà de MAX_SCRUTINS, les votes sur l'ensemble, motions, articles et
    amendements de suppression ou de rétablissement seulement (règle 11)."""
    df = (pl.read_csv(export / "scrutins.csv", infer_schema_length=None)
          .filter(pl.col("dossier_id") == dossier).sort("date", "numero"))
    if df.height > MAX_SCRUTINS:
        df = df.filter((pl.col("objet") != "amendement")
                       | pl.col("titre").str.contains(r"(?i)suppression|supprimer|rétabli|retabli"))
    return df.select([c for c in COLONNES_SCRUTINS if c in df.columns]).with_columns(
        pl.col("titre").str.slice(0, 240))


def scrutins_senat(export: Path, dossier: str) -> pl.DataFrame:
    f = export / "senat/scrutins.csv"
    if not f.exists():
        return pl.DataFrame()
    df = pl.read_csv(f, infer_schema_length=None).filter(pl.col("dossier_id") == dossier).sort("date", "numero")
    return df.select("id", "date", "lecture", "objet", "sort", "pour", "contre", "titre", "url")


def publie(dossier: str, doc: dict | None = None) -> tuple[str, dict] | None:
    """Version publiée du dossier dans editorial.json : (« texte », « suivi » ou « ecarte », entrée)."""
    doc = doc or editorial.charger()
    for genre, cle in (("texte", "textes"), ("suivi", "suivis"), ("ecarte", "ecartes")):
        for t in doc.get(cle) or []:
            if t["dossier_an"] == dossier:
                return genre, t
    return None


def message_tache(export: Path, dossier: str, mode: str, alerte: dict | None, version: tuple[str, dict] | None,
                  aujourd_hui: str) -> str:
    textes = pl.read_csv(export / "textes.csv", infer_schema_length=None).filter(pl.col("id") == dossier)
    if not textes.height:
        raise SystemExit(f"{dossier} : absent du catalogue (data/export/textes.csv)")
    fiche = {k: v for k, v in textes.row(0, named=True).items() if v not in (None, "")}
    parties = [
        f"Date du jour : {aujourd_hui}.",
        "## Tâche\n\n" + CONSIGNES[mode],
    ]
    if alerte:
        parties.append(f"## Alerte\n\n{alerte['type']} du {alerte['date']} : {alerte['detail']}"
                       + (f" (scrutin {alerte['scrutin_id']})" if alerte.get("scrutin_id") else ""))
    parties.append("## Dossier (data/export/textes.csv)\n\n```yaml\n"
                   + yaml.safe_dump(fiche, allow_unicode=True, sort_keys=False, width=1000) + "```")
    parties.append("## Scrutins publics de l'Assemblée sur ce dossier (data/export/scrutins.csv)\n\n```csv\n"
                   + _csv(scrutins_du_dossier(export, dossier)) + "```")
    senat = scrutins_senat(export, dossier)
    if senat.height:
        parties.append("## Scrutins publics du Sénat sur ce dossier (data/export/senat/scrutins.csv)\n\n```csv\n"
                       + _csv(senat) + "```")
    if version:
        genre, t = version
        libelle = {"texte": "qualification publiée", "suivi": "fiche de suivi publiée",
                   "ecarte": "écart publié"}[genre]
        parties.append(f"## Version publiée ({libelle})\n\n```yaml\n"
                       + yaml.safe_dump(t, allow_unicode=True, sort_keys=False, width=1000) + "```")
    return "\n\n".join(parties)


# Appel ----------------------------------------------------------------------------------------

# Le site public et l'admin du projet affichent les qualifications : jamais une source, et leur lecture
# fausserait la mesure de l'accord (item 4).
DOMAINES_BLOQUES = ["technoperchoir.fr"]
OUTILS = [
    {"type": "web_search_20260209", "name": "web_search", "max_uses": 12, "blocked_domains": DOMAINES_BLOQUES},
    {"type": "web_fetch_20260209", "name": "web_fetch", "max_uses": 20, "max_content_tokens": 60_000,
     "blocked_domains": DOMAINES_BLOQUES},
]
MAX_REPRISES = 8  # reprises d'un tour mis en pause par le serveur (pause_turn)


@dataclass
class Proposition:
    dossier_an: str
    mode: str
    yaml_brut: str | None = None
    doc: dict | None = None
    documents: dict[str, str] = field(default_factory=dict)  # URL lue par web_fetch → texte
    echec: str | None = None
    cout_usd: float = 0.0
    appels: int = 0


def _texte_pdf(donnees: str) -> str:
    from pypdf import PdfReader
    lecteur = PdfReader(io.BytesIO(base64.b64decode(donnees)))
    return "\n".join(p.extract_text() or "" for p in lecteur.pages)


def documents_lus(contenus) -> dict[str, str]:
    """Documents rendus par web_fetch dans la conversation : URL → texte (PDF extrait)."""
    out = {}
    for bloc in contenus:
        if getattr(bloc, "type", None) != "web_fetch_tool_result":
            continue
        c = bloc.content
        if getattr(c, "type", None) != "web_fetch_result":
            continue
        source = c.content.source
        try:
            texte = source.data if source.type == "text" else _texte_pdf(source.data)
        except Exception:
            continue
        out[c.url] = texte
    return out


def bloc_yaml(texte: str) -> str | None:
    blocs = re.findall(r"```ya?ml\s*\n(.*?)```", texte, re.DOTALL)
    return blocs[-1] if blocs else None


def proposer(session: llm.Session, export: Path, dossier: str, mode: str, alerte: dict | None = None,
             version: tuple[str, dict] | None = None, aujourd_hui: str | None = None) -> Proposition:
    """Une proposition pour `dossier`. Lève `llm.Indisponible` si le plafond interdit l'appel ; toute autre
    issue (refus, sortie tronquée, YAML absent ou illisible) donne une proposition en échec, avec sa raison."""
    if check.liste_termes() is None:
        raise llm.Indisponible("liste des termes interdits introuvable (source/termes_interdits.txt ou secret "
                               "TERMES_INTERDITS) : aucune proposition sans elle")
    systeme = contexte_fixe()
    tache = message_tache(export, dossier, mode, alerte, version, aujourd_hui or date.today().isoformat())
    if trouves := check.termes_interdits(systeme + tache):
        raise SystemExit(f"le prompt contient {len(trouves)} terme(s) de la liste d'exclusion : rien n'est envoyé")

    p = Proposition(dossier, mode)
    messages = [{"role": "user", "content": tache}]
    contenus, depart = [], len(session.appels)
    for _ in range(MAX_REPRISES + 1):
        r = session.appeler(
            dossier,
            max_tokens=64_000,
            system=[{"type": "text", "text": systeme, "cache_control": {"type": "ephemeral", "ttl": "1h"}}],
            messages=messages,
            tools=OUTILS,
            thinking={"type": "adaptive"},
            output_config={"effort": "high"},
        )
        contenus += r.content
        if r.stop_reason != "pause_turn":
            break
        messages = messages + [{"role": "assistant", "content": r.content}]
    p.appels = len(session.appels) - depart
    p.cout_usd = sum(a["cout_usd"] for a in session.appels[depart:])
    p.documents = documents_lus(contenus)

    if r.stop_reason == "pause_turn":
        p.echec = f"tour encore en pause après {MAX_REPRISES} reprises"
    elif r.stop_reason == "refusal":
        p.echec = "refus du modèle" + (f" ({r.stop_details.category})" if getattr(r, "stop_details", None) else "")
    elif r.stop_reason == "max_tokens":
        p.echec = "réponse tronquée (max_tokens)"
    if p.echec:
        return p
    final = "".join(b.text for b in r.content if getattr(b, "type", None) == "text")
    p.yaml_brut = bloc_yaml(final)
    if p.yaml_brut is None:
        p.echec = "aucun bloc YAML dans la réponse"
        return p
    try:
        doc = yaml.safe_load(p.yaml_brut)
    except yaml.YAMLError as ex:
        p.echec = f"YAML illisible : {str(ex)[:200]}"
        return p
    if not isinstance(doc, dict):
        p.echec = "le bloc YAML n'est pas un objet"
        return p
    if doc.get("dossier_an") != dossier:
        p.echec = f"dossier_an {doc.get('dossier_an')!r} ≠ {dossier}"
        return p
    p.doc = doc
    return p
