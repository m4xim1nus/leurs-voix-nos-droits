"""Normalisation des intitulés et classement de l'objet d'un scrutin (repris de quifaitlaloi)."""

import re
import unicodedata


def nettoyer(t: str | None) -> str | None:
    """Répare l'encodage Dosleg (apostrophes cp1252 U+0092 dans de l'UTF-8) et les blancs de remplissage."""
    if t is None:
        return None
    return re.sub(r"\s+", " ", t.replace("\u0092", "’")).strip()


def typographie(t: str | None) -> str | None:
    """Titre d'affichage : espaces normalisés, apostrophe typographique, « œ » (le Sénat écrit
    « oeuvre », « coeur »…)."""
    if t is None:
        return t
    t = nettoyer(t).replace("\u00a0", " ").replace("'", "’")
    return re.sub(r"\b(c|m|s|v|man|)(o)e(?=u)", lambda m: m.group(1) + ("Œ" if m.group(2) == "O" else "œ"),
                  t, flags=re.I)


def norm(t: str | None) -> str:
    """Minuscules sans accents ni ponctuation, pour comparer des intitulés."""
    t = re.sub(r"[’'`\u0092]", " ", t or "")
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", t)).strip()


VIDES = set("avec dans pour sans sous vers entre contre leurs relative relatif visant portant "
             "projet proposition texte lecture premiere deuxieme nouvelle definitive commission mixte paritaire "
             "ensemble article unique loi organique les des aux par sur une son ses est qui que "
             # formule commune aux conventions (« autorisant l'approbation de l'accord entre le
             # Gouvernement de la République française et le Gouvernement de… ») : seul le reste distingue
             "autorisant approbation ratification adhesion accord accords convention protocole avenant "
             "gouvernement republique francaise".split())


def mots_ordonnes(t: str | None) -> list[str]:
    """Mots significatifs d'un intitulé, dans l'ordre (trois lettres ou plus, hors mots-outils,
    mots de procédure et formule des conventions)."""
    return [m for m in norm(t).split() if len(m) > 2 and m not in VIDES]


def mots(t: str | None) -> set[str]:
    return set(mots_ordonnes(t))


def cle_titre(titre: str | None, n: int = 40) -> str:
    """Début d'un titre réduit à ses mots significatifs (comparé à `mots_ordonnes` d'un intitulé de
    scrutin) : un début de titre commun (« autorisant l'approbation de l'accord… ») ne suffit pas."""
    return " ".join(mots_ordonnes(titre))[:n]


def similarite(a: str | None, b: str | None) -> float:
    """Part des mots significatifs de `b` (titre du texte) présents dans `a` (intitulé du scrutin)."""
    mb = mots(b)
    return len(mots(a) & mb) / len(mb) if mb else 0.0


# Objet d'un scrutin, d'après son intitulé normalisé (AN : « l'ensemble du
# projet… » ; Sénat : « sur l'ensemble du projet… »). Ordre significatif.
OBJETS = [
    ("ensemble", r"l ensemble"),
    ("ensemble", r"(le projet|la proposition) de loi"),  # texte à article unique voté d'un bloc
    ("article_unique", r"l article unique"),
    # Sénat, jusqu'en 2019 : « sur les conclusions de la CMP… », « sur le texte élaboré par la CMP… »
    ("ensemble", r"(les conclusions de|le texte elabore par) la commission mixte paritaire"),
    ("partie", r"la (premiere|deuxieme|troisieme|quatrieme) partie"),
    # amendement(s) de suppression de l'article unique : s'il est adopté, le texte est rejeté
    ("suppression_article_unique", r"(l |les )?amendements? .{0,200}de suppression de l article unique"),
    # vote unique (art. 44, al. 3) : « sur les articles 9 à 20 et sur l'ensemble du texte… »
    ("ensemble", r"(l |les )?articles? .{0,60}et sur l ensemble"),
    ("amendement", r"(l |le |les )?(sous )?amendements?"),
    ("article", r"(l |les )?articles?"),
    ("resolution", r"la proposition de resolution"),
    ("declaration", r"la declaration du gouvernement"),
]
# Motions : le type est dans le corps de l'intitulé (Sénat : « la motion n° 1,
# présentée par…, tendant à opposer la question préalable… »).
MOTIONS = [
    ("motion_censure", r"censure"),
    ("motion_rejet", r"rejet prealable|motion de rejet|question prealable|exception d irrecevabilite"),
    ("motion_renvoi", r"renvoi en commission"),
]


def objet_scrutin(titre: str | None) -> str:
    t = re.sub(r"^sur ", "", norm(titre))
    if t.startswith("la motion"):
        for objet, motif in MOTIONS:
            if re.search(motif, t[:250]):
                return objet
        return "motion_autre"
    for objet, motif in OBJETS:
        if re.match(motif, t):
            return objet
    return "autre"
